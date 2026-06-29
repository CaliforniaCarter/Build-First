"""The ablation ladder — the eval. Hold the idea constant, add one input tier at a
time, draft and score at each step, so each input's contribution is isolated.

Key design: the high-level TOPIC is known at every level, but the rich SPECIFICS
(scene, number, mechanism, only-you angle, proof) only enter at L4. That's what makes
the ladder show real progression instead of leaking the good stuff at L0.
"""
from __future__ import annotations

import json
from pathlib import Path

from .blocks import council
from .blocks import draft as draft_block
from .blocks import receipts as receipts_block
from .blocks.intake import Intake
from .config import LAYERS_DIR, RUNS_DIR
from .providers.base import Provider
from .rubric.schemas import LevelResult
from .rubric.shared import build_score_prompt, parse_score

LEVELS = [
    ("L0", "Online", "handles + public footprint only", ["online"]),
    ("L1", "+Docs", "résumé / credentials", ["online", "docs"]),
    ("L2", "+Typed", "identity, background, beliefs", ["online", "docs", "typed"]),
    ("L3", "+Persona", "the voice profile", ["online", "docs", "typed", "persona"]),
    ("L4", "+Specifics", "the concrete scene, real proof, mechanism",
     ["online", "docs", "typed", "persona", "specifics"]),
    ("L5", "+Eval pass", "Writer's Council to threshold",
     ["online", "docs", "typed", "persona", "specifics", "eval"]),
]


def load_layers() -> str:
    fmt = (LAYERS_DIR / "format.md").read_text(encoding="utf-8")
    aud = (LAYERS_DIR / "audience_tenex.md").read_text(encoding="utf-8")
    return f"{fmt}\n\n{aud}"


def context_for(inputs: list[str], intake: Intake) -> str:
    o, d, t, i = intake.online, intake.docs, intake.typed, intake.idea
    parts: list[str] = []

    if "online" in inputs:
        foot = [f"Name: {intake.name}"]
        if o.linkedin:
            foot.append(f"LinkedIn: {o.linkedin}")
        if o.x:
            foot.append(f"X: {o.x}")
        foot.append("Start: cold start, no existing posts" if o.cold_start else f"Existing: {o.existing_posts}")
        parts.append("PUBLIC FOOTPRINT:\n" + "\n".join(foot))

    if "docs" in inputs and d.resume:
        parts.append("RESUME:\n" + d.resume)

    if "typed" in inputs:
        typed = [s for s in (
            f"Identity: {t.identity}" if t.identity else "",
            f"Known for: {t.known_for}" if t.known_for else "",
            f"Background: {t.background}" if t.background else "",
            f"Beliefs: {t.beliefs}" if t.beliefs else "",
            f"Lessons: {t.lessons}" if t.lessons else "",
        ) if s]
        if typed:
            parts.append("ABOUT YOU:\n" + "\n".join(typed))

    if "specifics" in inputs:
        spec = [f"Topic: {i.topic}"]
        for label, val in (
            ("Take", i.take), ("How it works", i.mechanism), ("Scene", i.scene),
            ("Number", i.number), ("Lesson", i.lesson), ("Only-you", i.only_you),
            ("Close", i.close),
        ):
            if val:
                spec.append(f"{label}: {val}")
        if i.proof:
            spec.append("Proof: " + "; ".join(i.proof))
        parts.append("THE SPECIFIC WORK:\n" + "\n".join(spec))
    else:
        parts.append("THE TOPIC (high level only — no specifics yet):\n" + i.topic)

    return "\n\n".join(parts)


def run_ablation(intake: Intake, persona_md: str, provider: Provider, run_id: str) -> list[LevelResult]:
    layers = load_layers()
    run_dir = RUNS_DIR / run_id
    results: list[LevelResult] = []
    prev_draft: str | None = None

    for level, label, adds, inputs in LEVELS:
        ldir = run_dir / level
        ldir.mkdir(parents=True, exist_ok=True)
        persona = persona_md if "persona" in inputs else None

        if "eval" in inputs:
            base = results[-1].draft  # council revises the previous level's draft
            text, clog = council.revise(base, persona_md, layers, provider)
            (ldir / "council_log.json").write_text(json.dumps(clog, indent=2), encoding="utf-8")
        else:
            ctx = context_for(inputs, intake)
            prompt = draft_block.build_draft_prompt(
                intake.idea.topic, ctx, persona, layers,
                intake.output.hard_nevers, intake.output.channels,
            )
            text = draft_block.draft(f"draft_{level}", prompt, provider)

        text, proof, redactions = receipts_block.attach_receipts(text, intake)

        score_prompt = build_score_prompt(
            text, persona_md if persona else "(no persona at this level)", layers, prev_draft
        )
        score = parse_score(provider.complete(f"score_{level}", score_prompt))

        (ldir / "draft.md").write_text(text, encoding="utf-8")
        (ldir / "score.json").write_text(score.model_dump_json(indent=2), encoding="utf-8")
        if proof:
            (ldir / "receipts.json").write_text(
                json.dumps({"proof": proof, "redacted": redactions}, indent=2), encoding="utf-8"
            )

        results.append(LevelResult(
            level=level, label=label, adds=adds, inputs_active=inputs, draft=text, score=score
        ))
        prev_draft = text

    return results
