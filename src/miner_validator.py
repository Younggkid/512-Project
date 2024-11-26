from anyio import current_time

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
from datetime import datetime
from utils import CodeSolution, run_model_code, load_pickle
from miner_researcher import MinerResearcher
import threading
import numpy as np
class MinerValidator(Miner):
    def __init__(self, NODE):
        super().__init__(NODE)
        self.mining_address = wallet.get_address(f"private_key_{self.port}.pem")
        self.print_prefix = f"VMiner - {self.port}:"
        print('Miner Validator initialized!')



    def mine(self):
        failed_attempts = 0
        successful_attempts = 0
        while True and failed_attempts < 10000:
            # random sleep for 0-2 seconds
            random.seed(int(time()) + int(self.port))
            sleep(np.random.randint(0, 3))
            response = requests.get(self.node_url + "/VMainChainBlock")
            if response.status_code != 200:
                # self.print("Failed to get main block")
                failed_attempts += 1
                sleep(5)
                continue

            main_block = response.json()
            main_block = Block.from_dict(main_block)

            # main_block = Block(
            #     research_address="research_address",
            #     index=0,
            #     previous_block_id=0,
            #     task_description="task_description",
            #     data_link=f"tmp/digits_0",
            #     constraint="constraint",
            #     code_link=CodeSolution("logistic_regression", {"C": 0.01, "max_iter": 100}),
            #     predictions=[0]*10,
            # )
            train_data = load_pickle(main_block.data_link + "/train.pkl")
            unlabeled_data = load_pickle(main_block.data_link + "/unlabeled.pkl")
            reproduced_model = run_model_code(train_data, main_block.code_link)
            predictions = reproduced_model.predict(unlabeled_data).tolist()

            # compare the predictions with the main block's predictions
            main_block_valid = False
            if predictions == main_block.predictions:
                main_block_valid = True


            # create a validation block
            validation_block = main_block
            validation_block.validator_address = self.mining_address
            validation_block.validation_state = main_block_valid
            # validator signs the block
            signature = self.auth_sign_block(validation_block)
            validation_block.digital_signature = signature
            json_data = {"block": validation_block.to_dict()}
            # publish the validation block
            response = requests.post(self.node_url + "/Vsubmitproof", json=json_data)
            if response.status_code == 200:
                self.print("Validation block published for block", main_block.index, "by Validator", self.port)
                successful_attempts += 1
            else:
                self.print("Validation block not published")
                failed_attempts += 1
                sleep(10)
    def print(self, *args):
        current_time = datetime.now().strftime("%H:%M:%S")
        print(f"[{current_time}]{self.print_prefix} ", *args)


if __name__ == "__main__":
    # researcher_node_url = f"http://127.0.0.1:6001"
    node_url1 = f"http://127.0.0.1:6002"
    node_url2 = f"http://127.0.0.1:6003"
    node_url3 = f"http://127.0.0.1:6004"
    miner_validator1 = MinerValidator(node_url1)
    miner_validator2 = MinerValidator(node_url2)
    miner_validator3 = MinerValidator(node_url3)
    # miner_researcher = MinerResearcher(researcher_node_url)

    # miner_researcher.mine()
    t1 = threading.Thread(target=miner_validator1.mine).start()
    t2 = threading.Thread(target=miner_validator2.mine).start()
    t3 = threading.Thread(target=miner_validator3.mine).start()







