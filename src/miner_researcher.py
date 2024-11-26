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

class MinerResearcher(Miner):
    def __init__(self, NODE):
        super().__init__(NODE)
        self.mining_address = wallet.get_address(f"private_key_{self.port}.pem")
        print('Miner Researcher initialized!')


    def mine(self):
        pass

