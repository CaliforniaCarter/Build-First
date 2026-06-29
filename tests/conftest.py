"""Test fixtures. Point all engine file I/O at a throwaway home BEFORE importing engine,
and provide a FakeProvider so nothing touches a real Claude subscription."""

from __future__ import annotations

import json
import os
import shutil
import tempfile

# Must happen before any `engine` import so config.HOME resolves here.
_TMP_HOME = tempfile.mkdtemp(prefix="content-test-home-")
os.environ["CONTENT_HOME"] = _TMP_HOME

import pytest  # noqa: E402

from engine.providers.base import Provider  # noqa: E402
from engine.rubric.schemas import DIM_NAMES, GATE_NAMES  # noqa: E402

_FULL_SCORE = json.dumps(
    {
        "gates": [{"name": n, "passed": True, "reason": "ok"} for n in GATE_NAMES],
        "dimensions": [{"name": n, "score": 8, "reason": "ok"} for n in DIM_NAMES],
        "delta_vs_prev": "baseline",
    }
)

_DRAFT = "i shipped a thing today. it broke at 2am. i fixed it and learned why."
_REVISED = "i shipped a thing. it broke at 2am — my fault. here's the fix, and the lesson."


class FakeProvider(Provider):
    """Canned, schema-valid outputs keyed by stage prefix. No subprocess, no network."""

    name = "fake"

    def __init__(self, *args, revised: str | None = None, **kwargs):
        self._revised = revised if revised is not None else _REVISED

    def complete(self, stage: str, prompt: str) -> str:
        if stage.startswith("score"):
            return _FULL_SCORE
        if stage.startswith("council"):
            return json.dumps(
                {
                    "critique": "tighten the hook",
                    "revised_draft": self._revised,
                    "stop": True,
                    "reason": "passes",
                }
            )
        if stage == "persona":
            return "# persona.md\n\nVoice signature: plain, direct, dry\n"
        return _DRAFT


@pytest.fixture(autouse=True)
def clean_home():
    """Each test starts from an empty home (the home path itself is stable for the session)."""
    for sub in ("data", "profiles", "runs"):
        shutil.rmtree(os.path.join(_TMP_HOME, sub), ignore_errors=True)
    yield


@pytest.fixture
def fake_provider():
    return FakeProvider()
