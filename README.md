# 512-Project
Source code for Compsci512 course project

## Proof of work

**Built With**

- [Python 3.9](https://www.python.org/)
- [Flask 2.0.3](https://pypi.org/project/Flask/)
- [Cryptography 3.4.7](https://pypi.org/project/cryptography/)

install all the requirements：
`pip3 install -r requirements.txt`

First, start node server:

`python3 node.py`

It should have two nodes running on different port based on Flask framework.

then create a local wallet and generate private key:

`python3 run_wallet.py -p [port]` 

and start mining at some ports.

`python3 run_miner.py -p [port]`

Note the port should be the same for the same node, miner, and wallet.

Use the command line tool created by `run_wallet.py` to send money
