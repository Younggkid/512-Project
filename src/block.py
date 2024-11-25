import hashlib
from enum import Enum
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes, serialization
from typing import List, Dict, Union
class BlockState(Enum):
    SEMI_CONFIRM = "semi-confirm"
    CONFIRM = "confirm"
    MINED = "mined"

class Block:
    def __init__(
        self,
        research_address: str,
        index: int,
        previous_block_id: str,
        task_description: str,
        data_link: str,
        code_link: str,
        constraint: str,
        validator_address: Union[str, None] = None,
        predictions: List[str] = None,
        state: Union[None, BlockState] = None,
        validation_state: Union[None, bool] = None,
        txs_list: List[Dict] = None,
        digital_signature: Union[bytes, None] = None,
    ):
        self.research_address = research_address
        self.validator_address = validator_address
        self.index = index
        self.previous_block_id = previous_block_id
        self.task_description = task_description
        self.data_link = data_link
        self.code_link = code_link
        self.constraint = constraint
        self.predictions = predictions if predictions is not None else []
        self.state = state
        self.validation_state = validation_state
        self.txs_list = txs_list if txs_list is not None else []
        self.digital_signature = digital_signature

    def calculate_hash(self) -> bytes:
        """Generates a hash for the block."""
        block_string = (
            f"{self.research_address}{self.validator_address}{self.index}"
            f"{self.previous_block_id}{self.task_description}{self.data_link}"
            f"{self.code_link}{self.constraint}{self.predictions}{self.state}"
            f"{self.validation_state}{self.txs_list}"
        )
        return hashlib.sha256(block_string.encode()).digest()

    def miner_sign_block(self, private_key) -> None:
        """
        Signs the block with a private key using PSS padding and SHA-256 hashing.
        :param private_key: The private key object for signing.
        """
        block_hash = self.calculate_hash()
        self.digital_signature = private_key.sign(
            block_hash,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )

    def verify_signature(self, public_key) -> bool:
        """
        Verifies the block's digital signature using the corresponding public key.
        :param public_key: The public key object for verification.
        :return: True if the signature is valid, False otherwise.
        """
        try:
            public_key.verify(
                self.digital_signature,
                self.calculate_hash(),
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            return True
        except Exception:
            return False
    
    def to_dict(self) -> Dict[str, Union[str, int, bool, bytes, List[Dict], List[str], None]]:
        """
        Converts the block's attributes to a dictionary.
        :return: A dictionary representation of the block.
        """
        return {
            'research_address': self.research_address,
            'validator_address': self.validator_address,
            'index': self.index,
            'previous_block_id': self.previous_block_id,
            'task_description': self.task_description,
            'data_link': self.data_link,
            'code_link': self.code_link,
            'constraint': self.constraint,
            'predictions': self.predictions,
            'state': self.state,
            'validation_state': self.validation_state,
            'txs_list': self.txs_list,
            'digital_signature': self.digital_signature.hex() if self.digital_signature else None,
        }
