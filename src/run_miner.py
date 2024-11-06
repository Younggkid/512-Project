import miner


miner = miner.Miner()
print()
try:
    miner.mine()
except Exception as error:
    print(f'Connection error - {error}')
    print()
    print('Please check your internet connection. Is the node online?')