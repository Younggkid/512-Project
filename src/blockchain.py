import json
import sys
from block import Block, BlockState
from time import time
from crypto import hash, valid_proof
from urllib.parse import urlparse
import requests

class Blockchain(object):
    @property
    def last_block(self) -> Block:
        # Returns the last (header) block in the chain
        return self.chain[-1]

    @property
    def blockchain(self) -> list:
        return self.chain
    
    def __init__(self, chain_file):
        self.chain = []
        self.pending_transactions = []
        self.current_transactions = []
        self.pending_balances = {}
        self.current_balances = {}
        self.push_time = 0
        self.mine_time = 0
        self.nodes = set()
        # If chain already exists on disk
        #try:
        #   with open(chain_file, 'r') as blockchain_file:
        #        self.chain = json.loads(blockchain_file.read())
        #except (FileNotFoundError, json.JSONDecodeError):
        #    print('Error while importing chain_file! But that is OK!', file=sys.stderr)
        """
        Create chain with default Genesis Block.
        The Genesis Block should be created by the authority
        """
        gen_block_params = {
            "research_address": "Autority",
            "index": 0,
            "previous_block_id": '-1',
            "task_description": "Train a model",
            "data_link": "http://data.example.com",
            "code_link": "http://code.example.com",
            "constraint": "Memory limit: 2GB",
            "validator_address": None,
            "predictions": ["class1", "class2"],
            "state": BlockState.CONFIRM,
            "validation_state": True,
            "txs_list": [],
            "digital_signature": None, #todo, should use authority's key
        }
        self.new_block(**gen_block_params)
    
    """
    Use the parameter list to create a new block, this should be
    called from node.py.
    """
    def new_block(self, research_address,
        index,
        previous_block_id,
        task_description,
        data_link,
        code_link,
        constraint,
        validator_address = None,
        predictions = None,
        state = None,
        validation_state= None,
        txs_list = None,
        digital_signature = None) -> Block:
        """
        Creates new block to add to the blockchain. 
        """
        block = Block(research_address,
        index,
        previous_block_id,
        task_description,
        data_link,
        code_link,
        constraint,
        validator_address,
        predictions,
        state,
        validation_state,
        txs_list,
        digital_signature)
        return block

    def new_transaction(self, sender, recipient, amount):
        """
        Compiles and appends new incoming transactions to add to the block.
        Once mined, transactions will "go through" and are added to the blockchain.
        Incoming transactions, therefore, are not transacted until the block is mined.
        :param sender: <str> Wallet address of the Sender
        :param recipient: <str> Wallet address of the Recipient
        :param amount: <float> Amount of $TR (Robcoin) to be transacted
        :return: <int> Index of transaction to add to the new block. (see example-block.py)
        """
        self.pending_transactions.append(
            {
                'sender': sender,
                'recipient': recipient,
                'amount': amount,
            })
        if sender not in self.pending_balances:
            self.pending_balances[sender] = amount
        else:
            self.pending_balances[sender] += amount
        
        return self.last_block['index'] + 1

    def save_blockchain(self, file="blockchain.txt"):
        """
        :param file: saves blockchain to 'blockchain.txt' in case node goes down
        """
        with open(file, 'w+', encoding='utf-8') as out:
            json.dump(self.chain, out, ensure_ascii=False, indent=4)  # Padding to make json look pretty

    def ready_to_push(self) -> bool:
        return (time() - self.push_time) >= 10  # seconds

    def ready_to_mine(self) -> bool:
        return (time() - self.mine_time) >= 10

    def push_pending(self) -> list:
        self.current_transactions += self.pending_transactions
        self.pending_transactions = []
        self.push_time = time()
        for sender in self.pending_balances.keys():
            if sender not in self.current_balances:
                self.current_balances[sender] = self.pending_balances
            else:
                self.current_balances[sender] += self.pending_balances
        self.pending_balances = {}
    
    def register_node(self, address):
        parsed_url = urlparse(address)
        self.nodes.add(parsed_url.netloc)

    def valid_chain(self, chain):
        last_block = chain[0]
        current_index = 1

        while current_index < len(chain):
            block = chain[current_index]
            print(f"{last_block}")
            print(f"{block}")
            print("\n--------\n")
            if block['previous_hash'] != self.hash(last_block):
                return False
            
            if not valid_proof(block, block["proof"]):
                return False
            
            last_block = block
            current_index += 1
        
        return True 

    def resolve_conflicts(self):

        neighbours = self.nodes
        new_chain = None

        max_length = len(self.chain)

        for node in neighbours:
            response = requests.get(f'http://{node}/chain')

            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']

                if length > max_length and self.valid_chain(chain):
                    max_length = length
                    new_chain = chain
        if new_chain:
            self.chain = new_chain
            return True
        
        return False
