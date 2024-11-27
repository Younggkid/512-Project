from oauthlib.uri_validate import authority

import miner
import argparse
from os import path
import sys
from miner_researcher import MinerResearcher
from miner_validator import MinerValidator
from authority import MinerAuthority
import threading
from time import sleep

from authority import MinerAuthority
import subprocess
import sys



try:
    with open("miner_address_6000.txt", "r") as address:
        mining_address = address.read()
except FileNotFoundError:
    print("'miner_address.txt' not detected! Run 'run_wallet.py' first!", file=sys.stderr)
    sys.exit(0)


authority_node_url = f"http://127.0.0.1:6000"
research_node_urls = [
        "http://127.0.0.1:6001",
        "http://127.0.0.1:6002",
        "http://127.0.0.1:6003"
    ]

validator_node_urls = [
    "http://127.0.0.1:6004",
    "http://127.0.0.1:6005",
    "http://127.0.0.1:6006"]

with open("output.txt", "w", buffering=1) as f:
    # sys.stdout = f
    t = threading.Thread(target=MinerAuthority(authority_node_url).mine)
    t.start()
    sleep(1)

    for node_url in research_node_urls:
        threading.Thread(target=MinerResearcher(node_url).mine).start()

    for node_url in validator_node_urls:
        threading.Thread(target=MinerValidator(node_url).mine).start()
    t.join()
    # sys.stdout = sys.__stdout__


