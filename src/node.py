from uuid import uuid4

from block import Block, BlockState
import threading
from flask import Flask, request
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
authority_pub_key = wallet.get_public_key("private_key_6000.pem")
# Generate a globally unique address for this node
node_identifier = str(uuid4()).replace('-', '')
'''
    Research miner node
    The node should receive http requests from miner
    and response
'''
class Node:
    def __init__(self, port, blockchain_file):
        self.app = Flask(__name__)
        self.port = port
        self.node_identifier = str(uuid4()).replace('-', '')
        self.setup_routes()

    def setup_routes(self):
        @self.app.route('/submitproof', methods=['POST'])
        def submit_proof():
            required = ['miner', 'proof']
            if not all(p in request.form for p in required):
                return 'Missing required transaction data', 400

            if not current_chain.ready_to_mine():
                return 'No block ready to mine!', 400

            block = {
                'index': len(current_chain.chain) + 1,
                'transactions': current_chain.current_transactions,
                'previous_hash': crypto.hash(current_chain.last_block)
            }

            valid = crypto.valid_proof(block, int(request.form['proof']), True)
            REWARD = 1

            if valid:
                block = current_chain.new_block(request.form['proof'])
                response = {
                    'message': "New Block Mined, should forward to validate now",
                    'index': block['index'],
                    'transactions': block['transactions'],
                    'proof': block['proof'],
                    'previous_hash': block['previous_hash'],
                }
                current_chain.new_transaction(
                    sender="0",
                    recipient=request.form['miner'],
                    amount=REWARD,
                )
                return response, 200
            else:
                return "Invalid proof", 406

        @self.app.route('/transactions/new', methods=['POST'])
        def new_transaction():
            required = ['transaction', 'signature', 'pubkey']
            if not all(p in request.form for p in required):
                return 'Missing required transaction data', 400

            transaction = request.form['transaction']
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

        @self.app.route('/chain', methods=['GET'])
        def full_chain():
            response = {
                'chain': current_chain.blockchain,
                'length': len(current_chain.blockchain),
            }
            return response, 200

        @self.app.route('/work', methods=['GET'])
        def broadcast_work():
            """
            sends block to be mined
                incoming transactions coming after block to be mined still is being mined will be added to pending_transactions
                After set time interval, if no block has been mined (blockchain size has not increased), pending_transactions is
                    appended to next block to be broadcasted
            """
            if current_chain.ready_to_push:
                current_chain.push_pending()
            if not current_chain.ready_to_mine():
                return "", 204
            response = {
                'index': len(current_chain.chain) + 1,
                'transactions': current_chain.current_transactions,
                'previous_hash': crypto.hash(current_chain.last_block)
            }
            return response, 200

    def run(self):
        self.app.run(host='127.0.0.1', port=self.port, debug=False, threaded=True)

class VNode:
    def __init__(self, port):
        self.app = Flask(__name__)
        self.port = port
        self.node_identifier = str(uuid4()).replace('-', '')
        self.setup_routes()
    '''
    TO DO:
    '''
    # The validator's main task
    def evaluate_result():
        return False
    
    def setup_routes(self):
        # The /broadcast_research is sent from the researchers instead of authority
        # It will send a response to the authority
        @self.app.route('/broadcast_research', methods=['POST'])
        def validator():
            payload = {
                'validator': wallet.get_address(f"private_key_{self.port}.txt"),
                'index': request.form['index'],
                'vote': False
            }
            required = ['researcher', 'index', 'predictions', 'data_link', 'code_link', 'state', 'digital_signature', 'hash','authority_ds']
            if not all(p in request.form for p in required):
                return 'Missing required transaction data', 400

            if not current_chain.ready_to_mine():
                return 'No block ready to mine!', 400
            
            if not self.evaluate_result():
                response = requests.post('http://127.0.0.1:6000/vote', json=payload)
                return 'The block submitted is garbage! Try again!', 400
            
            if not crypto.verify_signature(request.form('authority_ds'), 
                                           request.form('digital_signature'),
                                           authority_pub_key):
                return 'Did not get approved by Authority!', 400
            
            if request.form('state') != BlockState.SEMI_CONFIRM:
                return 'Did not get semi confirmed by the authority', 400
            # Create the block data, state here should be confirmed by authority
            block = {
                'researcher': request.form['researcher'],
                'index': request.form['index'],
                'predictions': request.form['predictions'],
                'data_link': request.form['data_link'],
                'code_link': request.form['code_link'],
                'digital_signature': request.form['digital_signature'],
                'hash': request.form['hash']
            }

            # Prepare the data for the POST request
            payload['vote'] = True

            # Send the POST request
            try:
                response = requests.post('http://127.0.0.1:6000/vote', json=payload)
                if response.status_code == 200:
                    return 'Block and vote broadcasted successfully!', 200
                else:
                    return f"Failed to broadcast block. Error: {response.text}", response.status_code
            except requests.RequestException as e:
                return f"Error sending POST request: {str(e)}", 500
        
        


    def run(self):
        self.app.run(host='127.0.0.1', port=self.port, debug=False, threaded=True)



# Current we only hard code authority to run in 6000
# Vnode runs in 6001,6002,6003
# 
if __name__ == '__main__':
    node2 = VNode(6001)
    node3 = VNode(6002)
    node4 = VNode(6003)

    t2 = threading.Thread(target=node2.run)
    t3 = threading.Thread(target=node3.run)
    t4 = threading.Thread(target=node4.run)

    t2.start()
    t3.start()
    t4.start()
