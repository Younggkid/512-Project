from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.serialization import load_pem_public_key
from cryptography.exceptions import InvalidSignature
import blockchain
import crypto
import wallet
import requests


from utils import load_pickle, save_pickle
from block import Block
from miner import Miner
import numpy as np
import time
import json
from time import sleep
from utils import CodeSolution
from datetime import datetime

# For now, the current chain is a global variable
# We can change it to the local variable in every node



class Task:
    def __init__(self, task_name, task_data_path="data"):
        self.task_name = task_name
        self.train_data = load_pickle(f"{task_data_path}/{task_name}_train.pkl")
        self.test_data = load_pickle(f"{task_data_path}/{task_name}_test.pkl")
        self.dev_data = load_pickle(f"{task_data_path}/{task_name}_dev.pkl")
        self.unlabeled_data = load_pickle(f"{task_data_path}/{task_name}_unlabeled.pkl")
        self.performance_records = []
        self.best_performance = 0

    def evaluate(self, predictions: list):

        return sum([1 for i in range(len(predictions)) if predictions[i] == self.test_data[1][i]]) / len(predictions)

    def evaluate_block(self, block: Block):
        is_best = False
        block_performance = self.evaluate(block.predictions)
        self.performance_records.append([block.index, block_performance])
        if block_performance > self.best_performance:
            self.best_performance = block_performance
            print(f"New best performance! Block {block.index}: {block_performance}")
            is_best = True
        return is_best




class AuthorityAgent:
    def __init__(self, task_data_path="data"):
        self.private_key = wallet.read_key("private_key.pem")
        self.task_name_queue = ["digits", "iris", "wine", "breast_cancer"]
        self.task_name_queue = self.task_name_queue * 10
        self.current_task = None
        self.task_history = []



    def auth_sign_block(self, block):
        block_hash = block.calculate_hash()
        signature = self.private_key.sign(
            block_hash,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        return signature

    def publish_task(self,index=0):
        if len(self.task_name_queue) == 0:
            print("No task in the queue")
            return None
        task_name = self.task_name_queue.pop(0)
        task_name = self.task_name_queue[0]
        if self.current_task:
            self.task_history.append(self.current_task)
        self.current_task = Task(task_name)

        # save the train data to a link in 10 pieces, make it convenient for the research miner to simulate the data increment process
        for i in range(10):
            data_len = len(self.current_task.train_data[0])
            data_start = 0
            data_end = (i + 1) * data_len // 10
            save_pickle([self.current_task.train_data[0][data_start:data_end],
                         self.current_task.train_data[1][data_start:data_end]], f"tmp/{task_name}_{i}/train.pkl")
            save_pickle(self.current_task.unlabeled_data, f"tmp/{task_name}_{i}/unlabeled.pkl")
            save_pickle(self.current_task.dev_data, f"tmp/{task_name}_{i}/dev.pkl")

        # TODO broadcast the task to the network
        predictions = [0] * len(self.current_task.test_data[1])



        code_solution = CodeSolution("random", {})
        block = Block(research_address="authority",
                        index=index,
                        previous_block_id=index-1,
                        task_description=task_name,
                        data_link=f"tmp/{task_name}_0",
                        code_link=code_solution,
                        constraint="constraint",
                        validator_address=None,
                        predictions=predictions,
                        state=None,
                        txs_list=None,
                        digital_signature=None)
        signature = self.auth_sign_block(block)
        block.state = signature
        return block



    def verify_block(self, block: Block):
        # verify the block's result
        is_best = self.current_task.evaluate_block(block)
        if is_best:
            signature = self.auth_sign_block(block)
        else:
            signature = None

        return is_best, signature

class MinerAuthority(Miner):
    def __init__(self, NODE):
        super().__init__(NODE)
        self.mining_address = wallet.get_address(f"private_key_{self.port}.pem")

        self.print_prefix = f"AMiner - {self.port}:"
        self.initialize_print()


    def mine(self):
        while True:
            try:
                response = requests.post(self.node_url + "/publishtask", json={})
            except Exception as error:
                print(f'{error}')
                time.sleep(10)
                continue
            if response.status_code == 200:
                message = response.json()['message']
                self.print(message)
                # print("Task published")
                time.sleep(60)



def run_authority():
    miner = MinerAuthority("http://127.0.0.1:6000")
    try:
        miner.mine()
    except Exception as error:
        print(f'Connection error - {error}')
        print()


if __name__ == "__main__":
    # agent = AuthorityAgent()
    # agent.publish_task()
    # predictions = agent.current_task.test_data[1]
    # block = Block("research_address", 1, "previous_block_id", "task_description", "data_link", "code_link", "constraint", "validator_address", ["predictions"], "state", True, [{"sender": "sender", "recipient": "recipient", "amount": 1}], None)
    # block.predictions = [0] * len(predictions)
    # is_best, signature = agent.verify_block(block)
    # block.predictions = predictions
    # is_best, signature = agent.verify_block(block)



    miner = MinerAuthority("http://127.0.0.1:6000")
    try:
        miner.mine()
    except Exception as error:
        print(f'Connection error - {error}')
        print()
        print('Please check your internet connection. Is the node online?')