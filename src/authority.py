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




class AuthorityAgent:
    def __init__(self):
        self.private_key = wallet.read_key("private_key.pem")
        pass
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

    def verify_block(self, block, public_key, signature):
        try:
            public_key.verify(
                signature,
                block.calculate_hash(),
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            return True
        except InvalidSignature:
            return False