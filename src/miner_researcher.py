from debugpy.common.timestamp import current

from miner import Miner

import random
import requests
import sys
import wallet
from time import sleep, time
from numpy import average
import re
import blockchain
import crypto
from block import Block
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from utils import load_pickle, save_pickle
import os
import io
import sys
import numpy as np
from utils import CodeSolution, init_parameters_list, run_model_code
from collections import Counter




class MinerResearcher(Miner):
    def __init__(self, NODE):
        super().__init__(NODE)
        self.mining_address = wallet.get_address(f"private_key_{self.port}.pem")
        print('Miner Researcher initialized!')
        self.model_sets = ["logistic_regression", "svm"]
        self.parameters_list = init_parameters_list()
        print(self.parameters_list)


    def search_best_model(self, train_data, dev_data, previous_score):
        best_params = None
        best_model_name = None
        best_score = 0

        for model_name in self.model_sets:
            for parameters in self.parameters_list[model_name]:
                code_solution = CodeSolution(model_name, parameters)
                model = run_model_code(train_data, code_solution)
                score = model.score(dev_data[0], dev_data[1])
                if score > best_score:
                    best_score = score
                if best_score > previous_score:
                    best_model_name = model_name
                    best_params = parameters
                    return best_score, best_model_name, best_params
        return best_score, best_model_name, best_params


    def mine(self):
        # TODO: wait for the request implementation
        # previous_block = requests.get(self.node_url + "/chain").json()["chain"][-1]
        previous_block = Block(
            research_address="research_address",
            index=0,
            previous_block_id=0,
            task_description="task_description",
            data_link=f"tmp/digits_0",
            constraint="constraint",
            code_link=CodeSolution("logistic_regression", {"C": 0.01, "max_iter": 100})
        )

        unlabeled_data = load_pickle(os.path.join(previous_block.data_link, "unlabeled.pkl"))


        current_dataset_idx = int(previous_block.data_link.split("_")[-1])
        dataset_path = "_".join(previous_block.data_link.split("_")[:-1])
        original_train_data = load_pickle(os.path.join(f"{dataset_path}_{current_dataset_idx}", "train.pkl"))
        X_train, X_dev, y_train, y_dev = train_test_split(original_train_data[0], original_train_data[1], test_size=0.2, random_state=42)
        dev_data = (X_dev, y_dev)
        train_data = (X_train, y_train)

        # for debug
        test_data = load_pickle(os.path.join(f"data/digits_test.pkl"))


        valid = False
        best_model_name = None
        best_params = None
        previous_model = run_model_code(train_data, previous_block.code_link)
        previous_score = previous_model.score(dev_data[0], dev_data[1])
        previous_test_score = previous_model.score(test_data[0], test_data[1])

        # Model selection and add data if needed
        while True and current_dataset_idx < 10:
            # random sleep for 0-5 seconds
            # random.seed(time() + self.port)
            # sleep(np.random.randint(0, 6))

            new_train_data = load_pickle(os.path.join(f"{dataset_path}_{current_dataset_idx}","train.pkl"))
            curr_train_data_len = len(train_data[1])
            additional_X_train, additional_y_train = new_train_data[0][curr_train_data_len:], new_train_data[1][curr_train_data_len:]
            train_data = (np.concatenate((train_data[0], additional_X_train)), np.concatenate((train_data[1], additional_y_train)))


            best_score, best_model_name, best_params = self.search_best_model(train_data, dev_data, previous_score)
            best_model = run_model_code(train_data, CodeSolution(best_model_name, best_params))
            test_score = best_model.score(test_data[0], test_data[1])
            print(current_dataset_idx, test_score)


            if  best_score > previous_score:
                valid = True
                break
            else:
                current_dataset_idx += 1


        if valid:
            model = run_model_code(train_data, CodeSolution(best_model_name, best_params))

            result = model.score(test_data[0], test_data[1])
            predictions = model.predict(unlabeled_data)

            block = Block(
                research_address=self.mining_address,
                index=previous_block.index + 1,
                previous_block_id=previous_block.index,
                task_description=previous_block.task_description,
                data_link=f"{dataset_path}_{current_dataset_idx}",
                constraint=previous_block.constraint,
                code_link=CodeSolution(best_model_name, best_params),
                predictions=predictions
            )




if __name__ == "__main__":
    node_url = f"http://127.0.0.1:6000"
    miner = MinerResearcher(node_url)
    miner.mine()


