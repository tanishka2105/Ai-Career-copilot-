import json
import os

from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import agent
import auth
import db
import rag
from analyzer import analyze, extract_text

app = FastAPI(title="AI Career Copilot")
db.init_db()


class Creds(BaseModel):
    username: str
    password: str


@app.post("/api/signup")
def signup(c: Creds):
    username = c.username.strip()
    if len(username) < 3 or len(c.password) < 6:
        raise HTTPException(400, "Username 3+ aur password 6+ characters ka ho")
    if ":" in username:
        raise HTTPException(400, "Username mein : nahi ho sakta")
    salt = os.urandom(16)
    if not db.create_user(username, salt, auth.hash_password(c.password, salt)):
        raise HTTPException(400, "Ye username pehle se hai")
    return {"ok": True}


@app.post("/api/login")
def login(c: Creds):
    user = db.get_user(c.username.strip())
    if not user or not auth.verify(c.password, user["salt"], user["password_hash"]):
        raise HTTPException(401, "Username ya password galat hai")
    return {"token": auth.make_token(user["id"])}


@app.get("/api/config")
def config():
    return {"google_client_id": auth.GOOGLE_CLIENT_ID}


class GoogleLogin(BaseModel):
    credential: str


@app.post("/api/google")
def google_login(g: GoogleLogin):
    if not auth.GOOGLE_CLIENT_ID:
        raise HTTPException(400, "Google login set nahi hai")
    try:
        email = auth.verify_google(g.credential)
    except Exception as e:
        print("Google verify error:", repr(e))        # asli wajah terminal mein dikhegi
        raise HTTPException(401, "Google se verify nahi hua")
    username = "google:" + email                 # alag naam, taaki password wale accounts se na takraye
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
        raise HTTPException(401, "Pehle login karo")
    return {"username": user["username"].replace("google:", "")}


@app.post("/api/analyze")
def analyze_resume(resume: UploadFile = File(...), jd: str = Form(...),
                   uid: int = Depends(auth.current_user)):
    if not (resume.filename or "").lower().endswith(".pdf"):
        raise HTTPException(400, "Sirf PDF upload karo")
    text = extract_text(resume.file)
    if len(text) < 50:
        raise HTTPException(400, "PDF se text nahi nikla (scanned PDF ho sakta hai)")
    try:
        result = analyze(text, jd)
    except Exception:
        raise HTTPException(502, "AI se jawab nahi aaya, dobara try karo")
    db.add_history(uid, resume.filename, json.dumps(result))
    return result


@app.get("/api/history")
def history(uid: int = Depends(auth.current_user)):
    return [{"id": r["id"], "title": r["title"], "created_at": r["created_at"],
             "result": json.loads(r["result"])} for r in db.get_history(uid, 20)]


@app.post("/api/docs")
def upload_doc(doc: UploadFile = File(...), uid: int = Depends(auth.current_user)):
    if not (doc.filename or "").lower().endswith(".pdf"):
        raise HTTPException(400, "Sirf PDF upload karo")
    chunks = rag.chunk_text(extract_text(doc.file))
    if not chunks:
        raise HTTPException(400, "PDF se text nahi nikla")
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


@app.post("/api/ask")
def ask(q: Question, uid: int = Depends(auth.current_user)):
    chunks = rag.top_chunks(q.question, db.get_chunks(uid))
    if not chunks:
        return {"answer": "Kuch nahi mila. Pehle document upload kar ya sawal alag tarah se pooch.",
                "sources": []}
    try:
        return {"answer": rag.answer(q.question, chunks), "sources": chunks}
    except Exception:
        raise HTTPException(502, "AI se jawab nahi aaya, dobara try karo")


class Msg(BaseModel):
    role: str
    content: str


class Chat(BaseModel):
    messages: list[Msg]
    session_id: int | None = None


@app.post("/api/coach")
def coach(chat: Chat, uid: int = Depends(auth.current_user)):
    msgs = [m.model_dump() for m in chat.messages if m.role in ("user", "assistant")][-20:]
    if not msgs or msgs[-1]["role"] != "user":
        raise HTTPException(400, "Koi message nahi")
    sid = chat.session_id
    if sid is not None and not db.session_owned(sid, uid):
        raise HTTPException(404, "Session nahi mila")
    try:
        reply = agent.coach(msgs, uid)
    except Exception as e:
        print("Coach error:", repr(e))
        raise HTTPException(502, "Coach se jawab nahi aaya, dobara try karo")
    if sid is None:
        first = next((x["content"] for x in msgs if x["role"] == "user"), "Chat")
        sid = db.create_session(uid, first[:45])
    db.add_message(sid, "user", msgs[-1]["content"])
    db.add_message(sid, "assistant", reply)
    return {"reply": reply, "session_id": sid}


@app.get("/api/sessions")
def sessions(uid: int = Depends(auth.current_user)):
    items = [{"id": s["id"], "type": "chat", "title": s["title"], "created_at": s["created_at"], "ts": s["ts"]}
             for s in db.list_sessions(uid)]
    items += [{"id": h["id"], "type": "analysis", "title": h["title"], "created_at": h["created_at"],
               "ts": h["ts"], "result": json.loads(h["result"])} for h in db.get_history(uid, 50)]
    return sorted(items, key=lambda x: x["ts"], reverse=True)


@app.get("/api/sessions/{sid}")
def session_detail(sid: int, uid: int = Depends(auth.current_user)):
    if not db.session_owned(sid, uid):
        raise HTTPException(404, "Session nahi mila")
    return {"messages": db.get_messages(sid)}


@app.post("/api/extract")
def extract(file: UploadFile = File(...), uid: int = Depends(auth.current_user)):
    name = (file.filename or "").lower()
    if name.endswith(".pdf"):
        text = extract_text(file.file)
    elif name.endswith(".txt"):
        text = file.file.read().decode("utf-8", errors="ignore")
    else:
        raise HTTPException(400, "PDF ya TXT file do")
    if not text.strip():
        raise HTTPException(400, "File se text nahi nikla")
    return {"text": text[:8000]}


# Ye sabse last mein: frontend/ folder ko website ki tarah serve karta hai
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
