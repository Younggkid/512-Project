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
# For now, the current chain is a global variable
# We can change it to the local variable in every node



class Task:
    def __init__(self, task_name, task_data_path="data"):
        self.task_name = task_name
        self.train_data = load_pickle(f"{task_data_path}/{task_name}_train.pkl")
        self.test_data = load_pickle(f"{task_data_path}/{task_name}_test.pkl")
        self.unlabeled_data = load_pickle(f"{task_data_path}/{task_name}_unlabeled.pkl")
        self.performance_records = []
        self.best_performance = 0

    def evaluate(self, predictions: list):
        if self.task_name == "digits":
            return sum([1 for i in range(len(predictions)) if predictions[i] == self.test_data[1][i]]) / len(predictions)
        elif self.task_name == "iris":
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
        self.task_name_queue = ["digits", "iris"]
        self.current_task = None
        self.task_history = []
        self.publish_task()


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

    def publish_task(self):
        task_name = self.task_name_queue.pop(0)
        if self.current_task:
            self.task_history.append(self.current_task)
        self.current_task = Task(task_name)
        print(f"New task published: {task_name}")
        # save the train data to a link in 10 pieces, make it convenient for the research miner to simulate the data increment process
        for i in range(10):
            data_len = len(self.current_task.train_data[0])
            data_start = i * data_len // 10
            data_start = 0
            data_end = (i + 1) * data_len // 10
            save_pickle([self.current_task.train_data[0][data_start:data_end],
                         self.current_task.train_data[1][data_start:data_end]], f"tmp/{task_name}_{i}/train.pkl")
            save_pickle(self.current_task.unlabeled_data, f"tmp/{task_name}_{i}/unlabeled.pkl")
        # TODO broadcast the task to the network
        return task_name



    def verify_block(self, block: Block):
        # verify the block's result
        is_best = self.current_task.evaluate_block(block)
        if is_best:
            signature = self.auth_sign_block(block)
        else:
            signature = None

        return is_best, signature


if __name__ == "__main__":
    agent = AuthorityAgent()
    predictions = agent.current_task.test_data[1]
    block = Block("research_address", 1, "previous_block_id", "task_description", "data_link", "code_link", "constraint", "validator_address", ["predictions"], "state", True, [{"sender": "sender", "recipient": "recipient", "amount": 1}], None)
    block.predictions = [0] * len(predictions)
    is_best, signature = agent.verify_block(block)
    block.predictions = predictions
    is_best, signature = agent.verify_block(block)