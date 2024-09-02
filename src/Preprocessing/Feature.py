from torch import nn
import torch


class CustomLabelEncoder:
    def __init__(self):
        self.label_mapping = {}
        self.classes_ = []

    def fit(self, labels):
        # Create a mapping from label to integer based on order of appearance
        for label in labels:
            if label not in self.label_mapping:
                self.label_mapping[label] = len(self.label_mapping)
                self.classes_.append(label)

    def transform(self, labels):
        # Transform labels to integers
        return [self.label_mapping[label] for label in labels]

    def fit_transform(self, labels):
        self.fit(labels)
        return self.transform(labels)

    def inverse_transform(self, values):
        # Reverse the label mapping
        inverse_mapping = {v: k for k, v in self.label_mapping.items()}
        return [inverse_mapping[value] for value in values]


class OneHotEmbedding(nn.Module):
    def __init__(self, num_classes, rule="zero", dist=None):
        super(OneHotEmbedding, self).__init__()
        self.rule = rule  # 'zero', 'one_over_n', 'random', 'dummy'
        self.num_classes = num_classes
        self.dist = dist

    def forward(self, x):
        where = torch.where(x >= self.num_classes)
        x[where] = torch.tensor(0, dtype=x.dtype)
        one_hot = torch.nn.functional.one_hot(x, num_classes=self.num_classes).float()

        if self.rule == 'dummy':
            one_hot = torch.nn.functional.one_hot(x, num_classes=self.num_classes+1).float()
            dummy_class = torch.zeros(self.num_classes+1)
            dummy_class[-1] = 1
            one_hot[where] = dummy_class
        elif self.rule == 'zero':
            one_hot[where] = torch.tensor(0., dtype=one_hot.dtype)
        elif self.rule == 'one_over_n':
            one_hot[where] = torch.tensor(1/self.num_classes, dtype=one_hot.dtype)
        elif self.rule == 'random':
            one_hot[where] = torch.rand(size=one_hot.shape)[where].clone().detach().type(one_hot.dtype)
        elif self.rule == 'dist':
            one_hot[where] = torch.tensor(self.dist, dtype=one_hot.dtype)
        else:
            raise ValueError('Invalid rule')

        return one_hot

