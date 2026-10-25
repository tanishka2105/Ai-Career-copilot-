from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.staticfiles import StaticFiles
import db 
import os
from pydantic import BaseModel 
import auth 
from fastapi import Depends

from analyzer import analyze, extract_text

app = FastAPI(title="AI Career Copilot")
db.init_db()

@app.post("/api/analyze")
def analyze_resume(resume: UploadFile = File(...), jd: str = Form(...)):
    if not (resume.filename or "").lower().endswith(".pdf"):
        raise HTTPException(400, "Sirf PDF upload karo")
    text = extract_text(resume.file)
    if len(text) < 50:
        raise HTTPException(400, "PDF se text nahi nikla (scanned PDF ho sakta hai)")
    try:
        return analyze(text, jd)
    except Exception:
        raise HTTPException(502, "AI se jawab nahi aaya, dobara try karo")


# Ye sabse last mein: frontend/ folder ko website ki tarah serve karta hai
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")

# instead of uvicorn main:app --reload python main.py use kr skte 
if __name__=="__main__":
    import uvicorn
    uvicorn.run("main:app",reload=True)

class Creds(BaseModel):
    username: str
    password: str

@app.post("/api/signup")
def signup(c: Creds):
    username = c.username.strip()
    if len(username) < 3 or len(c.password) < 8:
        raise HTTPException(400, "Username 3+ aur password 8+ characters ka ho")
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