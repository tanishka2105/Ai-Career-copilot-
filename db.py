import os
import sqlite3
from contextlib import contextmanager

DB_PATH = os.getenv("DB_PATH", "app.db")
@contextmanager
def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with db() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            salt BLOB NOT NULL,
            password_hash BLOB NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS history(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT,
            score INTEGER,
            result TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS chunks(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            doc_name TEXT,
            text TEXT NOT NULL);
        """)
def create_user(username, salt, password_hash):
    try:
        with db() as c:
            c.execute("INSERT INTO users(username, salt, password_hash) VALUES (?,?,?)",
                      (username, salt, password_hash))
        return True
    except sqlite3.IntegrityError:          # username pehle se hai
        return False


def get_user(username):
    with db() as c:
        return c.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()


def get_user_by_id(user_id):
    with db() as c:
        return c.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
    
#  history save 
def add_history(user_id, title, result_json):
    with db() as c:
        c.execute("INSERT INTO history(user_id, title, result) VALUES (?,?,?)",
                  (user_id, title, result_json))


def get_history(user_id, limit=20):
    with db() as c:
        return c.execute("SELECT * FROM history WHERE user_id=? ORDER BY id DESC LIMIT ?",
                         (user_id, limit)).fetchall()

#  RAG 1 
def add_chunks(user_id, doc_name, chunks):
    with db() as c:
        c.executemany("INSERT INTO chunks(user_id, doc_name, text) VALUES (?,?,?)",
                      [(user_id, doc_name, t) for t in chunks])


def get_chunks(user_id):
    with db() as c:
        rows = c.execute("SELECT text FROM chunks WHERE user_id=?", (user_id,)).fetchall()
    return [r["text"] for r in rows]


def list_docs(user_id):
    with db() as c:
        rows = c.execute("SELECT doc_name, COUNT(*) AS chunks FROM chunks "
                         "WHERE user_id=? GROUP BY doc_name", (user_id,)).fetchall()
    return [dict(r) for r in rows]


def clear_docs(user_id):
    with db() as c:
        c.execute("DELETE FROM chunks WHERE user_id=?", (user_id,))