import wallet
from os import path
import argparse

parser = argparse.ArgumentParser(description='Run wallet')
parser.add_argument('-p', '--port', type=int, default=6000, help='Port of the node to connect to')
args = parser.parse_args()


NODE = f"http://127.0.0.1:{args.port}"

private_key_file = f"private_key_{args.port}.pem"
miner_address_file = f"miner_address_{args.port}.txt"

print('Looking for Private Key...')
print()
if path.exists(private_key_file):
    print("Private key detected!")
    print(f'Your Receiving Address: {wallet.get_address(private_key_file)}')

# If private key is not detected
else:
    print("No private key detected, creating private key now...")
    wallet.generate_key(private_key_file)
    print("Private key has been saved as \' private_key.pem \' DO NOT share this key with anyone")

if path.exists(miner_address_file):
    print("Miner address detected!")
else:
    print("No Miner address detected, generating one now...")
    wallet.save_address(private_key_file, miner_address_file)


def command_error():
    print("Command error, listing available commands")
    print()
    print('\t> send <receiver> <amount>')
    print()
    print('\t> balance [optional: address]')
    print()
    print('\t> address')
    print()

print()
print('Wallet initialized!')
print()
while True:
    try:
        command = input('> ').split()
    except IndexError:
        command_error()
    try:
        if command[0].lower() == 'send':
            if len(command) == 3:
                receiver = command[1]
                amount = command[2]
                sent = wallet.send(receiver, amount, wallet.read_key(private_key_file), NODE)
                if sent:
                    print(f"Sent {amount} to {receiver}")
                    print(f"Your current balance is: {wallet.get_balance(NODE, wallet.get_address(private_key_file))[0]} (Pending: {wallet.get_balance(NODE, wallet.get_address(private_key_file))[1]})")
                else:
                    print("Command error, check if you have enough balance. Please refer to the documentation.")
                    print("Link to docs")
            else:
                print("Command Error:")
                print("\tUsage: `send <receiver> <amount>`")
        elif command[0].lower() == 'balance':
            if len(command) == 1:
                print(f"Your current balance is: {wallet.get_balance(NODE, wallet.get_address(private_key_file))[0]} (Pending: {wallet.get_balance(NODE,wallet.get_address(private_key_file))[1]})")
            elif len(command) == 2:
                balance = wallet.get_balance(command[1], NODE)[0]
                if balance:
                    print(f'Balance for input address: {balance}')
                else:
                    print(f'Error: Invalid Address (Does not exist on blockchain)')
        elif command[0].lower() == 'address':
            print(f'Your Receiving Address is: {wallet.get_address(private_key_file)}')
        else:
            command_error()
    except IndexError:
        command_error()
    except Exception:
        print('  - Make sure you are connected to the internet/check your DNS')

