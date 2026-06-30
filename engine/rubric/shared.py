"""The shared rubric: the same grading sheet the eval and the council both use.

Framing borrowed from Tenex's 5-stage eval framework: must-contain (the hard
gates) + must-not-contain (the slop list) + an LLM-as-judge rubric calibrated to
one human (Carter corrects the scores each morning, which tunes the weights).
"""

from __future__ import annotations

import json
import re

from ..blocks.proof import load_proof_config
from .schemas import DIM_DESCRIPTIONS, DIM_NAMES, GATE_DESCRIPTIONS, GATE_NAMES, Score


def rubric_text() -> str:
    gates = "\n".join(f"  - {n}: {GATE_DESCRIPTIONS[n]}" for n in GATE_NAMES)
    dims = "\n".join(f"  - {n}: {DIM_DESCRIPTIONS[n]}" for n in DIM_NAMES)
    slop = load_proof_config().slop_phrases  # single source: engine/proof.json
    return (
        "HARD GATES (pass/fail, each needs a one-line reason):\n"
        f"{gates}\n\n"
        "QUALITY DIMENSIONS (score 0-10, each with a one-line reason):\n"
        f"{dims}\n\n"
        "BANNED SLOP PHRASES (presence fails no_slop):\n"
        f"  {', '.join(slop)}"
    )


def build_score_prompt(draft: str, persona_md: str, layers: str, prev_draft: str | None) -> str:
    prev = f"\nPREVIOUS LEVEL'S DRAFT (for the delta):\n{prev_draft}\n" if prev_draft else ""
    return (
        "You are the eval. Score the DRAFT below against the rubric. Be a tough, "
        "honest judge calibrated to one human's taste. Reasons must be one line.\n\n"
        f"{rubric_text()}\n\n"
        "PERSONA (judge voice_match against this):\n"
        f"{persona_md}\n\n"
        "LAYERS (judge format_adherence and audience_fit against these):\n"
        f"{layers}\n"
        f"{prev}\n"
        "DRAFT:\n"
        f"{draft}\n\n"
        "Return ONLY JSON with this shape — include EVERY gate and EVERY dimension, "
        "using these exact names:\n"
        f"  gates ({len(GATE_NAMES)}): {', '.join(GATE_NAMES)}\n"
        f"  dimensions ({len(DIM_NAMES)}): {', '.join(DIM_NAMES)}\n"
        '{"gates":[{"name":..., "passed":true|false, "reason":...}, ... all '
        f"{len(GATE_NAMES)} gates],\n"
        '  "dimensions":[{"name":..., "score":0-10, "reason":...}, ... all '
        f"{len(DIM_NAMES)} dimensions],\n"
        '  "delta_vs_prev":"one line on what changed vs the previous level (\\"baseline\\" for L0)"}'
    )


def parse_score(raw: str) -> Score:
    """Pull the JSON object out of a completion and validate it."""
    text = raw.strip()
    if "```" in text:
        text = re.sub(r"```(?:json)?", "", text).strip()
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("no JSON object found in score completion")
    return Score.model_validate(json.loads(text[start : end + 1]))
