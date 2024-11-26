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
from authority import AuthorityAgent, run_authority
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
            required = ['block']
            if not all(p in request.json for p in required):
                return 'Missing required transaction data', 400

            if not current_chain.ready_to_mine():
                return 'No block ready to mine!', 400

            block= request.get_json()['block']
            # 1. send to the authority node, here just is a relay
            post_data = {"block": block}
            response = requests.post(self.authority_link + "/Rsubmitblock", json=post_data)
            block = Block.from_dict(block)
            REWARD = 1

            if response.status_code == 200:
                # TODO, add to miner
                block.add_new_transaction(
                    sender="0",
                    recipient=block.research_address,
                    amount=REWARD,
                )
                try:
                    response_data = response.json()

                    authority_signature = response_data.get('authority_sign')
                    # only the authority provide the signature can the Rnode append the block to
                    # the main chain but not validate chain
                    if authority_signature:
                        print(f"Authority signature: {authority_signature}")
                        block.state = authority_signature
                        # TODO, add signature
                        block.index = len(current_chain.chain)
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
            latest_validation_blocks = {}

            # Count occurrences of validation_state=True per block index
            for block in validate_chain.chain:
                if block.validation_state:  # Only count blocks with validation_state=True
                    validation_counts[block.index] += 1
                    latest_validation_blocks[block.index] = block  # Keep the latest block for the index


            # Find the block with the maximum index that has at least 2 confirmations
            min_confirmations = 2
            eligible_block_ids = [
                block.index for index, block in latest_validation_blocks.items() if validation_counts[index] >= min_confirmations
            ]
            # TODO change to verify according to signature
            authority_block_ids = [block.index for block in current_chain.chain if block.research_address.lower() == "authority"]
            eligible_block_ids.extend(authority_block_ids)

            if not eligible_block_ids: # return the genius block
                if len(current_chain.chain) > 0:
                    main_block = current_chain.chain[0]
                else:
                    main_block = None
            else:
                main_block = current_chain.chain[max(eligible_block_ids)]
            if not main_block:
                return 'no block to be validated', 501
            response = main_block.to_dict()
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
        print(f"Node is running on port {self.port}")
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

            current_max_block_idx = current_chain.chain[-1].index if current_chain.chain else -1
            block = self.agent.publish_task(index=current_max_block_idx + 1)

            if block:
                current_chain.add_new_block(block)
                # print(f"New block is published: {block}")
                block_data = block.to_dict()
                response = {"message": f"New task is published, {block.task_description}","block": block_data}
                return response, 200
            else:
                return 'No block is published', 400


        @self.app.route('/Rsubmitblock', methods=['POST'])
        def Rsubmit_proof():
            # Now the authority only test the
            # performance of the model according to the prediction file
            # it submitted
            required = ['block']
            if not all(p in request.json for p in required):
                print('Missing required transaction data')
                return 'Missing required transaction data', 400

            block = request.get_json()['block']
            block = Block.from_dict(block)
            # for test
            valid, signature = self.agent.verify_block(block)
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
        self.address = wallet.get_address(f"private_key_{port}.pem")

    def setup_routes(self):
        @self.app.route('/Vsubmitproof', methods=['POST'])
        def validator_submit_proof():
            required = ["block"]
            if not all(p in request.json for p in required):
                return 'Missing required transaction data', 400

            # if not current_chain.ready_to_mine():
            #     return 'No block ready to mine!', 400

            # validator mined block
            block_data = request.json.get('block')
            block = Block.from_dict(block_data)


            REWARD = 0.001

            validate_chain.add_new_block(block)
            block.add_new_transaction(
                sender="0",
                recipient=block.validator_address,
                amount=REWARD,
            )

            response = {
                'message': "New Block Validated",
                'index': block.index,
                'transactions': block.txs_list,
            }

            return response, 200


        @self.app.route('/VMainChainBlock', methods=['GET'])
        def validator_get_main_chain_block():
            # Iterate through current_chain to find the first block that has not been validated by the current address
            for block in current_chain.chain:
                if block.research_address.lower() != "authority":  # Only consider blocks with non-zero indices
                    # Check if the block has been validated by the current address
                    block_validated = False

                    # Iterate through the validate_chain to see if the block has been validated by the current address
                    for validator_block in validate_chain.chain:
                        if validator_block.index == block.index and validator_block.validator_address == self.address:
                            # The current address has validated this block
                            block_validated = True
                            break  # No need to check further, we've found the current address validated it

                    # If the block has not been validated by the current address, return it
                    if not block_validated:
                        return block.to_dict(), 200  # Return the block as it hasn't been validated by the current address
            
            # If no block was found that hasn't been validated by the current address, return a message
            return 'no block to be validated', 400

            

        @self.app.route('/Vchain', methods=['GET'])
        def validator_full_chain():
            """
            Returns the valid chain, filtered to include only blocks that have at least
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



 
if __name__ == '__main__':
    node0 = ANode(6000)
    # threading.Thread(target=run_authority).start()
    threading.Thread(target=node0.run).start()


    research_node_ports = [6001, 6002, 6003]
    validator_node_ports = [6004, 6005, 6006]
    for port in research_node_ports:
        threading.Thread(target=Node(port).run).start()
    for port in validator_node_ports:
        threading.Thread(target=VNode(port).run).start()


