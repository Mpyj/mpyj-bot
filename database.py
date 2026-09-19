import sqlite3
import os
from config import DB_PATH

def init_db():
    """ساخت جدول‌ها اگه وجود نداشته باشن"""
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # جدول کاربران
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            telegram_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            balance INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # جدول شرط‌ها
    c.execute("""
        CREATE TABLE IF NOT EXISTS bets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            player1_id INTEGER,
            player2_id INTEGER,
            amount INTEGER,
            winner_id INTEGER,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # جدول تاریخچه تراکنش‌ها
    c.execute("""
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            from_id INTEGER,
            to_id INTEGER,
            amount INTEGER,
            reason TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    conn.close()

# ========== کاربران ==========
def get_user(telegram_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
    user = c.fetchone()
    conn.close()
    return user

def add_user(telegram_id, username, first_name=""):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute("""
            INSERT INTO users (telegram_id, username, first_name, balance)
            VALUES (?, ?, ?, 0)
        """, (telegram_id, username, first_name))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def get_all_users():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT telegram_id, username, first_name, balance FROM users")
    users = c.fetchall()
    conn.close()
    return users

def get_all_users_except(exclude_id):
    """گرفتن همه کاربران به جز یه نفر"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "SELECT telegram_id, username, first_name, balance FROM users WHERE telegram_id != ?",
        (exclude_id,)
    )
    users = c.fetchall()
    conn.close()
    return users

def get_user_by_username(username):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = c.fetchone()
    conn.close()
    return user

# ========== موجودی ==========
def get_balance(telegram_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT balance FROM users WHERE telegram_id = ?", (telegram_id,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else 0

def update_balance(telegram_id, amount):
    """اضافه یا کم کردن موجودی"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE users SET balance = balance + ? WHERE telegram_id = ?", (amount, telegram_id))
    conn.commit()
    conn.close()

def transfer(from_id, to_id, amount, reason=""):
    """انتقال سکه بین دو کاربر"""
    from_balance = get_balance(from_id)
    if from_balance < amount:
        return False, "موجودی کافی نداری!"
    
    if not get_user(to_id):
        return False, "کاربر مقصد پیدا نشد!"
    
    if amount <= 0:
        return False, "مقدار باید بزرگتر از صفر باشه!"
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE users SET balance = balance - ? WHERE telegram_id = ?", (amount, from_id))
    c.execute("UPDATE users SET balance = balance + ? WHERE telegram_id = ?", (amount, to_id))
    c.execute(
        "INSERT INTO history (from_id, to_id, amount, reason) VALUES (?, ?, ?, ?)",
        (from_id, to_id, amount, reason)
    )
    conn.commit()
    conn.close()
    return True, "موفق!"

def add_history(from_id, to_id, amount, reason):
    """ثبت تراکنش تو تاریخچه"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "INSERT INTO history (from_id, to_id, amount, reason) VALUES (?, ?, ?, ?)",
        (from_id, to_id, amount, reason)
    )
    conn.commit()
    conn.close()

# ========== شرط‌بندی ==========
def create_bet(title, player1_id, player2_id, amount):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        INSERT INTO bets (title, player1_id, player2_id, amount)
        VALUES (?, ?, ?, ?)
    """, (title, player1_id, player2_id, amount))
    bet_id = c.lastrowid
    conn.commit()
    conn.close()
    return bet_id

def get_bet(bet_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM bets WHERE id = ?", (bet_id,))
    bet = c.fetchone()
    conn.close()
    return bet

def get_active_bets():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM bets WHERE status = 'pending'")
    bets = c.fetchall()
    conn.close()
    return bets

def update_bet_status(bet_id, status, winner_id=None):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE bets SET status = ?, winner_id = ? WHERE id = ?", (status, winner_id, bet_id))
    conn.commit()
    conn.close()

# ========== تاریخچه ==========
def get_history(telegram_id, limit=10):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        SELECT * FROM history 
        WHERE from_id = ? OR to_id = ? 
        ORDER BY created_at DESC LIMIT ?
    """, (telegram_id, telegram_id, limit))
    history = c.fetchall()
    conn.close()
    return history