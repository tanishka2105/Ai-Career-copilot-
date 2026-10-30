import os
import sys
import tempfile
import types

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.environ["DATABASE_URL"] = "sqlite:///" + os.path.join(tempfile.mkdtemp(), "test.db")
os.environ["JWT_SECRET"] = "test-secret"
sys.path.insert(0, ROOT)
os.chdir(ROOT)
os.makedirs("frontend", exist_ok=True)          # main.py mounts this folder
_llm = types.ModuleType("llm")                    # tests never call the real AI
_llm.ask_llm = lambda prompt: "{}"
sys.modules["llm"] = _llm

import pytest                                     # noqa: E402
from fastapi.testclient import TestClient         # noqa: E402

import features                                   # noqa: E402
import main                                       # noqa: E402


@pytest.fixture(autouse=True)
def reset_limits():
    main._hits.clear()
    features._hits.clear()


@pytest.fixture()
def client():
    return TestClient(main.app)


@pytest.fixture()
def user(client):
    def make(name="alice", pw="Passw0rd1"):
        client.post("/api/signup", json={"username": name, "password": pw})
        tok = client.post("/api/login", json={"username": name, "password": pw}).json()["token"]
        return {"Authorization": "Bearer " + tok}
    return make