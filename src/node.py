from uuid import uuid4
from collections import defaultdict
from block import Block
import threading
from flask import Flask, request, json
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
import base64
# For now, the current chain is a global variable
# We can change it to the local variable in every node
current_chain = blockchain.Blockchain("blockchain.txt")
validate_chain = blockchain.Blockchain("blockchain.txt")
#authority_pub_key = wallet.get_public_key("private_key_6000.pem")
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
        self.authority_link = "http://127.0.0.1:6000"

    def setup_routes(self):
        @self.app.route('/submitproof', methods=['POST'])
        def submit_proof():
            required = ['block', 'researcher']
            if not all(p in request.json for p in required):
                return 'Missing required transaction data', 400

            if not current_chain.ready_to_mine():
                return 'No block ready to mine!', 400

            block_data = request.json.get('block')
            # 1. send to the authority node, here just is a relay
            block = Block.from_dict(block_data)
            # use dict here so that it can be serialized
            print(block_data)
            response = requests.post(self.authority_link + "/Rsubmitblock", json=block_data)

            REWARD = 1

            if response.status_code == 200:
                # TODO, add to miner
                block.add_new_transaction(
                    sender="0",
                    recipient=request.json['researcher'],
                    amount=REWARD,
                )
                try:
                    response_data = response.json()

                    authority_signature = response_data.get('authority_sign')
                    # only the authority provide the signature can the Rnode append the block to
                    # the main chain but not validate chain
                    if authority_signature:
                        print(f"Authority signature: {authority_signature}")
                        current_chain.add_new_block(block)
                        response = {
                            'message': "New Block Mined, should forward to validate now",
                            'index': block.index,
                            'transactions': block.txs_list,
                        }
                        return response, 200
                    else:
                        print("Authority signature not found in the response.")
                        return 'no signature from authority', 406  
                except ValueError:
                    print("Failed to decode JSON from the response.")
            else:
                return response.text, response.status_code

        @self.app.route('/MainChainBlock', methods=['GET'])
        def get_main_chain_block():
            # TODO Find the most recent confirmed block need to use validator chain
            # Dictionary to count validation_state=True occurrences for each index
            validation_counts = defaultdict(int)

            # Dictionary to store the latest block for each index
            latest_blocks = {}

            # Count occurrences of validation_state=True per block index
            for block in validate_chain.chain:
                if block.validation_state:  # Only count blocks with validation_state=True
                    validation_counts[block.index] += 1
                    latest_blocks[block.index] = block  # Keep the latest block for the index

            # Find the block with the maximum index that has at least 2 confirmations
            eligible_blocks = [
                block for index, block in latest_blocks.items() if validation_counts[index] >= 2
            ]

            if not eligible_blocks: # return the genius block
                return validate_chain.chain[0].to_dict()
            response = max(eligible_blocks, key=lambda block: block.index).to_dict()
            # Return the block with the highest index
            return response, 200

            

        @self.app.route('/chain', methods=['GET'])
        def full_chain():
            """
            Returns the main chain, filtered to include only blocks that have at least
            2 confirmations in the validator chain.
            """
            # Dictionary to count validation_state=True occurrences for each block index
            validation_counts = defaultdict(int)

            # Populate the validation counts from validator_chain
            for block in validate_chain.chain:
                if block.validation_state:
                    validation_counts[block.index] += 1

            # Filter main chain blocks that meet the validation threshold
            validated_main_chain = [
                block for block in current_chain.chain if validation_counts[block.index] >= 2
            ]

            response = {
                'chain': validated_main_chain,
                'length': len(validated_main_chain),
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

        @self.app.route('/publishtask', methods=['POST'])
        def publish_task():
            required = []
            if not all(p in request.json for p in required):
                return 'Missing required transaction data', 400



            block = self.agent.publish_task()
            if block:
                current_chain.add_new_block(block)
                print(f"New block is published: {block}")
                block_data = block.to_dict()
                response = {"message": f"New block is published, {block.task_description}","block": block_data}
                return response, 200
            else:
                return 'No block is published', 400


        @self.app.route('/Rsubmitblock', methods=['POST'])
        def Rsubmit_proof():
            # Now the authority only test the
            # performance of the model according to the prediction file
            # it submitted
            required = ['research_address', 'predictions', 'data_link', 'code_link']
            if not all(p in request.json for p in required):
                print('Missing required transaction data')
                return 'Missing required transaction data', 400

            #if not current_chain.ready_to_mine():
            #    return 'No block ready to mine!', 400

            # TODO check the block format input
            block_params = {
                "research_address": request.json['research_address'],
                "index": len(current_chain.chain) + 1,
                "previous_block_id": len(current_chain.chain),
                "task_description": "Train a model",
                "data_link": request.json['data_link'],
                "code_link": request.json['code_link'],
                "constraint": "Memory limit: 2GB",
                "validator_address": None,
                "predictions": ["class1", "class2"],
                "state": 'semi',
                "validation_state": False,
                "txs_list": current_chain.current_transactions,
                "digital_signature": request.json['digital_signature'],
            }
            block = Block.from_dict(block_params)
            # for test
            valid = True#self.agent.verify_block(block)
            if valid:
                response = {
                    'authority_sign': base64.b64encode(self.agent.auth_sign_block(block)).decode('utf-8')
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
            required = ['block', 'validator', 'vote']
            if not all(p in request.json for p in required):
                return 'Missing required transaction data', 400

            if not current_chain.ready_to_mine():
                return 'No block ready to mine!', 400

            # validator mined block
            block_data = request.json.get('block')
            block = Block.from_dict(block_data)

            vote = request.json.get('vote')
            block.validation_status = vote

            REWARD = 0.001
            # TODO
            validate_chain.add_new_block(block)
            block.add_new_transaction(
                sender="0",
                recipient=request.json['validator'],
                amount=REWARD,
            )

            response = {
                'message': "New Block Valid",
                'index': block.index,
                'transactions': block.txs_list,
            }

            return response, 200


        @self.app.route('/MainChainBlock', methods=['GET'])
        def get_main_chain_block():
            # TODO Find the most recent confirmed block need to use validator chain
            # Dictionary to count validation_state=True occurrences for each index
            validation_counts = defaultdict(int)

            # Dictionary to store the latest block for each index
            latest_blocks = {}

            # Count occurrences of validation_state=True per block index
            for block in validate_chain.chain:
                if block.validation_state:  # Only count blocks with validation_state=True
                    validation_counts[block.index] += 1
                    latest_blocks[block.index] = block  # Keep the latest block for the index

            # Find the block with the maximum index that has at least 2 confirmations
            eligible_blocks = [
                block for index, block in latest_blocks.items() if validation_counts[index] >= 2
            ]

            if not eligible_blocks: # return the genius block
                return validate_chain.chain[0].to_dict()
            response = max(eligible_blocks, key=lambda block: block.index).to_dict()
            # Return the block with the highest index
            return response, 200

            

        @self.app.route('/chain', methods=['GET'])
        def full_chain():
            """
            Returns the main chain, filtered to include only blocks that have at least
            2 confirmations in the validator chain.
            """
            # Dictionary to count validation_state=True occurrences for each block index
            validation_counts = defaultdict(int)

            # Populate the validation counts from validator_chain
            for block in validate_chain.chain:
                if block.validation_state:
                    validation_counts[block.index] += 1

            # Filter main chain blocks that meet the validation threshold
            validated_main_chain = [
                block for block in current_chain.chain if validation_counts[block.index] >= 2
            ]

            response = {
                'chain': validated_main_chain,
                'length': len(validated_main_chain),
            }
            return response, 200


# Current we only hard code authority to run in 6000
# Vnode runs in 6001,6002,6003
# 
if __name__ == '__main__':
    node1 = ANode(6000)
    node2 = Node(6001)
    # node3 = Node(6002)
    # node4 = Node(6003)

    t1 = threading.Thread(target=node1.run)
    t2 = threading.Thread(target=node2.run)
    # t3 = threading.Thread(target=node3.run)
    # t4 = threading.Thread(target=node4.run)

    t1.start()
    t2.start()
    # t3.start()
    # t4.start()
