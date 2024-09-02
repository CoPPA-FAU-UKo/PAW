from src.Trainer import Classifier
from src.Trainer import Regressor
from src.Trainer import CaseDataSet
from sklearn.metrics import mean_absolute_error
from sklearn.metrics import precision_recall_fscore_support

def split_data(log, training_ratio, validation_ratio):
    data_size = log.shape[0]
    training_set = log[:int(training_ratio * data_size)]
    validation_set = log[int(training_ratio * data_size): int(training_ratio * data_size) + int(validation_ratio * data_size)]
    test_set = log[int(training_ratio * data_size) + int(validation_ratio * data_size): ]
    return training_set, validation_set, test_set


def train_xgb_predictor(training_set, validation_set, test_set, parameter):
    predictor = None
    if parameter["task"] == "Regression":
        predictor = Regressor.XgbRegressor(training_set, validation_set, tree_method=parameter["tree_method"],
                                           early_stopping_rounds=parameter["early_stopping_rounds"])
    elif parameter["task"] == "Classification":
        predictor = Classifier.XgbClassifier(training_set, validation_set, tree_method=parameter["tree_method"],
                                             early_stopping_rounds=parameter["early_stopping_rounds"])
    if predictor:
        predictor.train()
        test_res, test_ref = predictor.predict(test_set)
        if parameter["task"] == "Regression":
            test_mae = mean_absolute_error(test_ref, test_res)
            test_score = [test_mae]
        elif parameter["task"] == "Classification":
            test_precision, test_recall, test_f1, support = precision_recall_fscore_support(test_ref, test_res,
                                                                                            average='weighted',
                                                                                            zero_division=0.0)
            test_score = [test_precision, test_recall, test_f1]

    return predictor, predictor.get_val_stat(), test_score


def training_pipline(log, parameter):
    train, val, test = split_data(log, parameter["training_ratio"], parameter["validation_ratio"])
    train_set = CaseDataSet.CaseDataset(train, feature_list=parameter["feature"],
                                        label=parameter["label"], encoding=parameter["encoding"])
    val_set = CaseDataSet.CaseDataset(val, feature_list=parameter["feature"],
                                      label=parameter["label"], encoding=parameter["encoding"])
    test_set = CaseDataSet.CaseDataset(val, feature_list=parameter["feature"],
                                       label=parameter["label"], encoding=parameter["encoding"])

    predictor, val_stat, test_score = None, None, None
    if parameter["model"] == "XGBoost":
        predictor, val_stat, test_score = train_xgb_predictor(train_set, val_set, test_set, parameter)

    return predictor, val_stat, test_score






