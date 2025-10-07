import sqlite3
from pathlib import Path
from datetime import datetime
import threading
from config import DB_PATH

_lock = threading.Lock()
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

def _get_conn():
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with _lock:
        conn = _get_conn()
        cur = conn.cursor()
        cur.execute('''
        CREATE TABLE IF NOT EXISTS users(
            tg_id INTEGER PRIMARY KEY,
            phone TEXT,
            verified INTEGER DEFAULT 0,
            created_at TEXT
        )
        ''')
        cur.execute('''
        CREATE TABLE IF NOT EXISTS otps(
            tg_id INTEGER PRIMARY KEY,
            otp_hash TEXT,
            expires_at INTEGER,
            attempts INTEGER DEFAULT 0,
            last_sent INTEGER
        )
        ''')
        conn.commit()
        conn.close()

# initialize
init_db()

# users
def upsert_user(tg_id, phone=None, verified=False):
    with _lock:
        conn = _get_conn(); cur = conn.cursor()
        now = datetime.utcnow().isoformat()
        cur.execute('SELECT tg_id FROM users WHERE tg_id=?', (tg_id,))
        if cur.fetchone():
            cur.execute('UPDATE users SET phone=?, verified=? WHERE tg_id=?', (phone, int(verified), tg_id))
        else:
            cur.execute('INSERT INTO users(tg_id, phone, verified, created_at) VALUES(?,?,?,?)', (tg_id, phone, int(verified), now))
        conn.commit(); conn.close()

def get_user(tg_id):
    conn = _get_conn(); cur = conn.cursor()
    cur.execute('SELECT * FROM users WHERE tg_id=?', (tg_id,))
    row = cur.fetchone(); conn.close()
    return dict(row) if row else None

# otp
def set_otp(tg_id, otp_hash, expires_at, last_sent_ts):
    with _lock:
        conn = _get_conn(); cur = conn.cursor()
        cur.execute('REPLACE INTO otps(tg_id, otp_hash, expires_at, attempts, last_sent) VALUES(?,?,?,?,?)', (tg_id, otp_hash, expires_at, 0, last_sent_ts))
        conn.commit(); conn.close()

def get_otp_record(tg_id):
    conn = _get_conn(); cur = conn.cursor()
    cur.execute('SELECT * FROM otps WHERE tg_id=?', (tg_id,))
    r = cur.fetchone(); conn.close()
    return dict(r) if r else None

def inc_otp_attempts(tg_id):
    with _lock:
        conn = _get_conn(); cur = conn.cursor()
        cur.execute('UPDATE otps SET attempts = attempts + 1 WHERE tg_id=?', (tg_id,))
        conn.commit(); conn.close()

def clear_otp(tg_id):
    with _lock:
        conn = _get_conn(); cur = conn.cursor()
        cur.execute('DELETE FROM otps WHERE tg_id=?', (tg_id,))
        conn.commit(); conn.close()
