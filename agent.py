import json

import db
import rag
from llm import ask_llm

TOOLS_HELP = (
    "Tools:\n"
    '1. get_last_analysis: Retrieve the user\'s most recent resume analysis (score, gaps, skill_gap_map). Input: {}\n'
    '2. search_documents: Search the user\'s uploaded documents. Input: {"query": "..."}'
)

INSTRUCTIONS = (
    "You are a professional interview coach. Ask ONE question at a time. "
    "Start by using get_last_analysis to review the user's weaknesses and tailor questions accordingly. "
    "Easy questions: 1 short sentence and about 15 words or fewer. "
    "Medium questions: 1-2 short sentences and about 25 words or fewer. "
    "Hard questions: about 35 words or fewer and may include a short scenario. "
    "Do not give feedback after an answer. Move directly to the next question. "
    "Never add multiple subquestions or a long introduction.\n\n"
    "Always respond with exactly one JSON object:\n"
    '1) If you need a tool: {"tool": "tool_name", "args": {}}\n'
    '2) For your final response: {"final": "text to show the user"}\n\n' + TOOLS_HELP
)


def run_tool(name, args, user_id):
    if name == "get_last_analysis":
        rows = db.get_history(user_id, 1)
        return rows[0]["result"] if rows else "No analysis available yet."
    if name == "search_documents":
        found = rag.top_chunks(args.get("query", ""), db.get_chunks(user_id))
        return "\n---\n".join(found) or "No matching content found."
    return "Unknown tool"


def parse(text):
    text = text.strip()
    # Try to find JSON object in the response
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return {"final": text}
    candidate = text[start:end + 1]
    try:
        data = json.loads(candidate)
    except (ValueError, json.JSONDecodeError):
        # If JSON parse fails, return the raw text as the final answer
        return {"final": text}
    if isinstance(data, dict) and ("final" in data or "tool" in data):
        return data
    # If the JSON doesn't have expected keys, wrap the text
    return {"final": text}


def coach(messages, user_id):
    chat = "\n".join(f"{m['role'].upper()}: {m['content']}" for m in messages)
    notes = ""
    for _ in range(5):
        raw = ask_llm(INSTRUCTIONS + "\n\nCONVERSATION:\n" + chat + notes)
        reply = parse(raw)
        if "tool" in reply:
            tool_name = reply["tool"]
            args = reply.get("args")
            try:
                result = run_tool(tool_name, args if isinstance(args, dict) else {}, user_id)
            except Exception:
                result = "Tool error, skipping."
            notes += f"\n\nTOOL RESULT ({tool_name}): {result}"
        else:
            answer = str(reply.get("final", "")).strip()
            return answer if answer else "I couldn't generate a response. Please try again."
    return "The coach encountered an issue. Please try again."
