from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.staticfiles import StaticFiles
import db

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