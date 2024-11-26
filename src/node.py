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
from authority import AuthorityAgent
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
    def __init__(self, port):
        self.app = Flask(__name__)
        self.port = port
        self.node_identifier = str(uuid4()).replace('-', '')
        self.setup_routes()
        self.authority_link = ""

    def setup_routes(self):
        @self.app.route('/submitproof', methods=['POST'])
        def submit_proof():
            required = ['miner', 'block']
            if not all(p in request.form for p in required):
                return 'Missing required transaction data', 400

            if not current_chain.ready_to_mine():
                return 'No block ready to mine!', 400

            # block = {
            #     'index': len(current_chain.chain) + 1,
            #     'transactions': current_chain.current_transactions,
            #     'previous_hash': crypto.hash(current_chain.last_block)
            # }
            block = request.form['block']

            # 1. send to the authority node
            block_dict = block.to_dict()
            response = requests.post(self.authority_link + "/Rsubmitblock", json=block)

            REWARD = 1

            if response.status_code == 200:
                # TODO, add to miner
                current_chain.new_transaction(
                    sender="0",
                    recipient=request.form['miner'],
                    amount=REWARD,
                )

                block = current_chain.new_block(request.form['proof'])
                response = {
                    'message': "New Block Mined, should forward to validate now",
                    'index': block['index'],
                    'transactions': block['transactions'],
                    'proof': block['proof'],
                    'previous_hash': block['previous_hash'],
                }

                return response, 200
            else:
                return "Invalid block", 406

        @self.app.route('/MainChainBlock', methods=['GET'])
        def get_main_chain_block():
            # TODO Find the most recent confirmed block
            pass

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
            # TODO check validation chain to confirm the status of main chain
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


class ANode(Node):
    def __init__(self, port):
        super().__init__(port)
        self.agent = AuthorityAgent()

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

            # TODO check the block format input
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
            block = block_params
            valid = self.agent.verify_block(block)
            if valid:
                response = {
                    'authority_sign': self.agent.auth_sign_block(block)
                }
                return response, 200
            else:
                return "Invalid proof", 406



class VNode(Node):
    def __init__(self, port):
        super().__init__(port)

    def setup_routes(self):
        @self.app.route('/submitproof', methods=['POST'])
        def submit_proof():
            required = ['miner', 'block']
            if not all(p in request.form for p in required):
                return 'Missing required transaction data', 400

            if not current_chain.ready_to_mine():
                return 'No block ready to mine!', 400



            # validator mined block
            block = request.form['block']
            main_block_valid = block.validation_status


            REWARD = 1
            # TODO
            validate_chain.new_block(block)
            current_chain.new_transaction(
                sender="0",
                recipient=request.form['miner'],
                amount=REWARD,
            )

            response = {
                'message': "New Block Mined, should forward to validate now",
                'index': block['index'],
                'transactions': block['transactions'],
                'proof': block['proof'],
                'previous_hash': block['previous_hash'],
            }

            return response, 200




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
            # TODO check validation chain to confirm the status of main chain
            response = {
                'chain': current_chain.blockchain,
                'length': len(current_chain.blockchain),
            }
            return response, 200

        @self.app.route('/MainChainBlock', methods=['GET'])
        def get_main_chain_block():
            # TODO check the main chain's most recent semi-confirmed block
            response = {
                'block': current_chain.chain[-1]
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
