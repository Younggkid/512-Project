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
from utils import CodeSolution, run_model_code, load_pickle

class MinerValidator(Miner):
    def __init__(self, NODE):
        super().__init__(NODE)
        self.mining_address = wallet.get_address(f"private_key_{self.port}.pem")
        print('Miner Validator initialized!')



    def mine(self):
        failed_attempts = 0
        successful_attempts = 0
        while True and failed_attempts < 1:
            main_block = requests.get(self.node_url + "/VMainChainBlock").json()
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
            reproduced_model = run_model_code(main_block, main_block.code_link)
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
            # publish the validation block
            response = requests.post(self.node_url + "/Vsubmitproof", json=validation_block.to_dict())
            if response.status_code == 200:
                print("Validation block published")
                successful_attempts += 1
            else:
                print("Validation block not published")
                failed_attempts += 1
                sleep(10)





