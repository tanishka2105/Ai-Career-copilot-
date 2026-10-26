import json

from pypdf import PdfReader

from llm import ask_llm


def extract_text(file_obj):
    reader = PdfReader(file_obj)
    return "\n".join(page.extract_text() or "" for page in reader.pages).strip()


def analyze(resume, jd):
    prompt = (
        "Tum ek ATS resume reviewer aur interview coach ho. Neeche resume aur job description hai. "
        "Sirf JSON do, bina extra text ke, is format mein: "
        '{"score": 0 se 100 ka number, "strengths": [], "gaps": [], "suggestions": [], '
        '"interview_questions": [{"question": "", "type": "technical ya behavioral", '
        '"answer_framework": "model answer ka dhancha", '
        '"star": {"situation": "", "task": "", "action": "", "result": ""}}], '
        '"best_practices": []}\n'
        "interview_questions mein job description ke hisaab se 6 sawal do (3 technical, 3 behavioral). "
        "Behavioral sawalon ke liye star bharo, technical ke liye star null rakho. "
        "best_practices mein 5 interview aur communication tips do.\n\n"
        f"RESUME:\n{resume}\n\nJOB DESCRIPTION:\n{jd}"
    )
    text = ask_llm(prompt)
    start, end = text.find("{"), text.rfind("}")
    data = json.loads(text[start:end + 1])
    for key in ("strengths", "gaps", "suggestions", "interview_questions", "best_practices"):
        if not isinstance(data.get(key), list):
            data[key] = []
    return data
