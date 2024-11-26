from oauthlib.uri_validate import authority

import miner
import argparse
from os import path
import sys
from miner_researcher import MinerResearcher
from authority import MinerAuthority
import subprocess

# parser = argparse.ArgumentParser(description='Run the miner')
# parser.add_argument('-p', '--port', type=int, default=6000, help='Port of the node to connect to')
# args = parser.parse_args()
# node_url = f"http://127.0.0.1:{args.port}"
authority_node_url = f"http://127.0.0.1:6000"
research_node_url = f"http://127.0.0.1:6001"

# subprocess.run(["python", "run_wallet.py", "-p 6000"], check=True)
# subprocess.run(["python", "run_wallet.py", "-p 6001"], check=True)
try:
    with open("miner_address_6000.txt", "r") as address:
        mining_address = address.read()
except FileNotFoundError:
    print("'miner_address.txt' not detected! Run 'run_wallet.py' first!", file=sys.stderr)
    sys.exit(0)

research_miner = MinerResearcher(research_node_url)
# miner = miner.Miner(node_url)
print()
try:
    # miner.mine()
    # authority_miner.mine()
    research_miner.mine()
except Exception as error:
    print(f'Connection error - {error}')
    print()
    print('Please check your internet connection. Is the node online?')