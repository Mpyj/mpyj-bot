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
                last_captcha TIMESTAMP,
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
        c.execute("""
            CREATE TABLE IF NOT EXISTS pending_rewards (
                id SERIAL PRIMARY KEY,
                user_id BIGINT,
                amount BIGINT,
                reason TEXT,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS daily_quests (
                id SERIAL PRIMARY KEY,
                user_id BIGINT,
                quest_type TEXT,
                completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS lottery_tickets (
                id SERIAL PRIMARY KEY,
                user_id BIGINT,
                ticket_number INTEGER,
                week_number INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS dice_games (
                id SERIAL PRIMARY KEY,
                creator_id BIGINT,
                status TEXT DEFAULT 'waiting',
                winner_id BIGINT,
                dice_value INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS dice_players (
                id SERIAL PRIMARY KEY,
                game_id INTEGER,
                user_id BIGINT,
                bet_amount BIGINT DEFAULT 0,
                dice_value INTEGER,
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
                last_captcha TIMESTAMP,
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
        c.execute("""
            CREATE TABLE IF NOT EXISTS pending_rewards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                amount INTEGER,
                reason TEXT,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS daily_quests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                quest_type TEXT,
                completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS lottery_tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                ticket_number INTEGER,
                week_number INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS dice_games (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                creator_id INTEGER,
                status TEXT DEFAULT 'waiting',
                winner_id INTEGER,
                dice_value INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS dice_players (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                game_id INTEGER,
                user_id INTEGER,
                bet_amount INTEGER DEFAULT 0,
                dice_value INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
    
    conn.commit()
    c.close()
    conn.close()


# ==================== تبدیل ====================
def _row_to_dict(row):
    if row is None:
        return None
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


# ==================== کپچا ====================
def update_last_captcha(telegram_id):
    """ذخیره زمان آخرین کپچا"""
    conn = get_conn()
    c = conn.cursor()
    if USE_POSTGRES:
        c.execute(f"""
            UPDATE users SET last_captcha = CURRENT_TIMESTAMP
            WHERE telegram_id = {PLACEHOLDER}
        """, (telegram_id,))
    else:
        c.execute(f"""
            UPDATE users SET last_captcha = datetime('now')
            WHERE telegram_id = {PLACEHOLDER}
        """, (telegram_id,))
    conn.commit()
    c.close()
    conn.close()


def needs_captcha(telegram_id):
    """چک کن کاربر نیاز به کپچا داره یا نه (۲۴ ساعت)"""
    conn = get_conn()
    if USE_POSTGRES:
        c = conn.cursor(cursor_factory=RealDictCursor)
        c.execute(f"""
            SELECT last_captcha FROM users
            WHERE telegram_id = {PLACEHOLDER}
        """, (telegram_id,))
    else:
        c = conn.cursor()
        c.execute(f"""
            SELECT last_captcha FROM users
            WHERE telegram_id = {PLACEHOLDER}
        """, (telegram_id,))
    row = c.fetchone()
    c.close()
    conn.close()
    
    if not row:
        return True  # کاربر وجود نداره
    
    last = row["last_captcha"] if USE_POSTGRES else row[0]
    
    if last is None:
        return True  # هیچ‌وقت کپچا نداده
    
    # چک کن ۲۴ ساعت گذشته یا نه
    import datetime
    if isinstance(last, str):
        try:
            last = datetime.datetime.fromisoformat(last.replace("Z", "+00:00"))
        except:
            return True
    
    try:
        diff = datetime.datetime.now() - last.replace(tzinfo=None) if hasattr(last, 'replace') else datetime.datetime.now() - last
    except:
        return True
    
    return diff.total_seconds() > 86400  # ۲۴ ساعت


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


def get_bet(bet_id):
    conn = get_conn()
    if USE_POSTGRES:
        c = conn.cursor(cursor_factory=RealDictCursor)
    else:
        c = conn.cursor()
    c.execute(f"SELECT * FROM bets WHERE id = {PLACEHOLDER}", (bet_id,))
    row = c.fetchone()
    c.close()
    conn.close()
    return _row_to_dict(row)


def get_pending_bets():
    conn = get_conn()
    if USE_POSTGRES:
        c = conn.cursor(cursor_factory=RealDictCursor)
    else:
        c = conn.cursor()
    c.execute("SELECT * FROM bets WHERE status = 'pending' ORDER BY created_at DESC")
    rows = c.fetchall()
    c.close()
    conn.close()
    return [_row_to_dict(r) for r in rows]


def update_bet_status(bet_id, status, winner_id=None):
    conn = get_conn()
    c = conn.cursor()
    c.execute(f"""
        UPDATE bets SET status = {PLACEHOLDER}, winner_id = {PLACEHOLDER}
        WHERE id = {PLACEHOLDER}
    """, (status, winner_id, bet_id))
    conn.commit()
    c.close()
    conn.close()


# ==================== جوایز در انتظار ====================
def create_pending_reward(user_id, amount, reason):
    conn = get_conn()
    c = conn.cursor()
    if USE_POSTGRES:
        c.execute("""
            INSERT INTO pending_rewards (user_id, amount, reason)
            VALUES (%s, %s, %s) RETURNING id
        """, (user_id, amount, reason))
        reward_id = c.fetchone()[0]
    else:
        c.execute("""
            INSERT INTO pending_rewards (user_id, amount, reason)
            VALUES (?, ?, ?)
        """, (user_id, amount, reason))
        reward_id = c.lastrowid
    conn.commit()
    c.close()
    conn.close()
    return reward_id


def get_pending_reward(reward_id):
    conn = get_conn()
    if USE_POSTGRES:
        c = conn.cursor(cursor_factory=RealDictCursor)
    else:
        c = conn.cursor()
    c.execute(f"SELECT * FROM pending_rewards WHERE id = {PLACEHOLDER}", (reward_id,))
    row = c.fetchone()
    c.close()
    conn.close()
    return _row_to_dict(row)


def update_pending_reward_status(reward_id, status):
    conn = get_conn()
    c = conn.cursor()
    c.execute(f"""
        UPDATE pending_rewards SET status = {PLACEHOLDER} WHERE id = {PLACEHOLDER}
    """, (status, reward_id))
    conn.commit()
    c.close()
    conn.close()


def get_all_pending_rewards():
    conn = get_conn()
    if USE_POSTGRES:
        c = conn.cursor(cursor_factory=RealDictCursor)
    else:
        c = conn.cursor()
    c.execute("SELECT * FROM pending_rewards WHERE status = 'pending' ORDER BY created_at DESC")
    rows = c.fetchall()
    c.close()
    conn.close()
    return [_row_to_dict(r) for r in rows]


# ==================== ماموریت‌ها ====================
def has_done_quest_today(user_id, quest_type):
    conn = get_conn()
    if USE_POSTGRES:
        c = conn.cursor(cursor_factory=RealDictCursor)
        c.execute(f"""
            SELECT * FROM daily_quests 
            WHERE user_id = {PLACEHOLDER} AND quest_type = {PLACEHOLDER}
            AND DATE(completed_at) = CURRENT_DATE
        """, (user_id, quest_type))
    else:
        c = conn.cursor()
        c.execute(f"""
            SELECT * FROM daily_quests 
            WHERE user_id = {PLACEHOLDER} AND quest_type = {PLACEHOLDER}
            AND DATE(completed_at) = DATE('now')
        """, (user_id, quest_type))
    row = c.fetchone()
    c.close()
    conn.close()
    return row is not None


def add_quest_completion(user_id, quest_type):
    conn = get_conn()
    c = conn.cursor()
    c.execute(f"""
        INSERT INTO daily_quests (user_id, quest_type)
        VALUES ({PLACEHOLDER}, {PLACEHOLDER})
    """, (user_id, quest_type))
    conn.commit()
    c.close()
    conn.close()


# ==================== لاتاری ====================
def get_week_number():
    import datetime
    return datetime.date.today().isocalendar()[1]


def buy_lottery_ticket(user_id):
    week = get_week_number()
    conn = get_conn()
    c = conn.cursor()
    
    c.execute(f"""
        SELECT * FROM lottery_tickets 
        WHERE user_id = {PLACEHOLDER} AND week_number = {PLACEHOLDER}
    """, (user_id, week))
    
    if c.fetchone():
        c.close()
        conn.close()
        return None, "تو این هفته قبلاً بلیط خریدی!"
    
    import random
    ticket_number = random.randint(1000, 9999)
    
    c.execute(f"""
        INSERT INTO lottery_tickets (user_id, ticket_number, week_number)
        VALUES ({PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER})
    """, (user_id, ticket_number, week))
    conn.commit()
    c.close()
    conn.close()
    return ticket_number, None


def get_lottery_participants():
    week = get_week_number()
    conn = get_conn()
    if USE_POSTGRES:
        c = conn.cursor(cursor_factory=RealDictCursor)
    else:
        c = conn.cursor()
    c.execute(f"""
        SELECT * FROM lottery_tickets WHERE week_number = {PLACEHOLDER}
    """, (week,))
    rows = c.fetchall()
    c.close()
    conn.close()
    return [_row_to_dict(r) for r in rows]


# ==================== تاس ====================
def create_dice_game(creator_id):
    conn = get_conn()
    c = conn.cursor()
    if USE_POSTGRES:
        c.execute("INSERT INTO dice_games (creator_id) VALUES (%s) RETURNING id", (creator_id,))
        game_id = c.fetchone()[0]
    else:
        c.execute("INSERT INTO dice_games (creator_id) VALUES (?)", (creator_id,))
        game_id = c.lastrowid
    conn.commit()
    c.close()
    conn.close()
    return game_id


def get_dice_game(game_id):
    conn = get_conn()
    if USE_POSTGRES:
        c = conn.cursor(cursor_factory=RealDictCursor)
    else:
        c = conn.cursor()
    c.execute(f"SELECT * FROM dice_games WHERE id = {PLACEHOLDER}", (game_id,))
    row = c.fetchone()
    c.close()
    conn.close()
    return _row_to_dict(row)


def add_dice_player(game_id, user_id, bet_amount=0):
    conn = get_conn()
    c = conn.cursor()
    try:
        c.execute(f"""
            INSERT INTO dice_players (game_id, user_id, bet_amount)
            VALUES ({PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER})
        """, (game_id, user_id, bet_amount))
        conn.commit()
        return True
    except Exception as e:
        print(f"❌ add_dice_player: {e}")
        conn.rollback()
        return False
    finally:
        c.close()
        conn.close()


def get_dice_players(game_id):
    conn = get_conn()
    if USE_POSTGRES:
        c = conn.cursor(cursor_factory=RealDictCursor)
    else:
        c = conn.cursor()
    c.execute(f"SELECT * FROM dice_players WHERE game_id = {PLACEHOLDER}", (game_id,))
    rows = c.fetchall()
    c.close()
    conn.close()
    return [_row_to_dict(r) for r in rows]


def update_dice_value(game_id, user_id, dice_value):
    conn = get_conn()
    c = conn.cursor()
    c.execute(f"""
        UPDATE dice_players SET dice_value = {PLACEHOLDER}
        WHERE game_id = {PLACEHOLDER} AND user_id = {PLACEHOLDER}
    """, (dice_value, game_id, user_id))
    conn.commit()
    c.close()
    conn.close()


def update_dice_bet(game_id, user_id, bet_amount):
    conn = get_conn()
    c = conn.cursor()
    c.execute(f"""
        UPDATE dice_players SET bet_amount = {PLACEHOLDER}
        WHERE game_id = {PLACEHOLDER} AND user_id = {PLACEHOLDER}
    """, (bet_amount, game_id, user_id))
    conn.commit()
    c.close()
    conn.close()


def update_dice_game_status(game_id, status, winner_id=None, dice_value=None):
    conn = get_conn()
    c = conn.cursor()
    c.execute(f"""
        UPDATE dice_games SET status = {PLACEHOLDER}, winner_id = {PLACEHOLDER}, dice_value = {PLACEHOLDER}
        WHERE id = {PLACEHOLDER}
    """, (status, winner_id, dice_value, game_id))
    conn.commit()
    c.close()
    conn.close()