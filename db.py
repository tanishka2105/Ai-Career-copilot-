import os

from dotenv import load_dotenv
from sqlalchemy import (Column, DateTime, Integer, LargeBinary, MetaData, String, Table, Text,
                        create_engine, delete, func, insert, select)
from sqlalchemy.exc import IntegrityError

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///app.db")      # .env mein Supabase ka link
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
meta = MetaData()

users = Table("users", meta,
              Column("id", Integer, primary_key=True, autoincrement=True),
              Column("username", String(150), unique=True, nullable=False),
              Column("salt", LargeBinary, nullable=False),
              Column("password_hash", LargeBinary, nullable=False),
              Column("created_at", DateTime, server_default=func.now()))

history = Table("history", meta,
                Column("id", Integer, primary_key=True, autoincrement=True),
                Column("user_id", Integer, nullable=False, index=True),
                Column("title", Text),
                Column("result", Text, nullable=False),
                Column("created_at", DateTime, server_default=func.now()))

chunks = Table("chunks", meta,
               Column("id", Integer, primary_key=True, autoincrement=True),
               Column("user_id", Integer, nullable=False, index=True),
               Column("doc_name", Text),
               Column("text", Text, nullable=False))

sessions = Table("chat_sessions", meta,
                 Column("id", Integer, primary_key=True, autoincrement=True),
                 Column("user_id", Integer, nullable=False, index=True),
                 Column("title", Text),
                 Column("created_at", DateTime, server_default=func.now()))

messages = Table("messages", meta,
                 Column("id", Integer, primary_key=True, autoincrement=True),
                 Column("session_id", Integer, nullable=False, index=True),
                 Column("role", String(20), nullable=False),
                 Column("content", Text, nullable=False),
                 Column("created_at", DateTime, server_default=func.now()))


def init_db():
    meta.create_all(engine)                  # tables sirf tab banti hain jab pehle se na hon
    name = engine.url.get_backend_name()
    print(f"[db] {name} @ {engine.url.host or 'local file'}")
    if name == "sqlite":
        print("[db] WARNING: DATABASE_URL nahi mila, local SQLite chal rahi hai. Supabase use nahi ho raha.")


def _user(row):
    if row is None:
        return None
    d = dict(row._mapping)
    d["salt"], d["password_hash"] = bytes(d["salt"]), bytes(d["password_hash"])
    return d


def create_user(username, salt, password_hash):
    try:
        with engine.begin() as c:
            c.execute(insert(users).values(username=username, salt=salt, password_hash=password_hash))
        return True
    except IntegrityError:                   # username pehle se hai
        return False


def get_user(username):
    with engine.connect() as c:
        return _user(c.execute(select(users).where(users.c.username == username)).fetchone())


def get_user_by_id(user_id):
    with engine.connect() as c:
        return _user(c.execute(select(users).where(users.c.id == user_id)).fetchone())


def add_history(user_id, title, result_json):
    with engine.begin() as c:
        c.execute(insert(history).values(user_id=user_id, title=title, result=result_json))


def get_history(user_id, limit=20):
    q = select(history).where(history.c.user_id == user_id).order_by(history.c.id.desc()).limit(limit)
    with engine.connect() as c:
        rows = [dict(r._mapping) for r in c.execute(q)]
    for r in rows:
        r["ts"] = r["created_at"].isoformat() if r["created_at"] else ""
        r["created_at"] = r["created_at"].strftime("%Y-%m-%d %H:%M") if r["created_at"] else ""
    return rows


def add_chunks(user_id, doc_name, texts):
    with engine.begin() as c:
        c.execute(insert(chunks), [{"user_id": user_id, "doc_name": doc_name, "text": t} for t in texts])


def get_chunks(user_id):
    with engine.connect() as c:
        return [r[0] for r in c.execute(select(chunks.c.text).where(chunks.c.user_id == user_id))]


def list_docs(user_id):
    q = (select(chunks.c.doc_name, func.count().label("chunks"))
         .where(chunks.c.user_id == user_id).group_by(chunks.c.doc_name))
    with engine.connect() as c:
        return [dict(r._mapping) for r in c.execute(q)]


def clear_docs(user_id):
    with engine.begin() as c:
        c.execute(delete(chunks).where(chunks.c.user_id == user_id))


# ---- chat sessions (sidebar history) ----
def create_session(user_id, title):
    with engine.begin() as c:
        res = c.execute(insert(sessions).values(user_id=user_id, title=title))
        return res.inserted_primary_key[0]


def session_owned(session_id, user_id):
    with engine.connect() as c:
        row = c.execute(select(sessions.c.id).where(sessions.c.id == session_id,
                                                    sessions.c.user_id == user_id)).fetchone()
    return row is not None


def add_message(session_id, role, content):
    with engine.begin() as c:
        c.execute(insert(messages).values(session_id=session_id, role=role, content=content))


def get_messages(session_id):
    with engine.connect() as c:
        rows = c.execute(select(messages.c.role, messages.c.content)
                         .where(messages.c.session_id == session_id).order_by(messages.c.id)).fetchall()
    return [{"role": r[0], "content": r[1]} for r in rows]


def list_sessions(user_id, limit=50):
    q = select(sessions).where(sessions.c.user_id == user_id).order_by(sessions.c.id.desc()).limit(limit)
    with engine.connect() as c:
        rows = [dict(r._mapping) for r in c.execute(q)]
    for r in rows:
        r["ts"] = r["created_at"].isoformat() if r["created_at"] else ""
        r["created_at"] = r["created_at"].strftime("%Y-%m-%d %H:%M") if r["created_at"] else ""
    return rows
