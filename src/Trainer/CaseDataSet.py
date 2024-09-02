import pandas as pd
import numpy as np
import torch
from torch.nn import functional as F
from torch.utils.data import Dataset


class CaseDataset(Dataset):
    def __init__(self, data, feature_list=["Activity"], label="Next_Activity", encoding="all",
                 max_case_len=1e4, min_case_len=1):

        self.data_all = data
        self.feature_list = feature_list
        self.encoding = encoding
        self.label = label
        self.next_event_prediction = False
        if label[:5] == "Next_":
            self.label = label[5:]
            self.next_event_prediction = True

        self.data_all.loc[:, "Case_Length"] = self.data_all[self.label].apply(len)
        self.data_all = self.data_all[self.data_all["Case_Length"] < max_case_len]
        self.data_all = self.data_all[self.data_all["Case_Length"] > min_case_len]
        self.max_case_len = self.data_all["Case_Length"].max()

        self.prefix_length = 1
        for column in self.feature_list:
            if self.data_all[column].values[0].ndim == 1:
                self.data_all[column] = self.data_all[column].apply(lambda x: x.reshape((-1, 1)))
        self.data_pool = self.data_all.copy()

    def set_prefix_length(self, prefix_len):
        self.prefix_length = prefix_len

    def shuffle_data(self):
        self.data_pool = self.data_pool.sample(frac=1)

    def update_data_pool(self):
        max_prefix = self.prefix_length
        if self.next_event_prediction:
            max_prefix = self.prefix_length + 1
        data_temp = self.data_pool[self.data_pool["Case_Length"] >= max_prefix]
        return data_temp

    def convert_feature_vec(self, data):
        data_com = np.hstack(data.values)
        if self.encoding == "Last":
            return data_com[self.prefix_length-1]
        if self.encoding == "Agg_Mean":
            return np.mean(data_com[:self.prefix_length], axis=0)
        return torch.from_numpy(data_com[:self.prefix_length])

    def convert_label_vec(self, label):
        if label.shape[0] == 1:
            return torch.from_numpy(label[0])
        if self.next_event_prediction:
            return torch.from_numpy(label[self.prefix_length:self.prefix_length+1])
        else:
            return torch.from_numpy(label[self.prefix_length-1:self.prefix_length])

    def __len__(self):
        data_temp = self.update_data_pool()
        return data_temp.shape[0]

    def __getitem__(self, idx):
        data_temp = self.update_data_pool()
        if torch.is_tensor(idx):
            idx = idx.tolist()

        x = data_temp[self.feature_list].apply(self.convert_feature_vec, axis=1).values[idx]
        y = data_temp[self.label].apply(self.convert_label_vec).values[idx]

        if len(x) == 0:
            return None

        y = torch.stack(y.tolist())
        return torch.tensor(np.stack(x)), y