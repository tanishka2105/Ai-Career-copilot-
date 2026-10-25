import os
from dotenv import load_dotenv

load_dotenv()
k = os.getenv("LLM_API_KEY")
print("LLM_API_KEY mili:", bool(k), "| length:", len(k) if k else 0, "| shuru:", k[:7] if k else None)
print("ANTHROPIC_AUTH_TOKEN set:", bool(os.getenv("ANTHROPIC_AUTH_TOKEN")))
print("ANTHROPIC_API_KEY set:", bool(os.getenv("ANTHROPIC_API_KEY")))