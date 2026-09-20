from cryptography.fernet import Fernet
from config import ENCRYPTION_KEY

if not ENCRYPTION_KEY:
    raise ValueError("❌ ENCRYPTION_KEY تو .env ست نشده!")

fernet = Fernet(ENCRYPTION_KEY.encode())

def encrypt(text: str) -> str:
    return fernet.encrypt(text.encode()).decode()

def decrypt(encrypted_text: str) -> str:
    return fernet.decrypt(encrypted_text.encode()).decode()