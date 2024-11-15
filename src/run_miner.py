import miner
import argparse
from os import path
import sys

parser = argparse.ArgumentParser(description='Run the miner')
parser.add_argument('-p', '--port', type=int, default=6000, help='Port of the node to connect to')
args = parser.parse_args()
node_url = f"http://127.0.0.1:{args.port}"

try:
    with open("miner_address_6000.txt", "r") as address:
        mining_address = address.read()
except FileNotFoundError:
    print("'miner_address.txt' not detected! Run 'run_wallet.py' first!", file=sys.stderr)
    sys.exit(0)

miner = miner.Miner(node_url)
print()
try:
    miner.mine()
except Exception as error:
    print(f'Connection error - {error}')
    print()
    print('Please check your internet connection. Is the node online?')