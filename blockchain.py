from web3 import Web3
from eth_account import Account
from config import SEPOLIA_RPC, CONTRACT_ADDRESS, OWNER_PRIVATE_KEY, OWNER_WALLET
import json
import os

# اتصال به شبکه
w3 = Web3(Web3.HTTPProvider(SEPOLIA_RPC))

# ABI رو بعداً از Remix می‌گیریم و اینجا لود می‌کنیم
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
    return w3.eth.contract(address=CONTRACT_ADDRESS, abi=abi)

def create_wallet():
    """ساخت کیف پول جدید برای کاربر"""
    account = Account.create()
    return {
        "address": account.address,
        "private_key": account.key.hex()
    }

def get_balance(address):
    """گرفتن موجودی MPYJ یه آدرس"""
    contract = get_contract()
    if not contract:
        return 0
    try:
        return contract.functions.balanceOf(address).call()
    except Exception as e:
        print(f"Error getting balance: {e}")
        return 0

def send_tokens(from_private_key, to_address, amount):
    """ارسال توکن از یه کیف پول به یه آدرس"""
    contract = get_contract()
    if not contract:
        return None
    
    account = Account.from_key(from_private_key)
    nonce = w3.eth.get_transaction_count(account.address)
    
    tx = contract.functions.transfer(to_address, amount).build_transaction({
        "from": account.address,
        "nonce": nonce,
        "gas": 200000,
        "gasPrice": w3.eth.gas_price,
        "chainId": 11155111  # Sepolia
    })
    
    signed = w3.eth.account.sign_transaction(tx, from_private_key)
    tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
    return tx_hash.hex()