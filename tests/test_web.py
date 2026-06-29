"""Web routes via TestClient, with a fake model injected. Covers onboarding, status,
the generate->stream->draft flow, and the invariant that nothing can publish."""

from __future__ import annotations

import re

import pytest
from starlette.testclient import TestClient

from engine.config import DATA_DIR, PROFILES_DIR
from engine.providers.claudecode import ClaudeStatus
from engine.web.app import create_app
from tests.conftest import FakeProvider

_JOB_RE = re.compile(r'"([0-9a-f]{32})"')

ONBOARD_FORM = {
    "name": "Tester",
    "idea__topic": "shipping an overnight build",
    "idea__mechanism": "a provider seam",
    "idea__number": "5 calls",
    "idea__scene": "2am, it broke",
    "voice_a__0": "i shipped the thing and it broke and i fixed it",
    "output__channels": "LinkedIn",
}


def _client() -> TestClient:
    app = create_app(provider_factory=lambda run_id, on_event=None: FakeProvider())
    return TestClient(app)


def _seed_onboarding(client: TestClient) -> None:
    resp = client.post("/onboarding", data=ONBOARD_FORM)
    assert resp.status_code == 200
    job_id = _JOB_RE.search(resp.text).group(1)
    # Drain the persona-build stream to completion (fake model is instant).
    body = client.get(f"/onboarding/stream/{job_id}").text
    assert "event: end" in body
    assert (DATA_DIR / "intake.json").exists()
    assert (PROFILES_DIR / "persona.md").exists()


def test_onboarding_form_renders():
    r = _client().get("/onboarding")
    assert r.status_code == 200
    assert 'name="name"' in r.text
    assert "data-wizard" in r.text  # one-question flow
    assert 'name="voice_a__0"' in r.text  # voice questions live in onboarding
    assert 'name="idea__topic"' not in r.text  # the post idea moved to the Write page


def test_status_page(monkeypatch):
    import engine.web.routes.status as status_mod

    monkeypatch.setattr(
        status_mod,
        "check_claude",
        lambda *a, **k: ClaudeStatus(True, True, "claude 2.1.195", "Logged in."),
    )
    r = _client().get("/status")
    assert r.status_code == 200
    assert "Status" in r.text and "subscription" in r.text


def test_onboarding_writes_intake_and_persona():
    _seed_onboarding(_client())  # asserts files written inside


def test_generate_flow_streams_and_persists():
    client = _client()
    _seed_onboarding(client)

    post_page = client.get("/post")
    assert 'name="idea__topic"' in post_page.text and "data-wizard" in post_page.text

    start = client.post("/post/generate", data={"idea__topic": "a sharper topic"}).json()
    assert "job_id" in start and "run_id" in start

    body = client.get(f"/post/stream/{start['job_id']}").text
    assert "event: end" in body
    assert '"status": "done"' in body or '"status":"done"' in body

    draft_page = client.get(f"/post/draft/{start['run_id']}")
    assert draft_page.status_code == 200
    assert "Export" in draft_page.text


def test_index_redirects_to_onboarding_when_fresh():
    r = _client().get("/", follow_redirects=False)
    assert r.status_code in (302, 307)
    assert r.headers["location"].endswith("/onboarding")


@pytest.mark.parametrize("module", ["posting", "onboarding"])
def test_no_publish_path(module):
    """Routes may only sink to local files / the gate — never an outbound publish client."""
    import importlib

    src = importlib.import_module(f"engine.web.routes.{module}").__file__
    with open(src, encoding="utf-8") as fh:
        text = fh.read().lower()
    for forbidden in ("import requests", "import httpx", "urllib.request", "linkedin.com"):
        assert forbidden not in text, f"{module} must not contain {forbidden!r}"
