import json

from web3 import Web3

import os

# from solcx import compile_standard and install_solc
from solcx import compile_standard, install_solc

from dotenv import load_dotenv

load_dotenv()

# Read contract file and store it into simple_storage_file
print("Reading smart contract code...")
with open("./SimpleStorage.sol", "r") as file:
    simple_storage_file = file.read()

print("Installing Solidity...")
install_solc("0.6.0")

# Compile simple_storage_file using JSON notation and Solidity standards
print("Compiling smart contract...")
compiled_sol = compile_standard(
    {
        "language": "Solidity",
        "sources": {"SimpleStorage.sol": {"content": simple_storage_file}},
        "settings": {
            "outputSelection": {
                "*": {
                    "*": ["abi", "metadata", "evm.bytecode", "evm.bytecode.sourceMap"]
                }
            }
        },
    },
    solc_version="0.6.0",
)

# Create new file called comipled_code.json containing our compiled contract
with open("compiled_code.json", "w") as file:
    json.dump(compiled_sol, file)

# To deploy the contract, we need to get the bytecode
# REMEMBER: evm stands for Ethereum Virtual Machine
bytecode = compiled_sol["contracts"]["SimpleStorage.sol"]["SimpleStorage"]["evm"][
    "bytecode"
]["object"]

# To deploy the contract, we need to get the abi (Application Binary Interface)
abi = compiled_sol["contracts"]["SimpleStorage.sol"]["SimpleStorage"]["abi"]

# Use HTTP/RPC Provider to connect to Ganache's simulated blockchain
print("Connecting to simulated blockchain...")
w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:8545"))
chain_id = 1337
my_address = "0x90F8bf6A479f320ead074411a4B0e7944Ea8c9C1"

# Always make addresses and private keys into hex values (add 0x at the front)
private_key = os.getenv("PRIVATE_KEY")

# Build contract
print("Building contract...")
SimpleStorage = w3.eth.contract(abi=abi, bytecode=bytecode)

# Get latest transaction count (we need it for the next transaction)
nonce = w3.eth.getTransactionCount(my_address)

# Build contract deploy transaction
transaction = SimpleStorage.constructor().buildTransaction(
    {
        "chainId": chain_id,
        "gasPrice": w3.eth.gas_price,
        "from": my_address,
        "nonce": nonce,
    }
)

# Sign transaction
signed_transaction = w3.eth.account.sign_transaction(
    transaction, private_key=private_key
)

# Send transaction
print("Publishing contract into the blockchain...")
transaction_hash = w3.eth.send_raw_transaction(signed_transaction.rawTransaction)

transaction_receipt = w3.eth.wait_for_transaction_receipt(transaction_hash)

# Working with the contract
# When working with a contract, we always need a
# Contract address
# Contract ABI
simple_storage = w3.eth.contract(address=transaction_receipt.contractAddress, abi=abi)

# Now we can interact with the contract as we previously did on Remix
# There are two ways to interact with a contract:
# Call -> Simulate making the call and getting a return value. Calls do not apply any change to the blockchain, they are the blue functions of Remix. Orange buttons can also be called, but Remix implicitly sets them to Transact actions automatically.
# Transact -> Actually make a state change. You can also transact with a view or a pure function, but it won't make a state change.

# Initial value of favourite number
print("Check initial favourite number:")
print(simple_storage.functions.retrieve().call())

# Calling store will return nothing because there is no return type, and it will not update the state, as we need transact to do that
print("Attempt to call store() without making any state change")
print(simple_storage.functions.store(15).call())

# Transact
# Build transaction first
print("Updating contract: Transact call of store(49)")
store_transaction = simple_storage.functions.store(49).buildTransaction(
    {
        "chainId": chain_id,
        "gasPrice": w3.eth.gas_price,
        "from": my_address,
        "nonce": nonce + 1,
    }
)

# Sign transaction
signed_store_transaction = w3.eth.account.sign_transaction(
    store_transaction, private_key=private_key
)

# Send transaction
store_transaction_hash = w3.eth.send_raw_transaction(
    signed_store_transaction.rawTransaction
)

# Get transaction receipt
store_transaction_receipt = w3.eth.wait_for_transaction_receipt(store_transaction_hash)

print("Updated favourite number!")
print(simple_storage.functions.retrieve().call())
