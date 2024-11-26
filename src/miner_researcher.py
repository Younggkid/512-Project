from anyio import current_time

from miner import Miner

import random
import requests
import sys
import wallet
from time import sleep, time
from datetime import datetime
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
        self.print_prefix = f"RMiner - {self.port}:"


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
        failed_attempts = 0
        successful_attempts = 0
        while True and failed_attempts < 10:
            # shuffle the self.parameters_list
            for model_name in self.model_sets:
                random.shuffle(self.parameters_list[model_name])
            responses = requests.get(self.node_url + "/MainChainBlock")
            previous_block = Block.from_dict(responses.json())

            unlabeled_data = load_pickle(os.path.join(previous_block.data_link, "unlabeled.pkl"))


            current_dataset_idx = int(previous_block.data_link.split("_")[-1])
            dataset_path = "_".join(previous_block.data_link.split("_")[:-1])
            train_data = load_pickle(os.path.join(f"{dataset_path}_{current_dataset_idx}", "train.pkl"))
            dev_data = load_pickle(os.path.join(f"{dataset_path}_{current_dataset_idx}", "dev.pkl"))

            # for debug
            task_name = previous_block.task_description
            test_data = load_pickle(os.path.join(f"data/{task_name}_test.pkl"))


            valid = False
            best_model_name = None
            best_params = None
            previous_model = run_model_code(train_data, previous_block.code_link)
            previous_score = previous_model.score(dev_data[0], dev_data[1])
            previous_test_score = previous_model.score(test_data[0], test_data[1])
            previous_dev_score = previous_model.score(dev_data[0], dev_data[1])
            # self.print("previous test score", previous_test_score, "previous dev score", previous_dev_score)

            # Model selection and add data if needed
            while True and current_dataset_idx < 10:
                # random sleep for 0-5 seconds
                # random.seed(time() + self.port)
                # sleep(np.random.randint(0, 6))

                train_data = load_pickle(os.path.join(f"{dataset_path}_{current_dataset_idx}", "train.pkl"))


                best_score, best_model_name, best_params = self.search_best_model(train_data, dev_data, previous_score)
                best_model = run_model_code(train_data, CodeSolution(best_model_name, best_params))
                test_score = best_model.score(test_data[0], test_data[1])
                # self.print(f"Train_data-{current_dataset_idx}. current test score:", test_score, "previous test score:", previous_test_score)
                # self.print(f"Train_data-{current_dataset_idx}. current dev score:", best_model.score(dev_data[0], dev_data[1]), "previous dev score:", previous_dev_score)
                # self.print(f"Train_data-{current_dataset_idx}. current test score:", test_score, "previous test score:", previous_test_score)

                if  best_score > previous_score:
                    valid = True
                    model = run_model_code(train_data, CodeSolution(best_model_name, best_params))

                    result = model.score(test_data[0], test_data[1])
                    predictions = model.predict(unlabeled_data).tolist()

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
                    block_data = block.to_dict()
                    response = {
                        "block": block_data
                    }
                    response = requests.post(self.node_url + "/submitproof", json=response)

                    if response.status_code == 200:
                        successful_attempts += 1
                        failed_attempts = 0
                        index = response.json()["index"]
                        task_name = block.task_description
                        self.print(f"Successfully mined Block-{index}. Dev score: {round(best_score, 2)}. Task: {task_name}. Total successful attempts: {successful_attempts}")
                        sleep(1)
                        break
                    else:
                        # self.print(f"New solution is not valid for Block-{block.index}")
                        current_dataset_idx += 1
                        sleep(5)
                else:
                    current_dataset_idx += 1

            if current_dataset_idx >= 10:
                failed_attempts += 1
                self.print("Failed to find a better model")
                sleep(20)


        self.print("Summary for this miner:")
        self.print(f"Successful attempts: {successful_attempts}")
        self.print(f"Failed attempts: {failed_attempts}")

    def print(self, *args):
        current_time = datetime.now().strftime("%H:%M:%S")
        print(f"[{current_time}]{self.print_prefix} ", *args)







if __name__ == "__main__":
    node_url = f"http://127.0.0.1:6001"
    miner = MinerResearcher(node_url)
    miner.mine()


