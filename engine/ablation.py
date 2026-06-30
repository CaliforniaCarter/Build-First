"""The ablation ladder — the eval. Hold the idea constant, add one input tier at a
time, draft and score at each step, so each input's contribution is isolated.

Key design: the high-level TOPIC is known at every level, but the rich SPECIFICS
(scene, number, mechanism, only-you angle, proof) only enter at L4. That's what makes
the ladder show real progression instead of leaking the good stuff at L0.
"""

from __future__ import annotations

import json

from .blocks import council
from .blocks import draft as draft_block
from .blocks import receipts as receipts_block
from .blocks.intake import Intake
from .blocks.persona import extract_voice
from .config import LABS_PATH, LAYERS_DIR, RUNS_DIR
from .onboarding import load_onboarding, render_audience
from .providers.base import Provider
from .rubric.schemas import LevelResult
from .rubric.shared import build_score_prompt, parse_score


def load_ladder() -> list[tuple[str, str, str, list[str]]]:
    """The ablation ladder, from editable JSON (engine/labs.json) — add/reorder a tier, no code."""
    data = json.loads(LABS_PATH.read_text(encoding="utf-8"))
    return [(t["level"], t["label"], t["adds"], list(t["inputs"])) for t in data["ladder"]]


def load_layers() -> str:
    """Format layer (a file) + the audience layer, rendered from the editable JSON in
    onboarding.json (single source of truth — see engine/onboarding.json `defaults.audience`)."""
    fmt = (LAYERS_DIR / "format.md").read_text(encoding="utf-8")
    aud = render_audience(load_onboarding().defaults.audience)
    return f"{fmt}\n\n{aud}"


def context_for(inputs: list[str], intake: Intake) -> str:
    o, d, t, i = intake.online, intake.docs, intake.typed, intake.idea
    parts: list[str] = []

    if "online" in inputs:
        # The raw handles are footprint, not draft material — a leave-one-out showed they add
        # nothing to a draft (+0.0), so they stay in the intake (receipts + grounding use them)
        # but don't enter the draft context. Only the posting-history framing carries signal.
        foot = [f"Name: {intake.name}"]
        foot.append(
            "Start: cold start, no existing posts"
            if o.cold_start
            else f"Existing: {o.existing_posts}"
        )
        parts.append("PUBLIC FOOTPRINT:\n" + "\n".join(foot))

    if "docs" in inputs and d.resume:
        parts.append("RESUME:\n" + d.resume)

    if "typed" in inputs:
        typed = [
            s
            for s in (
                f"Identity: {t.identity}" if t.identity else "",
                f"Background: {t.background}" if t.background else "",
                f"Beliefs: {t.beliefs}" if t.beliefs else "",
                f"Lessons: {t.lessons}" if t.lessons else "",
            )
            if s
        ]
        if typed:
            parts.append("ABOUT YOU:\n" + "\n".join(typed))

    if "specifics" in inputs:
        spec = [f"Topic: {i.topic}"]
        for label, val in (
            ("Take", i.take),
            ("How it works", i.mechanism),
            ("Scene", i.scene),
            ("Number", i.number),
            ("Lesson", i.lesson),
            ("Only-you", i.only_you),
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


def run_ablation(
    intake: Intake, persona_md: str, provider: Provider, run_id: str
) -> list[LevelResult]:
    layers = load_layers()
    run_dir = RUNS_DIR / run_id
    results: list[LevelResult] = []
    prev_draft: str | None = None

    for level, label, adds, inputs in load_ladder():
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
                intake.idea.topic,
                ctx,
                persona,
                layers,
                intake.output.hard_nevers,
                intake.output.channels,
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

        results.append(
            LevelResult(
                level=level, label=label, adds=adds, inputs_active=inputs, draft=text, score=score
            )
        )
        prev_draft = text

    return results


# --- field-level ablation: prove what EACH field is worth, not just each tier ----------------
# Leave-one-out: hold everything constant, drop one field, re-draft + re-score, measure the
# loss. A positive contribution means the field earns its place. Fields are auto-discovered
# from the intake, so adding a field to the schema makes it ablatable for free.

_FULL_INPUTS = ["online", "docs", "typed", "persona", "specifics"]
_ABLATE_SECTIONS = ("idea", "typed", "docs", "online")
# Skip the topic (the seed of the post) and the raw handles (footprint, not draft material — a
# leave-one-out showed +0.0, so they no longer enter the draft context).
_ABLATE_SKIP = {"idea.topic", "online.linkedin", "online.x"}


def ablatable_fields(intake: Intake) -> list[str]:
    """Every populated content field worth ablating (idea/typed/docs/online), as dotted paths.
    Auto-discovered from the intake — add a field to the schema and it shows up here for free.
    Skips the topic (the seed), boolean flags, and empty fields (nothing to drop)."""
    out: list[str] = []
    for sec in _ABLATE_SECTIONS:
        for field, val in getattr(intake, sec).model_dump().items():
            path = f"{sec}.{field}"
            if path in _ABLATE_SKIP or isinstance(val, bool) or val in ("", [], {}, None):
                continue
            out.append(path)
    return out


def _clear_field(intake: Intake, path: str) -> None:
    sec, attr = path.split(".", 1)
    obj = getattr(intake, sec)
    cur = getattr(obj, attr)
    setattr(obj, attr, [] if isinstance(cur, list) else {} if isinstance(cur, dict) else "")


def _draft_score(
    intake: Intake, persona_md: str, layers: str, provider: Provider, stage: str
) -> float:
    """One draft + one score with all inputs (no council) — the unit the field ablation compares."""
    ctx = context_for(_FULL_INPUTS, intake)
    prompt = draft_block.build_draft_prompt(
        intake.idea.topic,
        ctx,
        persona_md,
        layers,
        intake.output.hard_nevers,
        intake.output.channels,
    )
    text = draft_block.draft(stage, prompt, provider)
    text, _proof, _red = receipts_block.attach_receipts(text, intake)
    score = parse_score(
        provider.complete(f"score_{stage}", build_score_prompt(text, persona_md, layers, None))
    )
    return score.quality_avg


def run_field_ablation(intake: Intake, persona_md: str, provider: Provider, run_id: str):
    """Leave-one-out over every field. Returns (baseline_score, [{field, score_without,
    contribution}]) sorted by contribution (most valuable field first)."""
    layers = load_layers()
    baseline = _draft_score(intake, persona_md, layers, provider, "ablate_field_baseline")
    results = []
    for path in ablatable_fields(intake):
        trimmed = intake.model_copy(deep=True)
        _clear_field(trimmed, path)
        without = _draft_score(
            trimmed, persona_md, layers, provider, "ablate_field_" + path.replace(".", "_")
        )
        results.append(
            {"field": path, "score_without": without, "contribution": round(baseline - without, 1)}
        )
    results.sort(key=lambda r: r["contribution"], reverse=True)
    return baseline, results


# --- persona-level ablation: prove what each VOICE input is worth ------------------------------
# The sibling of the field ablation. The context fields above feed the DRAFT directly; the voice
# corpus (writing samples, answers, the A/B pick) feeds the PERSONA instead — so to test it we
# drop one voice input, RE-EXTRACT the persona from what's left, then redraft + rescore. Context
# is held constant, so any change traces to that one voice input.


def ablatable_voice_fields(intake: Intake) -> list[str]:
    """Every populated voice-corpus field (feeds the persona, not the draft), as dotted paths.
    Auto-discovered from the intake — add a voice input and it's tested here for free."""
    out: list[str] = []
    for field, val in intake.voice.model_dump().items():
        if val in ("", [], {}, None):
            continue
        out.append(f"voice.{field}")
    return out


def run_persona_ablation(intake: Intake, provider: Provider, run_id: str):
    """Leave-one-out over the voice corpus. Drop one voice input, re-extract the persona, redraft
    + rescore, measure the loss. Returns (baseline_score, [{field, score_without, contribution}])
    sorted by contribution (most valuable voice input first)."""
    layers = load_layers()
    base_persona = extract_voice(intake, provider, "ablate_persona_extract_baseline")
    baseline = _draft_score(intake, base_persona, layers, provider, "ablate_persona_baseline")
    results = []
    for path in ablatable_voice_fields(intake):
        trimmed = intake.model_copy(deep=True)
        _clear_field(trimmed, path)
        tag = path.replace(".", "_")
        persona = extract_voice(trimmed, provider, "ablate_persona_extract_" + tag)
        without = _draft_score(trimmed, persona, layers, provider, "ablate_persona_" + tag)
        results.append(
            {"field": path, "score_without": without, "contribution": round(baseline - without, 1)}
        )
    results.sort(key=lambda r: r["contribution"], reverse=True)
    return baseline, results
