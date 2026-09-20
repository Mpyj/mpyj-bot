from web3 import Web3
from eth_account import Account
from config import SEPOLIA_RPC, CONTRACT_ADDRESS, OWNER_PRIVATE_KEY
import json
import os

w3 = Web3(Web3.HTTPProvider(SEPOLIA_RPC))
ABI_PATH = "contracts/abi.json"

def load_abi():
    if os.path.exists(ABI_PATH):
        with open(ABI_PATH, "r") as f:
            return json.load(f)
    return None

def get_contract():
    abi = load_abi()
    if not abi or not CONTRACT_ADDRESS:
        return None
    try:
        return w3.eth.contract(
            address=Web3.to_checksum_address(CONTRACT_ADDRESS),
            abi=abi
        )
    except Exception as e:
        print(f"❌ Contract error: {e}")
        return None

def create_wallet():
    account = Account.create()
    return {"address": account.address, "private_key": account.key.hex()}

def get_balance(address):
    contract = get_contract()
    if not contract:
        return 0
    try:
        return contract.functions.balanceOf(
            Web3.to_checksum_address(address)
        ).call()
    except Exception as e:
        print(f"❌ Balance error: {e}")
        return 0

def send_tokens_from_owner(to_address, amount):
    contract = get_contract()
    if not contract:
        return None, "قرارداد پیدا نشد!"
    try:
        account = Account.from_key(OWNER_PRIVATE_KEY)
        nonce = w3.eth.get_transaction_count(account.address)
        tx = contract.functions.transfer(
            Web3.to_checksum_address(to_address), amount
        ).build_transaction({
            "from": account.address,
            "nonce": nonce,
            "gas": 200000,
            "gasPrice": w3.eth.gas_price,
            "chainId": 11155111
        })
        signed = w3.eth.account.sign_transaction(tx, OWNER_PRIVATE_KEY)
        tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
        return tx_hash.hex(), None
    except Exception as e:
        return None, str(e)

def reward_winner(to_address, amount, reason):
    """جایزه دادن به برنده از طرف Owner"""
    contract = get_contract()
    if not contract:
        return None, "قرارداد پیدا نشد!"
    try:
        account = Account.from_key(OWNER_PRIVATE_KEY)
        nonce = w3.eth.get_transaction_count(account.address)
        tx = contract.functions.rewardWinner(
            Web3.to_checksum_address(to_address), amount, reason
        ).build_transaction({
            "from": account.address,
            "nonce": nonce,
            "gas": 300000,
            "gasPrice": w3.eth.gas_price,
            "chainId": 11155111
        })
        signed = w3.eth.account.sign_transaction(tx, OWNER_PRIVATE_KEY)
        tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
        return tx_hash.hex(), None
    except Exception as e:
        return None, str(e)

def add_member_on_chain(member_address, starter_coins):
    """اضافه کردن عضو روی بلاک‌چین"""
    contract = get_contract()
    if not contract:
        return None, "قرارداد پیدا نشد!"
    try:
        account = Account.from_key(OWNER_PRIVATE_KEY)
        nonce = w3.eth.get_transaction_count(account.address)
        tx = contract.functions.addMember(
            Web3.to_checksum_address(member_address), starter_coins
        ).build_transaction({
            "from": account.address,
            "nonce": nonce,
            "gas": 200000,
            "gasPrice": w3.eth.gas_price,
            "chainId": 11155111
        })
        signed = w3.eth.account.sign_transaction(tx, OWNER_PRIVATE_KEY)
        tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
        return tx_hash.hex(), None
    except Exception as e:
        return None, str(e)

def get_owner_eth_balance():
    try:
        account = Account.from_key(OWNER_PRIVATE_KEY)
        balance_wei = w3.eth.get_balance(account.address)
        return float(w3.from_wei(balance_wei, "ether"))
    except Exception as e:
        print(f"❌ ETH error: {e}")
        return 0