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