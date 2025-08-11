# database.py
import sqlite3
from config import DB_PATH
import os

os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
conn = sqlite3.connect(DB_PATH, check_same_thread=False)
cur = conn.cursor()

def init_db():
    cur.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        balance REAL DEFAULT 0,
        banned INTEGER DEFAULT 0,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )''')
    cur.execute('''CREATE TABLE IF NOT EXISTS buttons (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        parent_id INTEGER DEFAULT 0,
        title TEXT,
        kind TEXT DEFAULT 'menu',
        content_text TEXT,
        content_photo TEXT
    )''')
    cur.execute('''CREATE TABLE IF NOT EXISTS kb_buttons (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        button_id INTEGER,
        text TEXT,
        ask_info TEXT DEFAULT NULL
    )''')
    cur.execute('''CREATE TABLE IF NOT EXISTS templates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        content TEXT
    )''')
    cur.execute('''CREATE TABLE IF NOT EXISTS requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        button_id INTEGER,
        info_key TEXT,
        info_text TEXT,
        status TEXT DEFAULT 'new',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )''')
    cur.execute('''CREATE TABLE IF NOT EXISTS logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        kind TEXT,
        detail TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )''')
    conn.commit()

# Users
def ensure_user(uid: int):
    cur.execute("INSERT OR IGNORE INTO users (id) VALUES (?)", (uid,))
    conn.commit()

def get_balance(uid: int) -> float:
    ensure_user(uid)
    cur.execute("SELECT balance FROM users WHERE id=?", (uid,))
    r = cur.fetchone()
    return float(r[0]) if r and r[0] is not None else 0.0

def add_balance(uid:int, amount:float):
    ensure_user(uid)
    cur.execute("UPDATE users SET balance = balance + ? WHERE id=?", (amount, uid))
    conn.commit()
    log("balance", f"add {amount} to {uid}")

def set_balance(uid:int, amount:float):
    ensure_user(uid)
    cur.execute("UPDATE users SET balance = ? WHERE id=?", (amount, uid))
    conn.commit()
    log("balance", f"set {uid} -> {amount}")

def is_banned(uid:int) -> bool:
    cur.execute("SELECT banned FROM users WHERE id=?", (uid,))
    r = cur.fetchone()
    return bool(r and r[0]==1)

def set_ban(uid:int, val:int):
    ensure_user(uid)
    cur.execute("UPDATE users SET banned=? WHERE id=?", (val, uid))
    conn.commit()
    log("ban", f"{'ban' if val==1 else 'unban'} {uid}")

def get_all_user_ids():
    cur.execute("SELECT id FROM users")
    return [r[0] for r in cur.fetchall()]

# Buttons / content
def create_button(title:str, parent_id:int=0, kind:str='menu', content_text:str='', content_photo:str=''):
    cur.execute("INSERT INTO buttons (parent_id, title, kind, content_text, content_photo) VALUES (?,?,?,?,?)",
                (parent_id, title, kind, content_text, content_photo))
    conn.commit()
    return cur.lastrowid

def update_button(bid:int, title=None, content_text=None, content_photo=None):
    if title is not None:
        cur.execute("UPDATE buttons SET title=? WHERE id=?", (title,bid))
    if content_text is not None:
        cur.execute("UPDATE buttons SET content_text=? WHERE id=?", (content_text,bid))
    if content_photo is not None:
        cur.execute("UPDATE buttons SET content_photo=? WHERE id=?", (content_photo,bid))
    conn.commit()
    log("button_update", f"id={bid} title={title}")

def delete_button(bid:int):
    cur.execute("DELETE FROM buttons WHERE id=?", (bid,))
    cur.execute("DELETE FROM kb_buttons WHERE button_id=?", (bid,))
    conn.commit()
    log("button_delete", f"id={bid}")

def list_children(parent_id:int=0):
    cur.execute("SELECT id, title, kind FROM buttons WHERE parent_id=? ORDER BY id", (parent_id,))
    return cur.fetchall()

def get_button(bid:int):
    cur.execute("SELECT id,parent_id,title,kind,content_text,content_photo FROM buttons WHERE id=?", (bid,))
    return cur.fetchone()

# keyboard buttons (under a content)
def add_kb(button_id:int, text:str, ask_info:str=None):
    cur.execute("INSERT INTO kb_buttons (button_id,text,ask_info) VALUES (?,?,?)", (button_id, text, ask_info))
    conn.commit()
    return cur.lastrowid

def get_kb_for(button_id:int):
    cur.execute("SELECT id,text,ask_info FROM kb_buttons WHERE button_id=?", (button_id,))
    return cur.fetchall()

# templates
def add_template(name, content):
    cur.execute("INSERT INTO templates (name,content) VALUES (?,?)", (name, content))
    conn.commit()
    log("template", f"add {name}")

def list_templates():
    cur.execute("SELECT id,name,content FROM templates")
    return cur.fetchall()

def del_template(tid:int):
    cur.execute("DELETE FROM templates WHERE id=?", (tid,))
    conn.commit()
    log("template", f"del {tid}")

# requests
def create_request(user_id, button_id, info_key, info_text):
    cur.execute("INSERT INTO requests (user_id,button_id,info_key,info_text) VALUES (?,?,?,?)",
                (user_id,button_id,info_key,info_text))
    conn.commit()
    rid = cur.lastrowid
    log("request", f"create {rid} user={user_id} btn={button_id}")
    return rid

def list_requests(status=None):
    if status:
        cur.execute("SELECT id,user_id,button_id,info_key,info_text,status,created_at FROM requests WHERE status=?", (status,))
    else:
        cur.execute("SELECT id,user_id,button_id,info_key,info_text,status,created_at FROM requests")
    return cur.fetchall()

def set_request_status(rid:int, status:str):
    cur.execute("UPDATE requests SET status=? WHERE id=?", (status, rid))
    conn.commit()
    log("request", f"req {rid} -> {status}")

# logs
def log(kind, detail):
    cur.execute("INSERT INTO logs (kind, detail) VALUES (?,?)", (kind, detail))
    conn.commit()

def recent_logs(limit=20):
    cur.execute("SELECT id,kind,detail,created_at FROM logs ORDER BY id DESC LIMIT ?", (limit,))
    return cur.fetchall()

# initialize DB
init_db()
