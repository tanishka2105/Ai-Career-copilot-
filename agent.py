import db
import rag
import json

from llm import ask_llm
TOOLS_HELP = (
    "Tools:\n"
    '1. get_last_analysis: user ka sabse naya resume analysis (score, gaps). Input: {}\n'
    '2. search_documents: user ke documents mein search. Input: {"query": "..."}'
)

INSTRUCTIONS = (
    "Tum ek interview coach ho. Ek baar mein sirf EK sawal pucho. "
    "Shuru mein get_last_analysis tool se user ki kamiyan dekho aur unke hisaab se sawal pucho. "
    "User jawab de toh 2-3 line ka feedback do aur agla sawal pucho.\n\n"
    "English mein baat karo.\n"
    "Har baar sirf ek JSON do:\n"
    '1) Tool chahiye toh: {"tool": "tool_ka_naam", "args": {}}\n'
    '2) Final jawab ke liye: {"final": "user ko dikhane wala text"}\n\n' + TOOLS_HELP
)


def run_tool(name, args, user_id):
    if name == "get_last_analysis":
        rows = db.get_history(user_id, 1)
        return rows[0]["result"] if rows else "Abhi koi analysis nahi hai"
    if name == "search_documents":
        found = rag.top_chunks(args.get("query", ""), db.get_chunks(user_id))
        return "\n---\n".join(found) or "Kuch nahi mila"
    return "Unknown tool"


def parse(text):
    start, end = text.find("{"), text.rfind("}")
    try:
        data = json.loads(text[start:end + 1])
    except ValueError:
        return {"final": text.strip()}
    return data if isinstance(data, dict) else {"final": str(data)}


def coach(messages, user_id):
    chat = "\n".join(f"{m['role'].upper()}: {m['content']}" for m in messages)
    notes = ""                                   # tool ke results yahan jama honge
    for _ in range(5):                           # zyada se zyada 5 round
        reply = parse(ask_llm(INSTRUCTIONS + "\n\nBAATCHEET:\n" + chat + notes))
        if "tool" in reply:
            args = reply.get("args")
            result = run_tool(reply["tool"], args if isinstance(args, dict) else {}, user_id)
            notes += f"\n\nTOOL RESULT ({reply['tool']}): {result}"
        else:
            return str(reply.get("final", "")).strip() or "Dobara try karo"
    return "Coach atak gaya, dobara try karo"