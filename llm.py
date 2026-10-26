import os

from dotenv import load_dotenv
from google import genai

load_dotenv()
client = genai.Client(api_key=os.getenv("LLM_API_KEY"))
MODEL = os.getenv("LLM_MODEL", "gemini-3.5-flash-lite")


def ask_llm(prompt):
    resp = client.models.generate_content(model=MODEL, contents=prompt)
    return (resp.text or "").strip()
