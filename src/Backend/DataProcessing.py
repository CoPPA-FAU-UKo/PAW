import numpy as np
import pandas as pd

import pickle as pickle
from src.Log import Reformat
from src.Preprocessing import Preprocess
from sklearn.preprocessing import OneHotEncoder
from sklearn.preprocessing import LabelEncoder


def generate_trace(data, time_column="endDate", case_column="Case ID", selected_columns=[]):
    data["nodeType"] = data["flowNodeId"].apply(lambda x: x[:4])
    data_fin = data[data["nodeType"] == "Task"]
    data_fin = data_fin[selected_columns]
    data_fin = data_fin.rename(columns={case_column: "CaseID", time_column:"EndDate"})
    data_fin["EndDate"] = data_fin["EndDate"].apply(pd.to_datetime)
    data_trace = Reformat.roll_sequence(data_fin, time_column="EndDate", case_column="CaseID")
    data_trace = data_trace.reset_index()
    data_trace["RemTime"] = data_trace["EndDate"].apply(Preprocess.cal_remtime)
    data_trace["LapseTime"] = data_trace["EndDate"].apply(Preprocess.cal_lapse)
    return data_trace


def onehot_encode(data, columns):
    encoder_dict = {}
    for column_to_encode in columns:
        enc = OneHotEncoder(sparse_output=False)
        enc.fit(data[column_to_encode].explode(column_to_encode).unique().reshape((-1, 1)))
        data[column_to_encode] = data[column_to_encode].apply(lambda x: enc.transform(x.reshape((-1, 1))))
        encoder_dict[column_to_encode] = enc
    return data, encoder_dict


def label_encode(data, columns):
    encoder_dict = {}
    for column_to_encode in columns:
        enc = LabelEncoder()
        enc.fit(data[column_to_encode].explode(column_to_encode).unique().reshape((-1, 1)))
        data[column_to_encode] = data[column_to_encode].apply(lambda x: enc.transform(x.reshape((-1, 1))))
        encoder_dict[column_to_encode] = enc
    return data, encoder_dict
