"""ClaudeCodeProvider behavior, fully mocked — no real `claude`, no subscription needed.

The load-bearing guarantees: it parses the json result, maps failures to typed errors, and
SCRUBS the API key from the subprocess env so calls go over subscription OAuth.
"""

from __future__ import annotations

import json
import subprocess
import types

import pytest

from engine.providers import claudecode as cc
from engine.providers.claudecode import (
    ClaudeCodeError,
    ClaudeCodeProvider,
    ClaudeNotFound,
    ClaudeNotLoggedIn,
    ClaudeTimeout,
    check_claude,
)


def _completed(stdout="", stderr="", returncode=0):
    return types.SimpleNamespace(stdout=stdout, stderr=stderr, returncode=returncode)


def _result_json(text):
    return json.dumps({"type": "result", "subtype": "success", "is_error": False, "result": text})


@pytest.fixture
def installed(monkeypatch):
    monkeypatch.setattr(cc.shutil, "which", lambda _b: "/usr/local/bin/claude")


def test_complete_parses_result(installed, monkeypatch):
    monkeypatch.setattr(cc.subprocess, "run", lambda *a, **k: _completed(_result_json("POST TEXT")))
    assert ClaudeCodeProvider().complete("draft", "hello") == "POST TEXT"


def test_complete_scrubs_api_key(installed, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-should-not-leak")
    captured = {}

    def fake_run(*args, **kwargs):
        captured["env"] = kwargs.get("env")
        return _completed(_result_json("ok"))

    monkeypatch.setattr(cc.subprocess, "run", fake_run)
    ClaudeCodeProvider().complete("draft", "hi")
    assert "ANTHROPIC_API_KEY" not in captured["env"]
    assert "ANTHROPIC_AUTH_TOKEN" not in captured["env"]


def test_not_logged_in_maps_to_typed_error(installed, monkeypatch):
    monkeypatch.setattr(
        cc.subprocess,
        "run",
        lambda *a, **k: _completed(stderr="Not logged in. Please run claude login", returncode=1),
    )
    with pytest.raises(ClaudeNotLoggedIn):
        ClaudeCodeProvider().complete("draft", "hi")


def test_missing_binary_maps_to_not_found(monkeypatch):
    monkeypatch.setattr(cc.shutil, "which", lambda _b: None)
    with pytest.raises(ClaudeNotFound):
        ClaudeCodeProvider().complete("draft", "hi")


def test_timeout_maps_to_typed_error(installed, monkeypatch):
    def boom(*a, **k):
        raise subprocess.TimeoutExpired(cmd="claude", timeout=1)

    monkeypatch.setattr(cc.subprocess, "run", boom)
    with pytest.raises(ClaudeTimeout):
        ClaudeCodeProvider().complete("draft", "hi")


def test_bad_json_maps_to_error(installed, monkeypatch):
    monkeypatch.setattr(cc.subprocess, "run", lambda *a, **k: _completed(stdout="not json at all"))
    with pytest.raises(ClaudeCodeError):
        ClaudeCodeProvider().complete("draft", "hi")


def test_is_error_payload_raises(installed, monkeypatch):
    payload = json.dumps({"type": "result", "is_error": True, "subtype": "x", "result": "boom"})
    monkeypatch.setattr(cc.subprocess, "run", lambda *a, **k: _completed(stdout=payload))
    with pytest.raises(ClaudeCodeError):
        ClaudeCodeProvider().complete("draft", "hi")


class _FakePopen:
    """Minimal Popen stand-in that yields stream-json lines then a result line."""

    def __init__(self, lines):
        self._lines = lines
        self.stdin = types.SimpleNamespace(write=lambda *_: None, close=lambda: None)
        self.stdout = iter(lines)
        self.stderr = types.SimpleNamespace(read=lambda: "")

    def wait(self, timeout=None):
        return 0


def test_streaming_emits_tokens_and_final(installed, monkeypatch):
    delta = {
        "type": "stream_event",
        "event": {"type": "content_block_delta", "delta": {"type": "text_delta", "text": "Hel"}},
    }
    delta2 = {
        "type": "stream_event",
        "event": {"type": "content_block_delta", "delta": {"type": "text_delta", "text": "lo"}},
    }
    result = {"type": "result", "result": "Hello"}
    lines = [json.dumps(delta) + "\n", json.dumps(delta2) + "\n", json.dumps(result) + "\n"]
    monkeypatch.setattr(cc.subprocess, "Popen", lambda *a, **k: _FakePopen(lines))

    events: list[tuple[str, dict]] = []
    p = ClaudeCodeProvider(
        stream=True, on_event=lambda kind, payload: events.append((kind, payload))
    )
    out = p.complete("draft", "hi")

    assert out == "Hello"
    tokens = [pay["text"] for kind, pay in events if kind == "token"]
    assert "".join(tokens) == "Hello"


def test_check_claude_not_installed(monkeypatch):
    monkeypatch.setattr(cc.shutil, "which", lambda _b: None)
    st = check_claude()
    assert not st.installed and not st.logged_in


def test_check_claude_logged_in(monkeypatch):
    monkeypatch.setattr(cc.shutil, "which", lambda _b: "/usr/local/bin/claude")

    def fake_run(argv, *a, **k):
        if "--version" in argv:
            return _completed(stdout="claude 2.1.195")
        return _completed(stdout=_result_json("ok"))

    monkeypatch.setattr(cc.subprocess, "run", fake_run)
    st = check_claude()
    assert st.installed and st.logged_in
    assert st.version
