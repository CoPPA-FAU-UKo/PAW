from src.Trainer import Classifier
from src.Trainer import Regressor
from src.Trainer import CaseDataSet
from sklearn.metrics import mean_absolute_error
from sklearn.metrics import precision_recall_fscore_support
import torch
from torch import nn


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


def train_LSTM_predictor(training_set, validation_set, test_set, parameter):
    predictor = None
    if parameter["task"] == "Regression":
        optimizer = torch.optim.NAdam
        loss = nn.L1Loss()
        predictor = Regressor.LstmRegressor(training_set, validation_set,
                                            parameter["hidden_size"], parameter["num_layers"],
                                            optimizer, loss, parameter["batch_size"],
                                            parameter["max_iter"], parameter["patience"])
    elif parameter["task"] == "Classification":
        optimizer = torch.optim.NAdam
        loss = nn.CrossEntropyLoss()
        num_class = training_set[:][1].shape[-1]
        predictor = Classifier.LstmClassifier(training_set, validation_set,
                                              parameter["hidden_size"], parameter["num_layers"],
                                              num_class, optimizer, loss, parameter["batch_size"],
                                              parameter["max_iter"], parameter["patience"])
    if predictor:
        predictor.train()
        test_res, test_ref = predictor.predict(test_set)
        if parameter["task"] == "Regression":
            test_mae = mean_absolute_error(test_ref, test_res)
            test_score = [test_mae]
        elif parameter["task"] == "Classification":
            test_precision, test_recall, test_f1, support = precision_recall_fscore_support(test_ref.T, test_res.T,
                                                                                            average='weighted',
                                                                                            zero_division=0.0)
            test_score = [test_precision, test_recall, test_f1]
    return predictor, predictor.val_score, test_score


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
    if parameter["model"] == "LSTM":
        predictor, val_stat, test_score = train_LSTM_predictor(train_set, val_set, test_set, parameter)

    return predictor, val_stat, test_score






