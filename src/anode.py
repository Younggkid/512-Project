from uuid import uuid4
from threading import Thread, Event
from block import Block, BlockState
import threading
from flask import Flask, request, jsonify
from base64 import b64decode
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.serialization import load_pem_public_key
from cryptography.exceptions import InvalidSignature
import blockchain
import crypto
import wallet
import requests
# For now, the current chain is a global variable
# We can change it to the local variable in every node
current_chain = blockchain.Blockchain("blockchain.txt")
validate_chain = blockchain.Blockchain("blockchain.txt")
authority_pri_key = wallet.read_key("private_key_6000.pem")
authority_pub_key = wallet.get_public_key("private_key_6000.pem")
# Generate a globally unique address for this node
node_identifier = str(uuid4()).replace('-', '')

class ANode:
    def __init__(self, port):
        self.app = Flask(__name__)
        self.port = port
        self.node_identifier = str(uuid4()).replace('-', '')
        self.max_perf = 0 # Authority should store the current best performance
        self.vote_slots = {}
        self.setup_routes()
    # The authority's signature does not need to be included in the block,
    # So I return it, it is expected to be transmitted through the network
    def auth_sign_block(self, block, private_key):
        block_hash = block.calculate_hash()
        signature = private_key.sign(
            block_hash,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        return signature

    '''
    TO DO:
    Use test set to calculate the submission's performance
    '''
    def evaluate_result(self) -> bool:
        return False
    '''
    TO DO:
    Check if the format of the block is correct, such as:
    data link, code link, etc..
    '''
    def validate_result(self) -> bool:
        return False
              
    def wait_for_votes(self, index):
        vote_slot = self.vote_slots[index]
        print(f"Waiting for votes for block index {index}...")

        # Wait for majority or timeout
        if vote_slot["event"].wait(timeout=20):
            print(f"Majority vote received for block index {index}. Proceeding...")
            self.process_block(index)
        else:
            print(f"Timeout. Not enough votes collected for block index {index}.")
            # Cleanup the vote slot after timeout
            self.vote_slots.pop(index, None)

    def process_block(self, index):
        # Assume vote_slot exists at this point
        vote_slot = self.vote_slots.pop(index, None)
        if not vote_slot:
            return

        REWARD_RES = 1
        REWARD_VAL = 0.001

        # Extract block data (replace with your block retrieval logic)
        block = self.current_chain.get_block_by_index(index)  # Placeholder method
        if not block:
            print(f"Block index {index} not found!")
            return

        block_data = block.to_dict()

        # Reward research address
        self.current_chain.new_transaction(
            sender="0",
            recipient=block_data['research_address'],
            amount=REWARD_RES,
        )

        # Reward participating validators
        for vote_record in vote_slot["votes"]:
            validator = vote_record["validator"]
            self.current_chain.new_transaction(
                sender="0",
                recipient=validator,
                amount=REWARD_VAL,
            )

        print(f"Block index {index} processed. Validators rewarded.")

    def setup_routes(self):
        '''
        This API is used to communicate with Researcher Miner
        Accept the block
        '''
        @self.app.route('/Rsubmitblock', methods=['POST'])
        def Rsubmit_proof():
            # Now the authority only test the 
            # performance of the model according to the prediction file
            # it submitted
            required = ['researcher', 'predictions', 'data_link', 'code_link', 'digital_signature']
            if not all(p in request.form for p in required):
                return 'Missing required transaction data', 400

            if not current_chain.ready_to_mine():
                return 'No block ready to mine!', 400
            
            if not self.evaluate_result():
                return 'The block submitted is garbage! Try again!', 400

            block_params = {
            "research_address": request.form['researcher'],
            "index": len(current_chain.chain) + 1,
            "previous_block_id": len(current_chain.chain),
            "task_description": "Train a model",
            "data_link": request.form('data_link'),
            "code_link": request.form('code_link'),
            "constraint": "Memory limit: 2GB",
            "validator_address": None,
            "predictions": ["class1", "class2"],
            "state": BlockState.SEMI_CONFIRM,
            "validation_state": False,
            "txs_list": current_chain.current_transactions,
            "digital_signature": request.form['digital_signature'], 
        }
            valid = self.validate_result(block_params)
            if valid:
                # append the block to the current chain, but it is semi-confirm
                block = current_chain.new_block(block_params)
                response = {
                    'message': "New Block Mined, forward to validate now",
                    'index': block['index'],
                    'transactions': block['transactions'],
                    'authority_sign': self.auth_sign_block(block, authority_pri_key)
                }

                return response, 200
            else:
                return "Invalid proof", 406
        '''
        This API is used to assign work with Researcher Miner
        '''
        @self.app.route('/Rwork', methods=['GET'])
        def publish_work_to_researcher():
            """
            sends block to be mined
            """
            if current_chain.ready_to_push:
                current_chain.push_pending()
            if not current_chain.ready_to_mine():
                return "", 204
            # publish the task
            response = {
                'index': len(current_chain.chain) + 1,
                'transactions': current_chain.current_transactions,
                'performance': self.max_perf,
                "task_description": "Train a model",
                "data_link": 'http://data.example.com',
                "code_link": 'http://code.example.com',
                "constraint": "Memory limit: 2GB",
            }
            return response, 200
            
        '''
        This API is used to communicate with Validator Miner
        It collects votes from the VM
        '''
        @self.app.route('/vote', methods=['POST'])
        def collect_votes(self):
            data = request.get_json()
            block = data.get('block')
            vote = data.get('vote')
            va = data.get('validator')

            if block and vote is not None and va:
                index = block.get('index')
                if index is None:
                    return jsonify({'status': 'Block must include an index'}), 400

                # Initialize vote slot for the index if it doesn't exist
                if index not in self.vote_slots:
                    self.vote_slots[index] = {
                        "votes": [],  # Store votes
                        "validators": set(),  # Track validators who have voted
                        "event": Event()  # For signaling majority
                    }
                    # Start a thread to handle vote collection for this index
                    Thread(target=self.wait_for_votes, args=(index,)).start()

                # Prevent duplicate votes from the same validator
                if va in self.vote_slots[index]["validators"]:
                    return jsonify({'status': f'Validator {va} has already voted for block {index}'}), 400

                # Record the vote and the validator's address
                self.vote_slots[index]["votes"].append({"validator": va, "vote": vote})
                self.vote_slots[index]["validators"].add(va)

                # Check if majority vote is reached
                if sum(1 for v in self.vote_slots[index]["votes"] if v["vote"]) >= 2:  # Majority condition
                    self.vote_slots[index]["event"].set()  # Signal the event

                return jsonify({'status': f'Vote received for block index {index} from validator {va}'}), 200

            return jsonify({'status': 'Invalid payload'}), 400
        
        
        '''
        This is to add new transactions, not tested.
        BE CAREFUL!
        '''
        @self.app.route('/transactions/new', methods=['POST'])
        def new_transaction():
            required = ['transaction', 'signature', 'pubkey']
            if not all(p in request.form for p in required):
                return 'Missing required transaction data', 400

            transaction = ['transaction']
            sender, recipient, amount = transaction.split(':')
            amount = float(amount)
            current_balance = current_chain.current_balances.get(sender, 0)
            pending_balance = current_chain.pending_balances.get(sender, 0)

            valid_signature = crypto.verify_signature(
                b64decode(request.form['signature']),
                transaction,
                request.form['pubkey']
            )
            valid_balance = wallet.get_balance(sender)[0] >= (amount + current_balance + pending_balance)

            if not valid_signature:
                return "Invalid signature", 401
            if not valid_balance:
                return "Insufficient funds", 401

            current_chain.new_transaction(sender, recipient, amount)
            return "Success", 201
        '''
        Get the whole main chain
        '''
        @self.app.route('/chain', methods=['GET'])
        def full_chain():
            response = {
                'chain': current_chain.blockchain,
                'length': len(current_chain.blockchain),
            }
            return response, 200

    def run(self):
        self.app.run(host='127.0.0.1', port=self.port, debug=False, threaded=True)

if __name__ == '__main__':
    # Anode is running at 6000
    node = ANode(port=6000)
    
    node.run()