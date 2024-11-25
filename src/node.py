from uuid import uuid4


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

current_chain = blockchain.Blockchain("blockchain.txt")
# Generate a globally unique address for this node
node_identifier = str(uuid4()).replace('-', '')
class Node:
    def __init__(self, port, blockchain_file):
        self.app = Flask(__name__)
        self.port = port
        self.current_chain = blockchain.Blockchain(blockchain_file)
        self.node_identifier = str(uuid4()).replace('-', '')
        self.setup_routes()

    def verify_signature(self, signature, packet, pub_key_serialized):
        try:
            pub_key = load_pem_public_key(bytes(pub_key_serialized, 'utf-8'))
            pub_key.verify(
                signature,
                packet.encode(),
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
        except InvalidSignature:
            return False
        return True

    def setup_routes(self):
        @self.app.route('/submitproof', methods=['POST'])
        def submit_proof():
            required = ['miner', 'proof']
            if not all(p in request.form for p in required):
                return 'Missing required transaction data', 400

            if not self.current_chain.ready_to_mine():
                return 'No block ready to mine!', 400

            block = {
                'index': len(self.current_chain.chain) + 1,
                'transactions': self.current_chain.current_transactions,
                'previous_hash': crypto.hash(self.current_chain.last_block)
            }

            valid = crypto.valid_proof(block, int(request.form['proof']), True)
            REWARD = 1

            if valid:
                block = self.current_chain.new_block(request.form['proof'])
                response = {
                    'message': f"New Block Mined, {REWARD} $TR has been added to your account",
                    'index': block['index'],
                    'transactions': block['transactions'],
                    'proof': block['proof'],
                    'previous_hash': block['previous_hash'],
                }
                self.current_chain.new_transaction(
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
            current_balance = self.current_chain.current_balances.get(sender, 0)
            pending_balance = self.current_chain.pending_balances.get(sender, 0)

            valid_signature = self.verify_signature(
                b64decode(request.form['signature']),
                transaction,
                request.form['pubkey']
            )
            valid_balance = wallet.get_balance(sender)[0] >= (amount + current_balance + pending_balance)

            if not valid_signature:
                return "Invalid signature", 401
            if not valid_balance:
                return "Insufficient funds", 401

            self.current_chain.new_transaction(sender, recipient, amount)
            return "Success", 201

        @self.app.route('/chain', methods=['GET'])
        def full_chain():
            response = {
                'chain': self.current_chain.blockchain,
                'length': len(self.current_chain.blockchain),
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


if __name__ == '__main__':
    node1 = Node(6000, "blockchain1.txt")
    node2 = Node(6001, "blockchain2.txt")

    t1 = threading.Thread(target=node1.run)
    t2 = threading.Thread(target=node2.run)

    t1.start()
    t2.start()
