import os
from config import DATABASE_URL, USE_POSTGRES, DB_PATH
from crypto_utils import encrypt, decrypt

# ==================== اتصال ====================
if USE_POSTGRES:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    
    def get_conn():
        return psycopg2.connect(DATABASE_URL, sslmode="require")
    
    PLACEHOLDER = "%s"
else:
    import sqlite3
    os.makedirs("data", exist_ok=True)
    
    def get_conn():
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn
    
    PLACEHOLDER = "?"


# ==================== init ====================
def init_db():
    conn = get_conn()
    c = conn.cursor()
    
    if USE_POSTGRES:
        c.execute("""
            CREATE TABLE IF NOT EXISTS users (
                telegram_id BIGINT PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                wallet_address TEXT,
                encrypted_private_key TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS history (
                id SERIAL PRIMARY KEY,
                from_id BIGINT,
                to_id BIGINT,
                amount BIGINT,
                reason TEXT,
                tx_hash TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS bets (
                id SERIAL PRIMARY KEY,
                title TEXT,
                player1_id BIGINT,
                player2_id BIGINT,
                amount BIGINT,
                winner_id BIGINT,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
    else:
        c.execute("""
            CREATE TABLE IF NOT EXISTS users (
                telegram_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                wallet_address TEXT,
                encrypted_private_key TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                from_id INTEGER,
                to_id INTEGER,
                amount INTEGER,
                reason TEXT,
                tx_hash TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
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
    
    conn.commit()
    c.close()
    conn.close()


# ==================== تبدیل ====================
def _row_to_dict(row):
    """تبدیل Row به dict، چه PostgreSQL چه SQLite"""
    if row is None:
        return None
    if USE_POSTGRES:
        # psycopg2 با RealDictCursor خودش dict برمی‌گردونه
        return dict(row)
    else:
        # sqlite3.Row رو باید به dict تبدیل کنیم
        return dict(row)


# ==================== کاربران ====================
def get_user(telegram_id):
    conn = get_conn()
    if USE_POSTGRES:
        c = conn.cursor(cursor_factory=RealDictCursor)
    else:
        c = conn.cursor()
    c.execute(f"SELECT * FROM users WHERE telegram_id = {PLACEHOLDER}", (telegram_id,))
    row = c.fetchone()
    c.close()
    conn.close()
    return _row_to_dict(row)


def add_user(telegram_id, username, first_name, wallet_address, private_key):
    encrypted_key = encrypt(private_key)
    conn = get_conn()
    c = conn.cursor()
    try:
        c.execute(f"""
            INSERT INTO users (telegram_id, username, first_name, wallet_address, encrypted_private_key)
            VALUES ({PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER})
        """, (telegram_id, username, first_name, wallet_address, encrypted_key))
        conn.commit()
        return True
    except Exception as e:
        print(f"❌ add_user error: {e}")
        conn.rollback()
        return False
    finally:
        c.close()
        conn.close()


def get_user_private_key(telegram_id):
    user = get_user(telegram_id)
    if user and user.get("encrypted_private_key"):
        try:
            return decrypt(user["encrypted_private_key"])
        except Exception as e:
            print(f"❌ Decrypt error: {e}")
            return None
    return None


def get_all_users():
    conn = get_conn()
    if USE_POSTGRES:
        c = conn.cursor(cursor_factory=RealDictCursor)
    else:
        c = conn.cursor()
    c.execute("SELECT telegram_id, username, first_name, wallet_address FROM users")
    rows = c.fetchall()
    c.close()
    conn.close()
    return [_row_to_dict(r) for r in rows]


def get_all_users_except(exclude_id):
    conn = get_conn()
    if USE_POSTGRES:
        c = conn.cursor(cursor_factory=RealDictCursor)
    else:
        c = conn.cursor()
    c.execute(f"""
        SELECT telegram_id, username, first_name, wallet_address
        FROM users WHERE telegram_id != {PLACEHOLDER}
    """, (exclude_id,))
    rows = c.fetchall()
    c.close()
    conn.close()
    return [_row_to_dict(r) for r in rows]


def get_user_by_username(username):
    conn = get_conn()
    if USE_POSTGRES:
        c = conn.cursor(cursor_factory=RealDictCursor)
    else:
        c = conn.cursor()
    c.execute(f"SELECT * FROM users WHERE username = {PLACEHOLDER}", (username,))
    row = c.fetchone()
    c.close()
    conn.close()
    return _row_to_dict(row)


# ==================== تاریخچه ====================
def add_history(from_id, to_id, amount, reason, tx_hash=""):
    conn = get_conn()
    c = conn.cursor()
    c.execute(f"""
        INSERT INTO history (from_id, to_id, amount, reason, tx_hash)
        VALUES ({PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER})
    """, (from_id, to_id, amount, reason, tx_hash))
    conn.commit()
    c.close()
    conn.close()


def get_history(telegram_id, limit=10):
    conn = get_conn()
    if USE_POSTGRES:
        c = conn.cursor(cursor_factory=RealDictCursor)
    else:
        c = conn.cursor()
    c.execute(f"""
        SELECT * FROM history
        WHERE from_id = {PLACEHOLDER} OR to_id = {PLACEHOLDER}
        ORDER BY created_at DESC LIMIT {PLACEHOLDER}
    """, (telegram_id, telegram_id, limit))
    rows = c.fetchall()
    c.close()
    conn.close()
    return [_row_to_dict(r) for r in rows]


# ==================== شرط‌بندی ====================
def create_bet(title, player1_id, player2_id, amount):
    conn = get_conn()
    c = conn.cursor()
    if USE_POSTGRES:
        c.execute("""
            INSERT INTO bets (title, player1_id, player2_id, amount)
            VALUES (%s, %s, %s, %s) RETURNING id
        """, (title, player1_id, player2_id, amount))
        bet_id = c.fetchone()[0]
    else:
        c.execute("""
            INSERT INTO bets (title, player1_id, player2_id, amount)
            VALUES (?, ?, ?, ?)
        """, (title, player1_id, player2_id, amount))
        bet_id = c.lastrowid
    conn.commit()
    c.close()
    conn.close()
    return bet_id