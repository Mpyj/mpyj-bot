import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OWNER_TELEGRAM_ID = int(os.getenv("OWNER_TELEGRAM_ID", "0"))
OWNER_WALLET = os.getenv("OWNER_WALLET", "")
OWNER_PRIVATE_KEY = os.getenv("OWNER_PRIVATE_KEY", "")
CONTRACT_ADDRESS = os.getenv("CONTRACT_ADDRESS", "")
SEPOLIA_RPC = os.getenv("SEPOLIA_RPC", "https://rpc.sepolia.org")

# مسیر دیتابیس
DB_PATH = "data/mpyj.db"