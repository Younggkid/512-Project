import hashlib
import json
from binascii import unhexlify

from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.serialization import load_pem_public_key
from cryptography.exceptions import InvalidSignature
def hash(block) -> str:
    """
    Hashes a block
    :param block: <dict> block (see example-block.py)
    :return: <bytes> hash of block
        - Returns block hash as bytes
    """
    block_encoded = bytes(json.dumps(block, sort_keys=True).encode())  # Sorted to ensure consistent hashes
    return hashlib.sha256(block_encoded).hexdigest()


def valid_proof(block, proof, node=False) -> bool:
    """
    Validates the Proof.
    :param current_hash: <bytes> Previous hash
    :param proof: <int> current proof
    :return: <bool> true the guessed POW meets the POW criteria (Guessed hash < POW requirement), false if not
            Guess hash is represented as a binary string.
            When inverted, the binary hash must have N leading 0s
            https://en.bitcoin.it/wiki/Block_hashing_algorithm
    """

    """Difficulty N increases mining difficulty exponentially (2**N)"""
    N: int = 20  # Difficulty (N >= 1)

    block['proof'] = proof
    guess = block
    # Append proof to end of block hash
    guess_hash = hash(guess)
    bin_guess_hash = f"{bin(int.from_bytes(unhexlify(guess_hash), byteorder='big'))}"[::-1]  # Reverse binary string
    return bin_guess_hash[:N] == "0" * N

def verify_signature(signature, packet, pub_key_serialized):
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