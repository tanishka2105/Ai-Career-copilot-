import json
import os

from dotenv import load_dotenv
from sqlalchemy import (Column, DateTime, Float, Integer, LargeBinary, MetaData, String, Table, Text, inspect,
                        create_engine, delete, func, insert, select, update)
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

scorecards = Table("interview_scorecards", meta,
                   Column("id", Integer, primary_key=True, autoincrement=True),
                   Column("user_id", Integer, nullable=False, index=True),
                   Column("session_id", Integer, nullable=False, index=True),
                   Column("average", Float, nullable=False),
                   Column("count", Integer, nullable=False),
                   Column("result", Text, nullable=False),
                   Column("created_at", DateTime, server_default=func.now()))

career_intakes = Table("career_intakes", meta,
                       Column("id", Integer, primary_key=True, autoincrement=True),
                       Column("user_id", Integer, nullable=False, index=True),
                       Column("target_role", String(200)),
                       Column("experience", String(50)),
                       Column("timeline", String(50)),
                       Column("resume_title", String(200)),
                       Column("resume_text", Text, nullable=False),
                       Column("jd_text", Text, nullable=False),
                       Column("jd_url", Text),
                       Column("result", Text, nullable=False),
                       Column("created_at", DateTime, server_default=func.now()))

roadmaps = Table("roadmaps", meta,
                 Column("id", Integer, primary_key=True, autoincrement=True),
                 Column("user_id", Integer, nullable=False, index=True),
                 Column("target_role", String(200), nullable=False),
                 Column("weeks", Integer, nullable=False),
                 Column("result", Text, nullable=False),
                 Column("created_at", DateTime, server_default=func.now()))

portfolio_projects = Table("portfolio_projects", meta,
                           Column("id", Integer, primary_key=True, autoincrement=True),
                           Column("user_id", Integer, nullable=False, index=True),
                           Column("target_role", String(200), nullable=False),
                           Column("result", Text, nullable=False),
                           Column("created_at", DateTime, server_default=func.now()))

skill_progress = Table("skill_progress", meta,
                       Column("user_id", Integer, primary_key=True),
                       Column("skill", String(80), primary_key=True),
                       Column("mastery", String(20), nullable=False),
                       Column("updated_at", DateTime, server_default=func.now()))


def init_db():
    meta.create_all(engine)                  # tables sirf tab banti hain jab pehle se na hon
    name = engine.url.get_backend_name()
    print(f"[db] {name} @ {engine.url.host or 'local file'}")
    if name == "sqlite":
        print("[db] WARNING: DATABASE_URL nahi mila, local SQLite chal rahi hai. Supabase use nahi ho raha.")
    existing = {column["name"] for column in inspect(engine).get_columns("applications")}
    types = {"role_type": "VARCHAR(80)", "domain": "VARCHAR(80)", "channel": "VARCHAR(80)", "response_date": "VARCHAR(10)"}
    with engine.begin() as c:
        for column, definition in types.items():
            if column not in existing:
                c.exec_driver_sql(f'ALTER TABLE applications ADD COLUMN "{column}" {definition}')


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


def get_document_chunks(user_id):
    q = select(chunks.c.doc_name, chunks.c.text).where(chunks.c.user_id == user_id)
    with engine.connect() as c:
        return [{"source": r[0] or "Document", "text": r[1]} for r in c.execute(q)]


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


def add_scorecard(user_id, session_id, average, count, result):
    with engine.begin() as c:
        res = c.execute(insert(scorecards).values(
            user_id=user_id,
            session_id=session_id,
            average=average,
            count=count,
            result=result,
        ))
        return res.inserted_primary_key[0]


def get_scorecards(user_id, limit=20):
    q = (select(scorecards)
         .where(scorecards.c.user_id == user_id)
         .order_by(scorecards.c.id.desc())
         .limit(limit))
    with engine.connect() as c:
        rows = [dict(r._mapping) for r in c.execute(q)]
    for r in rows:
        r["created_at"] = r["created_at"].strftime("%Y-%m-%d %H:%M") if r["created_at"] else ""
        r["result"] = json.loads(r["result"])
        r.pop("average", None)
        r.pop("user_id", None)
    return rows


def add_career_intake(user_id, target_role, experience, timeline, resume_title, resume_text, jd_text, jd_url, result):
    with engine.begin() as c:
        c.execute(insert(career_intakes).values(
            user_id=user_id, target_role=target_role, experience=experience, timeline=timeline,
            resume_title=resume_title, resume_text=resume_text, jd_text=jd_text,
            jd_url=jd_url, result=result,
        ))


def get_latest_career_intake(user_id):
    q = select(career_intakes).where(career_intakes.c.user_id == user_id).order_by(career_intakes.c.id.desc()).limit(1)
    with engine.connect() as c:
        row = c.execute(q).fetchone()
    if not row:
        return None
    r = dict(row._mapping)
    r.pop("user_id", None)
    r["created_at"] = r["created_at"].strftime("%Y-%m-%d %H:%M") if r["created_at"] else ""
    r["result"] = json.loads(r["result"])
    return r


def save_roadmap(user_id, target_role, weeks, result):
    with engine.begin() as c:
        c.execute(insert(roadmaps).values(
            user_id=user_id, target_role=target_role, weeks=weeks, result=result,
        ))


def get_latest_roadmap(user_id):
    q = select(roadmaps).where(roadmaps.c.user_id == user_id).order_by(roadmaps.c.id.desc()).limit(1)
    with engine.connect() as c:
        row = c.execute(q).fetchone()
    if not row:
        return None
    r = dict(row._mapping)
    r.pop("user_id", None)
    r["created_at"] = r["created_at"].strftime("%Y-%m-%d %H:%M") if r["created_at"] else ""
    r["result"] = json.loads(r["result"])
    return r


def save_portfolio_projects(user_id, target_role, result):
    with engine.begin() as c:
        c.execute(insert(portfolio_projects).values(
            user_id=user_id, target_role=target_role, result=result,
        ))


def get_latest_portfolio_projects(user_id):
    q = select(portfolio_projects).where(portfolio_projects.c.user_id == user_id).order_by(portfolio_projects.c.id.desc()).limit(1)
    with engine.connect() as c:
        row = c.execute(q).fetchone()
    if not row:
        return None
    r = dict(row._mapping)
    r.pop("user_id", None)
    r["created_at"] = r["created_at"].strftime("%Y-%m-%d %H:%M") if r["created_at"] else ""
    r["result"] = json.loads(r["result"])
    return r


def set_skill_progress(user_id, skill, mastery):
    with engine.begin() as c:
        row = c.execute(select(skill_progress).where(
            skill_progress.c.user_id == user_id,
            skill_progress.c.skill == skill,
        )).fetchone()
        values = {"mastery": mastery, "updated_at": func.now()}
        if row:
            c.execute(update(skill_progress).where(
                skill_progress.c.user_id == user_id,
                skill_progress.c.skill == skill,
            ).values(**values))
        else:
            c.execute(insert(skill_progress).values(
                user_id=user_id, skill=skill, mastery=mastery,
            ))


def get_skill_progress(user_id):
    q = select(skill_progress.c.skill, skill_progress.c.mastery).where(
        skill_progress.c.user_id == user_id
    ).order_by(skill_progress.c.skill)
    with engine.connect() as c:
        return {skill: mastery for skill, mastery in c.execute(q)}


def list_sessions(user_id, limit=50):
    q = select(sessions).where(sessions.c.user_id == user_id).order_by(sessions.c.id.desc()).limit(limit)
    with engine.connect() as c:
        rows = [dict(r._mapping) for r in c.execute(q)]
    for r in rows:
        r["ts"] = r["created_at"].isoformat() if r["created_at"] else ""
        r["created_at"] = r["created_at"].strftime("%Y-%m-%d %H:%M") if r["created_at"] else ""
    return rows
