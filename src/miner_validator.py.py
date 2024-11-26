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

class MinerValidator(Miner):
    def __init__(self, NODE):
        super().__init__(NODE)
        self.mining_address = wallet.get_address(f"private_key_{self.port}.pem")
        print('Miner Validator initialized!')


    def validate(self):
        pass

    def mine(self):
        while True:
            while requests.get(self.node_url + "/work").status_code == 204:  # Empty
                sleep(2)

            response = requests.get(self.node_url + "/work")

            # 1. Find the main block to be verified
            main_block = requests.get(self.node_url + "/chain").json()["chain"][-1]
            # 2. Reproduce the main block's result
            # 3. Submit the result to the node

            proof = self.validate(response.json())
            print(f'Proof found: {proof}')
            print('Sending now to node...')
            if requests.get(self.node_url + "/work").status_code == 200:  # worked
                print('Success! You have been rewarded with 1 $TR (to be added in next block)')
                print()
            else:
                print('Error! Did not send block in on-time!')
                print()
            headers = {'User-Agent': 'Mozilla/5.0'}
            requests.post(self.node_url + "/submitproof", headers=headers, data={
                "proof": proof,
                "miner": self.mining_address
            })