import json

from pypdf import PdfReader

from llm import ask_llm


def extract_text(file_obj):
    reader = PdfReader(file_obj)
    return "\n".join(page.extract_text() or "" for page in reader.pages).strip()


def analyze(resume, jd):
    prompt = (
        "Tum ek ATS resume reviewer ho. Neeche resume aur job description hai. "
        "Sirf JSON do, is format mein: "
        '{"score": 0 se 100 ka number, "strengths": [], "gaps": [], "suggestions": [], "keywords_missing": []}\n\n'
        f"RESUME:\n{resume}\n\nJOB DESCRIPTION:\n{jd}"
    )
    text = ask_llm(prompt)
    start, end = text.find("{"), text.rfind("}")
    return json.loads(text[start:end + 1])