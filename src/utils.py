import os
import sys
import pickle
from typing import List, Dict, Union
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
import warnings

warnings.filterwarnings('ignore', category=Warning, module='sklearn')

def create_directory(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)
    else:
        pass
        # print(f"Directory '{directory}' already exists!")

def save_pickle(data, filename, display=False):
    directory = os.path.dirname(filename)
    create_directory(directory)
    with open(filename, 'wb') as file:
        pickle.dump(data, file)
        if display:
            print(f"Data saved to '{filename}'")

def load_pickle(filename, display=False):
    with open(filename, 'rb') as file:
        data = pickle.load(file)
        if display:
            print(f"Data loaded from '{filename}'")
        return data




class CodeSolution:
    def __init__(self, model_name: str, parameters: Dict):
        self.model_name = model_name
        self.parameters = parameters
    def __str__(self):
        return f"Model: {self.model_name}, Parameters: {self.parameters}"

class RandomModel:
    def __init__(self):
        self.model_name = "random"
        self.parameters = {}

    def score(self, X, y):
        num_classes = len(set(y))
        return 1 / num_classes
    def predict(self, X):
        return [0] * len(X)


parameters_space = {
            "logistic_regression": {
                "C": [0.01, 0.1],
                "max_iter": [100, 200]
            },
            "svm": {
                "C": [0.01, 0.1],
                "kernel": ["linear", "poly"],
                "degree": [2, 3, 4]
            }
        }
parameters_keys = {
    model_name: list(parameters_space[model_name].keys()) for model_name in parameters_space
}

def run_model_code(data, code: CodeSolution):
    model_name = code.model_name
    parameters = code.parameters
    if model_name == "random" or not model_name:
        return RandomModel()
    model = None
    if model_name == "logistic_regression":
        model = LogisticRegression(C=parameters["C"], max_iter=parameters["max_iter"], multi_class="multinomial")
    elif model_name == "svm":
        model = SVC(C=parameters["C"], kernel=parameters["kernel"], degree=parameters["degree"])

    model.fit(data[0], data[1])
    return model

def init_parameters_list(model_sets=None):
    if model_sets is None:
        model_sets = parameters_space.keys()
    parameters_list = {}
    for model_name in model_sets:
        parameters_list[model_name] = []

        def search_parameters(curr_params, model_name, curr_param_index=0):
            curr_param_key = parameters_keys[model_name][curr_param_index]
            for param_value in parameters_space[model_name][curr_param_key]:
                curr_params[curr_param_key] = param_value
                if curr_param_index == len(parameters_keys[model_name]) - 1:
                    parameters_list[model_name].append(curr_params.copy())
                else:
                    search_parameters(curr_params, model_name, curr_param_index + 1)
            return
        search_parameters({}, model_name)
    return parameters_list

