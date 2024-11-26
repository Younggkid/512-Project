import random
import requests
import sys
import wallet
from time import sleep, time
from numpy import average
import re
import blockchain
import crypto
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes
from datetime import datetime


hash_per_second = []


class Miner(object):

    def __init__(self, NODE):
        self.node_url = NODE
        self.port = re.search(r'http://\d+\.\d+\.\d+\.\d+:(\d+)', self.node_url).group(1)
        private_key_filename = f"private_key_{self.port}.pem"
        self.private_key = wallet.read_key(private_key_filename)
        try:
            # Use wallet's get_address function to retrieve miner address
            self.mining_address = wallet.get_address(private_key_filename)  
            print('Miner address:', self.mining_address)
        except FileNotFoundError:
            print("'private_key.pem' not detected! Run 'run_wallet.py' first to generate keys!", file=sys.stderr)
            sys.exit(0)
        #self.mining_address = wallet.get_address("private_key.pem") 
        print('Miner initialized!')

    @property
    def current_chain(self):
        response = requests.get(self.node_url + "/chain")
        chain = blockchain.Blockchain()
        chain.chain = response["chain"]
        return chain


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


    def proof_of_work(self, block) -> int:
        """
        Proof of Work (POW algorithm)
            - Find <int> p' such that p' combined by p < POW target, where p is the previous hash
            - for hash(pp') to be smaller than the POW target, the hash must have N number of leading zeros
            - leading zeros N can be increased to increase mining difficulty
        :param block: <dict>
        :return: <int> p'
        """

        guesses = 0
        proof = 0
        start = time()
        while not crypto.valid_proof(block, proof):
            proof = random.getrandbits(256)
            guesses += 1
        end = time()
        hash_per_second.append(guesses / (end - start))
        print(f'Hashrate: {average(hash_per_second) / 1000:.2f} KH/s')
        return proof

    def mine(self):
        while True:
            while requests.get(self.node_url + "/work").status_code == 204:  # Empty
                sleep(2)
            response = requests.get(self.node_url + "/work")

            proof = self.proof_of_work(response.json())
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

    def print(self, *args):
        current_time = datetime.now().strftime("%H:%M:%S")
        print(f"[{current_time}]{self.print_prefix} ", *args)
