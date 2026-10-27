import json
import os

from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlalchemy import delete, select

import agent
import auth
import db
import rag
from analyzer import analyze, extract_text

app = FastAPI(title="AI Career Copilot")
db.init_db()

DOC_TAG = "[doc] "   # marks document chats inside chat_sessions.title, no database change needed


class Creds(BaseModel):
    username: str
    password: str


@app.post("/api/signup")
def signup(c: Creds):
    username = c.username.strip()
    if len(username) < 3 or len(c.password) < 6:
        raise HTTPException(400, "Username needs 3+ characters and password 6+ characters")
    if ":" in username:
        raise HTTPException(400, "Username cannot contain a colon")
    salt = os.urandom(16)
    if not db.create_user(username, salt, auth.hash_password(c.password, salt)):
        raise HTTPException(400, "This username is already taken")
    return {"ok": True}


@app.post("/api/login")
def login(c: Creds):
    user = db.get_user(c.username.strip())
    if not user or not auth.verify(c.password, user["salt"], user["password_hash"]):
        raise HTTPException(401, "Wrong username or password")
    return {"token": auth.make_token(user["id"])}


@app.get("/api/config")
def config():
    return {"google_client_id": auth.GOOGLE_CLIENT_ID}


class GoogleLogin(BaseModel):
    credential: str


@app.post("/api/google")
def google_login(g: GoogleLogin):
    if not auth.GOOGLE_CLIENT_ID:
        raise HTTPException(400, "Google sign-in is not set up")
    try:
        email = auth.verify_google(g.credential)
    except Exception as e:
        print("Google verify error:", repr(e))
        raise HTTPException(401, "Google could not verify this sign-in")
    username = "google:" + email
    user = db.get_user(username)
    if not user:
        salt = os.urandom(16)
        db.create_user(username, salt, auth.hash_password(os.urandom(16).hex(), salt))
        user = db.get_user(username)
    return {"token": auth.make_token(user["id"])}


@app.get("/api/me")
def me(uid: int = Depends(auth.current_user)):
    user = db.get_user_by_id(uid)
    if not user:
        raise HTTPException(401, "Please sign in")
    return {"username": user["username"].replace("google:", "")}


@app.post("/api/analyze")
def analyze_resume(resume: UploadFile | None = File(None), resume_text: str = Form(""),
                   jd: str = Form(...), uid: int = Depends(auth.current_user)):
    if resume is not None and resume.filename:
        if not resume.filename.lower().endswith(".pdf"):
            raise HTTPException(400, "Upload a PDF, or paste the resume text")
        text, title = extract_text(resume.file), resume.filename
    else:
        text, title = resume_text, "Pasted resume"
    if len(text.strip()) < 50:
        raise HTTPException(400, "Resume text is too short or could not be read (scanned PDF?)")
    try:
        result = analyze(text, jd)
    except Exception as e:
        print("Analyze error:", repr(e))
        raise HTTPException(502, "The AI did not respond, please try again")
    db.add_history(uid, title, json.dumps(result))
    return result


@app.get("/api/history")
def history(uid: int = Depends(auth.current_user)):
    return [{"id": r["id"], "title": r["title"], "created_at": r["created_at"],
             "result": json.loads(r["result"])} for r in db.get_history(uid, 20)]


@app.post("/api/docs")
def upload_doc(doc: UploadFile = File(...), uid: int = Depends(auth.current_user)):
    if not (doc.filename or "").lower().endswith(".pdf"):
        raise HTTPException(400, "Upload a PDF file")
    chunks = rag.chunk_text(extract_text(doc.file))
    if not chunks:
        raise HTTPException(400, "No text could be read from this PDF")
    db.add_chunks(uid, doc.filename, chunks)
    return {"chunks": len(chunks)}


@app.get("/api/docs")
def list_docs(uid: int = Depends(auth.current_user)):
    return db.list_docs(uid)


@app.delete("/api/docs")
def clear_docs(uid: int = Depends(auth.current_user)):
    db.clear_docs(uid)
    return {"ok": True}


class Question(BaseModel):
    question: str
    session_id: int | None = None


@app.post("/api/ask")
def ask(q: Question, uid: int = Depends(auth.current_user)):
    sid = q.session_id
    if sid is not None and not db.session_owned(sid, uid):
        raise HTTPException(404, "Chat not found")
    chunks = rag.top_chunks(q.question, db.get_chunks(uid))
    if not chunks:
        answer, sources = "Nothing found. Add a document first or rephrase the question.", []
    else:
        try:
            answer, sources = rag.answer(q.question + "\n\n(Answer in English.)", chunks), chunks
        except Exception as e:
            print("Ask error:", repr(e))
            raise HTTPException(502, "The AI did not respond, please try again")
    if sid is None:
        sid = db.create_session(uid, DOC_TAG + q.question[:40])
    db.add_message(sid, "user", q.question)
    db.add_message(sid, "assistant", answer)
    return {"answer": answer, "sources": sources, "session_id": sid}


class Msg(BaseModel):
    role: str
    content: str


class Chat(BaseModel):
    messages: list[Msg]
    session_id: int | None = None
    context: str = ""


@app.post("/api/coach")
def coach(chat: Chat, uid: int = Depends(auth.current_user)):
    msgs = [m.model_dump() for m in chat.messages if m.role in ("user", "assistant")][-20:]
    if not msgs or msgs[-1]["role"] != "user":
        raise HTTPException(400, "No message to answer")
    sid = chat.session_id
    if sid is not None and not db.session_owned(sid, uid):
        raise HTTPException(404, "Chat not found")
    agent_msgs = [dict(m) for m in msgs]
    if chat.context:
        agent_msgs[-1]["content"] = chat.context + "\n\n" + agent_msgs[-1]["content"]
    try:
        reply = agent.coach(agent_msgs, uid)
    except Exception as e:
        print("Coach error:", repr(e))
        raise HTTPException(502, "The coach did not respond, please try again")
    if sid is None:
        first = next((x["content"] for x in msgs if x["role"] == "user"), "Chat")
        sid = db.create_session(uid, first[:45])
    db.add_message(sid, "user", msgs[-1]["content"])
    db.add_message(sid, "assistant", reply)
    return {"reply": reply, "session_id": sid}


@app.get("/api/sessions")
def sessions(uid: int = Depends(auth.current_user)):
    items = []
    for s in db.list_sessions(uid):
        t = s["title"] or "Chat"
        kind = "doc" if t.startswith(DOC_TAG) else "chat"
        items.append({"id": s["id"], "type": kind, "title": t.removeprefix(DOC_TAG),
                      "created_at": s["created_at"], "ts": s["ts"]})
    items += [{"id": h["id"], "type": "analysis", "title": h["title"], "created_at": h["created_at"],
               "ts": h["ts"], "result": json.loads(h["result"])} for h in db.get_history(uid, 50)]
    return sorted(items, key=lambda x: x["ts"], reverse=True)


@app.get("/api/sessions/{sid}")
def session_detail(sid: int, uid: int = Depends(auth.current_user)):
    if not db.session_owned(sid, uid):
        raise HTTPException(404, "Chat not found")
    return {"messages": db.get_messages(sid)}


def _delete_sessions(uid, sid=None):
    with db.engine.begin() as c:
        q = select(db.sessions.c.id).where(db.sessions.c.user_id == uid)
        if sid is not None:
            q = q.where(db.sessions.c.id == sid)
        ids = [r[0] for r in c.execute(q)]
        if ids:
            c.execute(delete(db.messages).where(db.messages.c.session_id.in_(ids)))
            c.execute(delete(db.sessions).where(db.sessions.c.id.in_(ids)))


@app.delete("/api/sessions/{sid}")
def delete_session(sid: int, uid: int = Depends(auth.current_user)):
    _delete_sessions(uid, sid)
    return {"ok": True}


@app.delete("/api/sessions")
def delete_all_sessions(uid: int = Depends(auth.current_user)):
    _delete_sessions(uid)
    return {"ok": True}


@app.post("/api/extract")
def extract(file: UploadFile = File(...), uid: int = Depends(auth.current_user)):
    name = (file.filename or "").lower()
    if name.endswith(".pdf"):
        text = extract_text(file.file)
    elif name.endswith(".txt"):
        text = file.file.read().decode("utf-8", errors="ignore")
    else:
        raise HTTPException(400, "Upload a PDF or TXT file")
    if not text.strip():
        raise HTTPException(400, "No text could be read from this file")
    return {"text": text[:8000]}


# Keep this last: serves the frontend/ folder as the website
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")