import xgboost as xgb
import numpy as np
import copy
import torch
from torch.nn import functional as F
from sklearn import preprocessing
from joblib import dump, load
import importlib
from src.Model import DLModels


class XgbClassifier():
    def __init__(self, training_set, validation_set, tree_method="hist", early_stopping_rounds=2):
        self.training_set = training_set
        self.validation_set = validation_set
        self.dataset_list = [self.training_set, self.validation_set]
        self.data_list = []
        self.le = preprocessing.LabelEncoder()
        self.train_input = self.generate_data_set(self.training_set, training_set=True)
        self.val_input = self.generate_data_set(self.validation_set)
        self.clf = xgb.XGBClassifier(objective='multi:softprob', tree_method=tree_method,
                                     early_stopping_rounds=early_stopping_rounds,
                                     num_class=self.le.classes_.shape[0])
        self.eval_result = {}

    def generate_data_set(self, dataset, training_set=False):
        feature_list = []
        label_list = []
        for prefix_len in range(1, dataset.max_case_len+1):
            dataset.set_prefix_length(prefix_len)
            if dataset:
                feature_list.append(dataset[:][0].numpy())
                label_list.append(dataset[:][1].numpy())
            else:
                break
        output = [np.vstack(feature_list), np.argmax(np.vstack(label_list), axis=-1)]
        if training_set:
            self.le.fit(output[1].ravel())

        return [output[0], self.le.transform(output[1].ravel())]

    def train(self):
        self.clf.fit(self.train_input[0], self.train_input[1],
                     eval_set=[(self.val_input[0], self.val_input[1])], verbose=False)

    def score(self):
        return self.clf.score(self.val_input[0], self.val_input[1])

    def predict(self, test_set):
        test_input = self.generate_data_set(test_set)
        return self.clf.predict(test_input[0]), test_input[1]

    def get_val_stat(self):
        return self.clf.evals_result_['validation_0']


def train_model_epoch(model, training_set, optimizer, criterion, torch_device, batch_size=50, training=True):
    training_data_set = training_set
    batch_size = batch_size
    loss_prefix_list = []
    sample_num_list = []
    for prefix_len in range(1, training_set.max_case_len+1):
        loss_prefix = 0
        training_data_set.set_prefix_length(prefix_len)
        training_data_set.shuffle_data()
        input_data = training_data_set[:]
        if input_data is None:
            break
        sample_num = input_data[0].shape[0]
        sample_num_list.append(sample_num)

        batch_num = int(sample_num / batch_size)
        for i in range(batch_num):
            x = input_data[0][int(batch_size * i): int(batch_size * (i+1))].float().to(torch_device)
            y = input_data[1][int(batch_size * i): int(batch_size * (i+1))].float().to(torch_device).argmax(dim=-1)
            outputs = model(x)
            loss = criterion(outputs, torch.flatten(y))
            if training:
                optimizer.zero_grad()
                loss.backward()
                optimizer.step()
            loss_prefix = loss_prefix + loss.item() * x.shape[0]

        if sample_num > batch_size * batch_num:
            x = input_data[0][batch_size * batch_num:].float().to(torch_device)
            y = input_data[1][batch_size * batch_num:].float().to(torch_device).argmax(dim=-1)
            outputs = model(x)
            loss = criterion(outputs, torch.flatten(y))
            if training:
                optimizer.zero_grad()
                loss.backward()
                optimizer.step()
            loss_prefix = loss_prefix + loss.item()* x.shape[0]

        loss_prefix_list.append(loss_prefix)
    return np.array(loss_prefix_list), np.array(sample_num_list)


def train_model(model, optimizer, criterion, training_set,
                test_set, batch_size, torch_device, device_package,
                max_epoch=100, max_ob_iter=20, score_margin=1e-4, print_iter=False):
    train_score_list = []
    test_score_list = []
    score = 1e5
    best_iter = 0
    best_model = None
    for iter_epoch in range(max_epoch):
        device_package.empty_cache()
        loss_train, sample_num_train = train_model_epoch(model, training_set, batch_size=batch_size,
                                                         optimizer=optimizer,
                                                         criterion=criterion,
                                                         torch_device=torch_device)
        device_package.empty_cache()
        loss_test, sample_num_test = train_model_epoch(model, test_set, batch_size=batch_size,
                                                       optimizer=optimizer,
                                                       criterion=criterion,
                                                       torch_device=torch_device,
                                                       training=False)

        score_train = np.sum(loss_train) / np.sum(sample_num_train)
        score_test = np.sum(loss_test) / np.sum(sample_num_test)
        train_score_list.append(score_train)
        test_score_list.append(score_test)

        if score_test < (score - score_margin):
            score = score_test
            best_model = copy.deepcopy(model)
            best_iter = iter_epoch

        if iter_epoch > best_iter + max_ob_iter:
            break
        if print_iter:
            print("Finished training iteration: ", iter_epoch, " with val loss: ", score_test)
    device_package.empty_cache()
    return best_model, np.array(train_score_list), np.array(test_score_list)


def evaluate_model(model, test_set, torch_device, device_package, batch_size=100):
    training_data_set = test_set
    evaluation_list = []
    sample_num_list = []
    model.flatten()
    device_package.empty_cache()
    for prefix_len in range(1, test_set.max_case_len+1):
        training_data_set.set_prefix_length(prefix_len)
        input_data = training_data_set[:]
        if input_data is None:
            # print("Max length reached, abort")
            break
        sample_num = input_data[0].shape[0]
        sample_num_list.append(sample_num)

        output_list = []
        label_list = []
        batch_num = int(sample_num / batch_size)
        for i in range(batch_num):
            x = input_data[0][int(batch_size * i): int(batch_size * (i+1))].float().to(torch_device)
            y = input_data[1][int(batch_size * i): int(batch_size * (i+1))].float().argmax(dim=-1)
            outputs = model(x).detach().argmax(dim=-1)
            output_list.append(outputs.cpu().numpy())
            label_list.append(y.cpu().numpy().T)

            device_package.empty_cache()

        if sample_num > batch_size * batch_num:
            x = input_data[0][batch_size * batch_num:].float().to(torch_device)
            y = input_data[1][batch_size * batch_num:].float().argmax(dim=-1)
            outputs = model(x).detach().argmax(dim=-1)
            output_list.append(outputs.cpu().numpy())
            label_list.append(y.cpu().numpy().T)

            device_package.empty_cache()

        evaluation_list.append([np.vstack(output_list),
                                np.vstack(label_list)])

    return evaluation_list, np.array(sample_num_list)


class LstmClassifier():
    def __init__(self, training_set, validation_set, hidden_size, num_layers, num_class, optimizer, loss, batch_size, max_epoch=200, max_ob_iter=40):
        self.torch_device = "cpu"
        self.device_package = torch.cpu
        self.check_torch_device()
        self.training_set = training_set
        self.validation_set = validation_set
        self.input_size = self.training_set[:][0].shape[-1]
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        self.num_class = num_class
        self.model = DLModels.SimpleLSTM(self.input_size, self.hidden_size, self.num_layers, self.num_class).to(self.torch_device)
        self.optimizer = optimizer(self.model.parameters(), lr=1e-3)
        self.loss = loss
        self.batch_size = batch_size
        self.max_epoch = max_epoch
        self.max_ob_iter = max_ob_iter
        self.train_score, self.val_score = None, None


    def check_torch_device(self):
        if importlib.util.find_spec("torch.backends.mps") is not None:
            if torch.backends.mps.is_available():
                self.torch_device = torch.device("mps")
                self.device_package = torch.mps
        if torch.cuda.is_available():
            self.torch_device = torch.device("cuda")
            self.device_package = torch.cuda

    def train(self):
        self.model, self.train_score, self.val_score = train_model(self.model, self.optimizer, self.loss,
                                                                   self.training_set, self.validation_set,
                                                                   self.batch_size, self.torch_device,
                                                                   self.device_package,  self.max_epoch, self.max_ob_iter, print_iter=False)

    def predict(self, test_set):
        self.evaluation_list, self.sample_num_list = evaluate_model(self.model, test_set, self.torch_device, self.device_package, self.batch_size)
