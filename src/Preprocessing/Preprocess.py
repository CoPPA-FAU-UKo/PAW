import pandas as pd
import numpy as np
from src.Log import Reformat
from src.Preprocessing import Feature


def cal_remtime(time_stamp_arr):
    return (time_stamp_arr[-1] - time_stamp_arr).astype('timedelta64[s]').astype(int)


def cal_lapse(time_stamp_arr):
    return -(time_stamp_arr[0] - time_stamp_arr).astype('timedelta64[s]').astype(int)


def custom_encoding(column):
    le = Feature.CustomLabelEncoder()
    le.fit(column)
    le_name_mapping = dict(zip(le.classes_, le.transform(le.classes_)))
    le_class_mapping = dict(zip(le.transform(le.classes_), le.classes_))
    return le.transform(column), le_name_mapping, le_class_mapping


def split_data(log, train=0.64, val=0.16, random=False):
    data_size = log.shape[0]
    split_log = log
    if random:
        split_log = log.sample(frac=1)
    training_set = split_log[:int(train * data_size)]
    validation_set = split_log[int(train * data_size): int(train * data_size) + int(val * data_size)]
    test_set = split_log[int(train * data_size) + int(val * data_size):]
    return training_set, validation_set, test_set


def split_encode(trace, feature, train=0.64, val=0.16, random=False):
    pd.options.mode.chained_assignment = None  # default='warn'
    train, val, test = split_data(trace, train=train, val=val, random=random)
    le_map = {}
    for cat_feature in feature:
        train_value = train[cat_feature].explode(cat_feature).unique()
        val_value = val[cat_feature].explode(cat_feature).unique()
        test_value = test[cat_feature].explode(cat_feature).unique()
        values = np.concatenate([train_value, val_value, test_value])
        le = Feature.CustomLabelEncoder()
        le.fit(values)
        name_mapping = dict(zip(le.classes_, le.transform(le.classes_)))
        class_mapping = dict(zip(le.transform(le.classes_), le.classes_))
        le_map[cat_feature] = {"name_mapping": name_mapping, "class_mapping": class_mapping}
        train[cat_feature] = train[cat_feature].apply(le.transform).apply(np.array)
        val[cat_feature] = val[cat_feature].apply(le.transform).apply(np.array)
        test[cat_feature] = test[cat_feature].apply(le.transform).apply(np.array)

    le_map_pd = pd.DataFrame(data=le_map)
    return train, val, test, le_map_pd


def generate_dist_embedding(trace, features):
    dist_embedding = {}
    for feature in features:
        data = trace[feature].explode(feature).values
        unique, counts = np.unique(data, return_counts=True)
        frequencies = counts / counts.sum()
        dist_embedding[feature] = [frequencies]
    return pd.DataFrame(data=dist_embedding)
