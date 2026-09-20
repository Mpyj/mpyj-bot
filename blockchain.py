from web3 import Web3
from eth_account import Account
from config import SEPOLIA_RPC, CONTRACT_ADDRESS, OWNER_PRIVATE_KEY, OWNER_WALLET
import json
import os

# اتصال به شبکه
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

def is_member(address):
    """چک کن که آدرس عضو قرارداد هست یا نه"""
    contract = get_contract()
    if not contract:
        return False
    try:
        return contract.functions.isMember(
            Web3.to_checksum_address(address)
        ).call()
    except Exception as e:
        print(f"❌ isMember error: {e}")
        return False

def add_member_on_chain(member_address, starter_coins=0):
    """
    اضافه کردن کاربر به عنوان عضو روی بلاک‌چین
    (قبل از اینکه بتونه توکن بگیره یا بفرسته)
    """
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
        tx_hash_hex = tx_hash.hex()
        print(f"✅ addMember TX: {tx_hash_hex}")
        
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
        if receipt.status != 1:
            return None, "تراکنش addMember fail شد!"
        
        return tx_hash_hex, None
    except Exception as e:
        print(f"❌ addMember ERROR: {type(e).__name__}: {e}")
        return None, f"{type(e).__name__}: {e}"

def send_tokens_from_owner(to_address, amount):
    """
    ارسال توکن از کیف پول Owner به یه آدرس
    """
    contract = get_contract()
    if not contract:
        return None, "قرارداد پیدا نشد!"
    try:
        print(f"🔍 === SEND TOKEN ===")
        print(f"🔍 To: {to_address}")
        print(f"🔍 Amount: {amount}")
        
        account = Account.from_key(OWNER_PRIVATE_KEY)
        print(f"🔍 Owner address: {account.address}")
        
        # چک موجودی ETH
        eth_balance = w3.eth.get_balance(account.address)
        eth_balance_ether = w3.from_wei(eth_balance, "ether")
        print(f"🔍 Owner ETH: {eth_balance_ether}")
        
        # چک موجودی توکن
        token_balance = contract.functions.balanceOf(account.address).call()
        print(f"🔍 Owner MPYJ: {token_balance}")
        
        # ✅ چک کن که گیرنده عضو هست
        member_status = contract.functions.isMember(
            Web3.to_checksum_address(to_address)
        ).call()
        print(f"🔍 Is member: {member_status}")
        
        if not member_status:
            print(f"⚠️ User is not a member, adding...")
            tx_hash, error = add_member_on_chain(to_address, 0)
            if error:
                return None, f"خطا در addMember: {error}"
            print(f"✅ User added as member")
        
        if token_balance < amount:
            return None, f"موجودی توکن Owner کافی نیست! ({token_balance} < {amount})"
        
        if eth_balance_ether < 0.001:
            return None, f"موجودی ETH Owner کافی نیست! ({eth_balance_ether})"
        
        # ساخت تراکنش
        nonce = w3.eth.get_transaction_count(account.address)
        print(f"🔍 Nonce: {nonce}")
        
        # تخمین گس
        try:
            gas_estimate = contract.functions.transfer(
                Web3.to_checksum_address(to_address), amount
            ).estimate_gas({"from": account.address})
            print(f"🔍 Gas estimate: {gas_estimate}")
        except Exception as e:
            print(f"⚠️ Gas estimate failed: {e}")
            gas_estimate = 200000
        
        gas_price = w3.eth.gas_price
        print(f"🔍 Gas price: {gas_price}")
        
        tx = contract.functions.transfer(
            Web3.to_checksum_address(to_address), amount
        ).build_transaction({
            "from": account.address,
            "nonce": nonce,
            "gas": int(gas_estimate * 1.2),
            "gasPrice": gas_price,
            "chainId": 11155111
        })
        print(f"🔍 TX built")
        
        signed = w3.eth.account.sign_transaction(tx, OWNER_PRIVATE_KEY)
        print(f"🔍 Signed")
        
        tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
        tx_hash_hex = tx_hash.hex()
        print(f"✅ TX sent: {tx_hash_hex}")
        
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
        print(f"✅ TX confirmed! Block: {receipt.blockNumber}, Status: {receipt.status}")
        
        if receipt.status != 1:
            return None, "تراکنش fail شد!"
        
        return tx_hash_hex, None
        
    except Exception as e:
        print(f"❌ SEND ERROR: {type(e).__name__}: {e}")
        return None, f"{type(e).__name__}: {e}"

def reward_winner(to_address, amount, reason):
    """جایزه دادن به برنده از طرف Owner"""
    contract = get_contract()
    if not contract:
        return None, "قرارداد پیدا نشد!"
    try:
        print(f"🔍 === REWARD ===")
        print(f"🔍 To: {to_address}, Amount: {amount}, Reason: {reason}")
        
        # چک کن که برنده عضو هست
        member_status = contract.functions.isMember(
            Web3.to_checksum_address(to_address)
        ).call()
        
        if not member_status:
            print(f"⚠️ Winner is not a member, adding...")
            _, error = add_member_on_chain(to_address, 0)
            if error:
                return None, f"خطا در addMember: {error}"
        
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
        tx_hash_hex = tx_hash.hex()
        print(f"✅ Reward TX: {tx_hash_hex}")
        
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
        print(f"✅ Reward confirmed! Status: {receipt.status}")
        
        if receipt.status != 1:
            return None, "تراکنش fail شد!"
        
        return tx_hash_hex, None
    except Exception as e:
        print(f"❌ REWARD ERROR: {type(e).__name__}: {e}")
        return None, f"{type(e).__name__}: {e}"

def get_owner_eth_balance():
    try:
        account = Account.from_key(OWNER_PRIVATE_KEY)
        balance_wei = w3.eth.get_balance(account.address)
        return float(w3.from_wei(balance_wei, "ether"))
    except Exception as e:
        print(f"❌ ETH error: {e}")
        return 0

def get_owner_token_balance():
    contract = get_contract()
    if not contract:
        return 0
    try:
        account = Account.from_key(OWNER_PRIVATE_KEY)
        return contract.functions.balanceOf(account.address).call()
    except Exception as e:
        print(f"❌ Token balance error: {e}")
        return 0