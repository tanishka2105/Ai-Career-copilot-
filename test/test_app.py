import json

import features
import main


def chat(client, h, text, sid=None, **extra):
    return client.post("/api/coach", headers=h, json={"messages": [{"role": "user", "content": text}],
                                                      "session_id": sid, **extra})


def test_weak_password_rejected(client):
    assert client.post("/api/signup", json={"username": "bob", "password": "short"}).status_code == 400


def test_private_routes_need_login(client):
    assert client.get("/api/sessions").status_code == 401
    assert client.get("/api/jobs").status_code == 401


def test_coach_prompt_is_built_on_the_server(client, user, monkeypatch):
    seen = {}
    monkeypatch.setattr(main.agent, "coach", lambda m, u: (seen.update(m=m), "ok")[1])
    h = user()
    r = chat(client, h, "hi", context="EVIL INSTRUCTION", round="Technical")
    assert r.status_code == 200
    sent = seen["m"][-1]["content"]
    assert "EVIL INSTRUCTION" not in sent and "Round type: Technical" in sent
    stored = client.get(f"/api/sessions/{r.json()['session_id']}", headers=h).json()["messages"]
    assert stored[0]["content"] == "hi"           # the hidden prompt is not stored as the user's message


def test_overlong_message_rejected(client, user):
    assert chat(client, user(), "x" * 5000).status_code == 422


def test_users_cannot_read_each_others_chats(client, user, monkeypatch):
    monkeypatch.setattr(main.agent, "coach", lambda m, u: "ok")
    sid = chat(client, user("alice"), "hello").json()["session_id"]
    assert client.get(f"/api/sessions/{sid}", headers=user("bobby")).status_code == 404


def test_progress_ignores_automatic_messages(client, user, monkeypatch):
    monkeypatch.setattr(main.agent, "coach", lambda m, u: "ok")
    h = user()
    sid = chat(client, h, "Start the interview").json()["session_id"]
    chat(client, h, "Switch the interview to the Technical round now.", sid)
    chat(client, h, "I led a migration of our billing system.", sid)
    assert client.get("/api/progress", headers=h).json()["total"] == 1


def test_password_reset_is_single_use(client, user, monkeypatch):
    links = []
    monkeypatch.setattr(features, "_send", lambda to, link: links.append(link))
    h = user("carol")
    assert client.post("/api/email", headers=h, json={"email": "c@example.com"}).status_code == 200
    assert client.post("/api/reset/request", json={"identifier": "nobody"}).json() == {"ok": True}
    assert not links                               # unknown account: same reply, no email
    client.post("/api/reset/request", json={"identifier": "carol"})
    token = links[0].split("#reset=")[1]
    assert client.post("/api/reset/confirm", json={"token": token, "password": "NewPass123"}).status_code == 200
    assert client.post("/api/reset/confirm", json={"token": token, "password": "Another123"}).status_code == 400
    assert client.post("/api/login", json={"username": "carol", "password": "Passw0rd1"}).status_code == 401
    assert client.post("/api/login", json={"username": "carol", "password": "NewPass123"}).status_code == 200


def test_deleted_account_cannot_use_old_token(client, user):
    h = user("dave")
    assert client.post("/api/account/delete", headers=h, json={"confirm": "nope"}).status_code == 400
    assert client.post("/api/account/delete", headers=h, json={"confirm": "DELETE"}).status_code == 200
    assert client.get("/api/me", headers=h).status_code == 401


def test_fake_pdf_rejected(client, user):
    r = client.post("/api/docs", headers=user(), files={"doc": ("a.pdf", b"not a pdf", "application/pdf")})
    assert r.status_code == 400


def test_job_tracker_is_private_and_validated(client, user):
    a, b = user("erin"), user("frank")
    jid = client.post("/api/jobs", headers=a, json={"company": "Acme", "role": "Analyst"}).json()["id"]
    assert client.post("/api/jobs", headers=a, json={"company": "X", "role": "Y", "status": "Hired"}).status_code == 400
    assert client.post("/api/jobs", headers=a, json={"company": "X", "role": "Y", "applied_on": "soon"}).status_code == 400
    assert client.get("/api/jobs", headers=b).json() == []
    assert client.put(f"/api/jobs/{jid}", headers=b, json={"company": "Hack", "role": "Y"}).status_code == 404
    assert client.put(f"/api/jobs/{jid}", headers=a, json={"company": "Acme", "role": "Analyst", "status": "Offer"}).status_code == 200
    assert client.get("/api/jobs", headers=a).json()[0]["status"] == "Offer"


def test_guest_match_is_limited_and_trimmed(client, monkeypatch):
    monkeypatch.setattr(features, "analyze", lambda r, j: {"score": 70, "strengths": list("abcde"), "gaps": list("vwxyz"),
                                                             "interview_questions": [1]})
    data = {"resume_text": "r" * 80, "jd": "j" * 40}
    first = client.post("/api/guest/analyze", data=data).json()
    assert len(first["strengths"]) == 3 and "interview_questions" not in first
    for _ in range(2):
        client.post("/api/guest/analyze", data=data)
    assert client.post("/api/guest/analyze", data=data).status_code == 429


def test_scorecard_average_comes_from_valid_scores(client, user, monkeypatch):
    monkeypatch.setattr(main.agent, "coach", lambda m, u: "Question: tell me about a project.")
    h = user()
    sid = chat(client, h, "Start the interview").json()["session_id"]
    assert client.post("/api/scorecard", headers=h, json={"session_id": sid}).status_code == 400   # nothing answered yet
    chat(client, h, "I built a billing migration that cut errors.", sid)
    fake = json.dumps({"answers": [{"index": 0, "score": 7, "comment": "ok"}, {"index": 9, "score": 10}, {"index": 0, "score": 99}],
                       "strengths": ["clear"], "average": 10})
    monkeypatch.setattr(features, "ask_llm", lambda p: fake)
    r = client.post("/api/scorecard", headers=h, json={"session_id": sid}).json()
    assert r["average"] == 7.0 and r["count"] == 1