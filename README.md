# 512-Project
Source code for Compsci512 course project

## Set-Up

**Built With**

- [Python 3.9](https://www.python.org/)
- [Flask 2.0.3](https://pypi.org/project/Flask/)
- [Cryptography 3.4.7](https://pypi.org/project/cryptography/)

install all the requirements：
```shell
pip3 install -r requirements.txt
cd src
````

## Initialization
First, initial the private keys and addresses for different nodes by running:

```shell
python3 run_wallet.py
```

## Node server
Then, start node server:

```shell
python3 node.py
```
It should have seven nodes running on different port based on Flask framework. One node is the authority node, and three are research nodes, and the other three are the validation nodes.


## Mining
Finally, start mining at some ports, including one authority miner, three research miners, and three validation miners:

```shell
python3 run_miner.py
```

Note the port should be the same for the same node, miner, and wallet.

Results will be output in the `output.txt` file.

