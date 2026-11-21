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


def test_scorecard_history_is_saved_and_private(client, user, monkeypatch):
    monkeypatch.setattr(main.agent, "coach", lambda m, u: "Question: tell me about a project.")
    a, b = user("alina"), user("ben")
    sid = chat(client, a, "Start the interview").json()["session_id"]
    chat(client, a, "I built a project.", sid)
    fake = json.dumps({
        "answers": [{"index": 0, "score": 8, "comment": "Clear"}],
        "strengths": ["clear"],
        "weaknesses": ["depth"],
        "recommendations": ["add metrics"],
    })
    monkeypatch.setattr(features, "ask_llm", lambda p: fake)
    assert client.post("/api/scorecard", headers=a, json={"session_id": sid}).status_code == 200
    history = client.get("/api/scorecards", headers=a).json()["scorecards"]
    assert len(history) == 1 and history[0]["result"]["average"] == 8.0
    assert client.get("/api/scorecards", headers=b).json()["scorecards"] == []


def test_progress_adjustment_moves_behind_and_ahead(client, user):
    h = user()
    behind = client.post("/api/progress/adjust", headers=h, json={
        "total_tasks": 10,
        "completed_tasks": 2,
        "planned_weeks": 4,
        "latest_score": 4,
        "struggling_skills": ["SQL"],
    }).json()
    assert behind["status"] == "behind" and behind["adjusted_weeks"] == 5
    ahead = client.post("/api/progress/adjust", headers=h, json={
        "total_tasks": 10,
        "completed_tasks": 9,
        "planned_weeks": 4,
        "latest_score": 8,
        "struggling_skills": [],
    }).json()
    assert ahead["status"] == "ahead" and ahead["adjusted_weeks"] == 3


def test_application_response_insights_include_channel_and_domain(client, user):
    h = user()
    for i in range(5):
        client.post("/api/jobs", headers=h, json={
            "company": f"Acme{i}",
            "role": "Backend Engineer",
            "role_type": "Engineering",
            "domain": "Fintech",
            "channel": "Referral",
            "status": "Interview" if i < 2 else "Applied",
        })
    insights = client.get("/api/jobs/insights", headers=h).json()
    assert insights["role_type_stats"][0]["label"] == "Engineering"
    assert insights["domain_stats"][0]["label"] == "Fintech"
    assert insights["channel_stats"][0]["label"] == "Referral"


def test_application_insight_empty_states(client, user):
    h = user()
    empty = client.get("/api/jobs/insights", headers=h).json()
    assert empty["eligible"] is False
    assert "0" in empty["empty_text"]

    for i in range(3):
        client.post("/api/jobs", headers=h, json={"company": f"C{i}", "role": "Web Developer", "status": "Applied"})
    below_five = client.get("/api/jobs/insights", headers=h).json()
    assert below_five["eligible"] is False
    assert "You have 3 so far" in below_five["empty_text"]

    for i in range(2):
        client.post("/api/jobs", headers=h, json={"company": f"D{i}", "role": "Data Analyst", "status": "Applied"})
    no_response = client.get("/api/jobs/insights", headers=h).json()
    assert no_response["eligible"] is False
    assert "No responses yet" in no_response["empty_text"]

    client.put("/api/jobs/1", headers=h, json={"company": "C0", "role": "Web Developer", "status": "Interview"})
    one_response = client.get("/api/jobs/insights", headers=h).json()
    assert one_response["eligible"] is False


def test_weekly_plan_and_portfolio_end_to_end(client, user, monkeypatch):
    h = user()
    monkeypatch.setattr(features, "ask_llm", lambda p:
        '[{"week":1,"theme":"SQL","tasks":[{"task":"Build joins","resource":"SQL tutorial","skill":"SQL"}]}]'
        if "Create a 4-week learning plan" in p
        else '[{"title":"SQL Dashboard","description":"Build a report","skills_covered":["SQL"],"difficulty":"Intermediate","duration":"1 week"},{"title":"SQL Quality Check","description":"Build data tests","skills_covered":["SQL"],"difficulty":"Beginner","duration":"1 week"},{"title":"SQL API","description":"Build SQL API","skills_covered":["SQL"],"difficulty":"Intermediate","duration":"1 week"}]')
    plan = client.post("/api/weekly-plan", headers=h, json={
        "target_role": "Data Analyst",
        "gaps": ["SQL"],
        "skill_gap_map": [{"skill": "SQL", "current_level": "Beginner", "required_level": "Intermediate", "gap_severity": "High"}],
        "weeks": 4,
    })
    assert plan.status_code == 200
    assert plan.json()["weeks"][0]["tasks"][0]["skill"] == "SQL"
    projects = client.post("/api/portfolio", headers=h, json={
        "target_role": "Data Analyst",
        "gaps": ["SQL"],
        "skill_gap_map": [{"skill": "SQL", "current_level": "Beginner", "required_level": "Intermediate"}],
    })
    assert projects.status_code == 200
    assert projects.json()["projects"][0]["title"] == "SQL Dashboard"


def test_saved_state_accepts_pipeline_objects(client, user):
    h = user()
    payloads = [
        {"key": "resume", "value": "Resume text"},
        {"key": "weekly", "value": {"weeks": [{"week": 1, "theme": "SQL", "tasks": []}]}},
        {"key": "projects", "value": [{"title": "Dashboard", "completed": False}]},
        {"key": "skill_mastery", "value": {"SQL": "Learning"}},
    ]
    for payload in payloads:
        assert client.put("/api/state", headers=h, json=payload).status_code == 200
    state = client.get("/api/state", headers=h).json()
    assert state["resume"] == "Resume text"
    assert state["weekly"]["weeks"][0]["theme"] == "SQL"
    assert state["projects"][0]["title"] == "Dashboard"
    assert state["skill_mastery"]["SQL"] == "Learning"


def test_skill_progress_is_saved_and_private(client, user):
    a, b = user("nora"), user("omar")
    r = client.put("/api/skills/SQL", headers=a, json={"mastery": "Practicing"})
    assert r.status_code == 200
    assert client.get("/api/skills", headers=a).json()["skills"]["SQL"] == "Practicing"
    assert "SQL" not in client.get("/api/skills", headers=b).json()["skills"]


def test_career_intake_persists_latest_records(client, user):
    h = user()
    result = {"score": 72, "gaps": ["SQL"], "skill_gap_map": [{"skill": "SQL", "gap_severity": "High"}]}
    r = client.post("/api/intake", headers=h, json={
        "target_role": "Data Analyst",
        "experience": "1 to 3",
        "timeline": "2026-12-01",
        "resume_title": "Resume",
        "resume_text": "Candidate worked with Python and reporting tools.",
        "jd_text": "The role requires SQL, Python, dashboards, and stakeholder communication.",
        "jd_url": "",
        "result": result,
    })
    assert r.status_code == 200
    latest = client.get("/api/intake", headers=h).json()["intake"]
    assert latest["target_role"] == "Data Analyst"
    assert latest["result"]["score"] == 72


def test_progress_adjustment_uses_skill_mastery(client, user):
    h = user()
    r = client.post("/api/progress/adjust", headers=h, json={
        "total_tasks": 10,
        "completed_tasks": 9,
        "planned_weeks": 4,
        "latest_score": 8,
        "struggling_skills": ["SQL"],
        "skill_mastery": {"SQL": "Mastered", "Python": "Learning"},
    })
    assert r.status_code == 200
    assert r.json()["status"] in ("ahead", "behind", "on_track")
    assert "SQL" in r.json()["priorities"] or "Python" in r.json()["priorities"]