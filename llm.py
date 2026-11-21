import os
import json
import re
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError

from dotenv import load_dotenv
from google import genai

load_dotenv()
client = genai.Client(api_key=os.getenv("LLM_API_KEY"))
MODEL = os.getenv("LLM_MODEL", "gemini-3.5-flash-lite")


class LLMError(Exception):
    pass


def _call(prompt):
    resp = client.models.generate_content(model=MODEL, contents=prompt)
    text = (resp.text or "").strip()
    if not text:
        raise LLMError("The AI returned an empty response")
    return text


def ask_llm(prompt, retries=2, timeout=60):
    last_error = None
    for attempt in range(retries + 1):
        try:
            with ThreadPoolExecutor(max_workers=1) as pool:
                future = pool.submit(_call, prompt)
                return future.result(timeout=timeout)
        except (FuturesTimeoutError, TimeoutError, LLMError) as exc:
            last_error = exc
        except Exception as exc:
            message = str(exc).lower()
            if "429" in message or "429" in str(getattr(exc, "status_code", "")) or "503" in message or "500" in message:
                last_error = exc
            else:
                last_error = exc
                break
        if attempt < retries:
            time.sleep(2 * (attempt + 1))
    raise LLMError(str(last_error or "The AI did not respond"))


def ask_llm_json(prompt, retries=2, timeout=60):
    last_error = None
    for attempt in range(retries + 1):
        try:
            raw = ask_llm(prompt, retries=0, timeout=timeout)
            cleaned = re.sub(r"^```(?:json)?\s*", "", raw.strip(), flags=re.I)
            cleaned = re.sub(r"\s*```$", "", cleaned)
            return json.loads(cleaned)
        except Exception as exc:
            last_error = exc
            if attempt < retries:
                time.sleep(1 + attempt)
    raise LLMError("The AI returned invalid JSON")
