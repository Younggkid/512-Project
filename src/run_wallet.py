from base64 import b64encode
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
import hashlib

# Functions for key generation and saving
def generate_key(private_key_file):
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend()
    )
    save_key(private_key, private_key_file)

def save_key(private_key, private_key_file):
    pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )
    with open(private_key_file, 'wb') as f:
        f.write(pem)

def main():
    # Generate private keys for ports 6000 to 6010
    for port in range(6000, 6010):
        private_key_file = f"private_key_{port}.pem"
        generate_key(private_key_file)
        print(f"Generated {private_key_file}")

if __name__ == "__main__":
    main()
