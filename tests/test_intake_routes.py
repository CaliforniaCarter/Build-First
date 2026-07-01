"""The web intake API — deterministic, no model calls.

Verifies the browser onboarding writes answers to the exact `writes_to` paths in
`engine/onboarding.json`, serves only the deterministic questions (the `style_pick`
this-or-that stays in the terminal), and never touches the real `data/intake.json`.
"""

import json

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx")

from fastapi.testclient import TestClient  # noqa: E402

from server import intake as intake_store  # noqa: E402
from server.main import create_app  # noqa: E402


@pytest.fixture
def client(tmp_path, monkeypatch):
    # Isolate all writes to a temp intake.json — never clobber the real one.
    monkeypatch.setattr(intake_store, "INTAKE_PATH", tmp_path / "intake.json")
    return TestClient(create_app())


def read(tmp_path):
    return json.loads((tmp_path / "intake.json").read_text(encoding="utf-8"))


def test_serves_only_deterministic_questions(client):
    data = client.get("/api/onboarding").json()
    assert data["welcome"]
    ids = [q["id"] for q in data["questions"]]
    assert ids == ["name", "background", "writing_samples", "weekend", "lunch", "teach"]
    assert "style_pick" not in ids  # adaptive_ab is terminal-only
    required = {q["id"]: q["required"] for q in data["questions"]}
    assert required["name"] is True
    assert required["writing_samples"] is False  # the only skippable one


def test_answers_land_at_writes_to_paths(client, tmp_path):
    assert client.post("/api/intake/begin").json() == {"ok": True}
    client.patch("/api/intake", json={"answers": {"name": "Carter"}})
    client.patch("/api/intake", json={"answers": {"typed.background": "PM who ships"}})
    client.patch("/api/intake", json={"answers": {"voice.writing_samples": ["a post I wrote"]}})
    client.patch(
        "/api/intake",
        json={
            "answers": {
                "voice.answers.weekend": "skied",
                "voice.answers.lunch": "burrito",
                "voice.answers.teach": "boil water, add pasta",
            }
        },
    )
    data = read(tmp_path)
    assert data["name"] == "Carter"
    assert data["typed"]["background"] == "PM who ships"
    assert data["voice"]["writing_samples"] == ["a post I wrote"]
    assert data["voice"]["answers"] == {
        "weekend": "skied",
        "lunch": "burrito",
        "teach": "boil water, add pasta",
    }
    assert data["voice"]["style_pick"] == ""  # never set by the web


def test_skip_writing_samples_is_empty_list(client, tmp_path):
    client.post("/api/intake/begin")
    client.patch("/api/intake", json={"answers": {"name": "X", "voice.writing_samples": []}})
    assert read(tmp_path)["voice"]["writing_samples"] == []


def test_resume_paste_sets_docs_resume(client, tmp_path):
    client.post("/api/intake/begin")
    files = {"file": ("resume.txt", b"Carter Chasson - product manager", "text/plain")}
    res = client.post("/api/intake/resume", files=files).json()
    assert res["ok"] is True and res["chars"] > 0
    assert "product manager" in read(tmp_path)["docs"]["resume"]


def test_writing_sample_upload_returns_text(client):
    # the endpoint parses the file and returns text; the client folds it into the list
    files = {"file": ("essay.txt", b"I was wrong about onboarding. We cut nine steps to four.", "text/plain")}
    res = client.post("/api/intake/writing-sample", files=files).json()
    assert res["ok"] is True
    assert "onboarding" in res["text"]


def test_health(client):
    assert client.get("/api/health").json() == {"ok": True}
