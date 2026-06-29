"""Stub provider — deterministic, offline, no key. For CI and cold smoke runs.

This is NOT a model. It returns fixed, schema-valid outputs so the whole pipeline
runs end to end with zero manual steps and no network — enough to prove the spine
works (`bf run --provider stub`). For a real draft use `--provider anthropic`; to
drive the model by hand step by step use `--provider terminal`.

Scores rise a little per level so the smoke report shows movement, but the content
is obviously canned — never mistake a stub run for a real one.
"""

from __future__ import annotations

import json

from ..rubric.schemas import DIM_NAMES, GATE_NAMES
from .base import Provider

_PERSONA = (
    "# persona.md (stub)\n\n"
    "- Voice signature: plain, direct, concrete\n"
    "- Vocabulary: everyday words, no jargon\n"
    "- BANNED: delve, leverage, game-changer, thrilled to announce\n"
    "- NEVER-DO: no hype, no emojis, never fake a number\n"
)


def _level_index(stage: str) -> int:
    """Pull the ladder level out of a stage name like 'score_L3' (default 5)."""
    if "_L" in stage:
        tail = stage.split("_L", 1)[1]
        if tail.isdigit():
            return int(tail)
    return 5


def _draft_text(stage: str) -> str:
    return (
        f"Stub draft for {stage}.\n\n"
        "A deterministic offline post, here only to prove the pipeline runs end to end. "
        "Run `--provider anthropic` for a real, in-voice draft.\n\n"
        "Ship the eval first."
    )


def _score_json(stage: str) -> str:
    lvl = _level_index(stage)
    dim_score = min(10, 5 + lvl)  # L0=5 … L5=10
    gates_clear = lvl >= 4  # hard gates only clear once specifics + eval are in
    gates = [
        {
            "name": n,
            "passed": True if n == "no_slop" else gates_clear,
            "reason": "stub: deterministic offline score",
        }
        for n in GATE_NAMES
    ]
    dims = [
        {"name": n, "score": dim_score, "reason": "stub: deterministic offline score"}
        for n in DIM_NAMES
    ]
    delta = "baseline" if lvl == 0 else f"stub progression to L{lvl}"
    return json.dumps({"gates": gates, "dimensions": dims, "delta_vs_prev": delta})


def _council_json() -> str:
    return json.dumps(
        {
            "critique": "stub: no real critique (offline provider)",
            "revised_draft": _draft_text("draft_L5"),
            "stop": True,
            "reason": "stub stops on the first pass",
        }
    )


class StubProvider(Provider):
    name = "stub"

    def complete(self, stage: str, prompt: str) -> str:
        if stage == "persona":
            return _PERSONA
        if stage.startswith("score_"):
            return _score_json(stage)
        if stage.startswith("council_pass"):
            return _council_json()
        if stage.startswith("draft_"):
            return _draft_text(stage)
        return f"[stub:{stage}]"
