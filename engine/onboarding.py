"""Onboarding scaffolding — the question flow lives in data, not code.

`engine/onboarding.json` is the single, hand-editable source of truth for onboarding:
the welcome line, the hardcoded audience default, and the ordered questions. The plugin
reads it to drive the conversation; the engine validates it (so a bad edit fails loudly,
not silently). Nothing here is invented — it only loads and validates what's in the file.
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import BaseModel

from .config import ONBOARDING_PATH

QuestionType = Literal["deterministic", "ab_pick", "adaptive"]


class ABOption(BaseModel):
    value: str  # the label stored into the voice field (e.g. "dry & deadpan")
    example: str  # a real little post the user picks between — never a bare label


class Question(BaseModel):
    id: str
    type: QuestionType
    order: float
    prompt: str | None = None  # null for `adaptive` — the LLM writes it
    purpose: str = ""  # plain-English why, so the flow stays self-documenting
    writes_to: str = ""  # dotted path into intake.json (e.g. "voice.answers.weekend")
    options: list[ABOption] = []  # for `ab_pick`
    based_on: str | None = None  # for `adaptive`: which prior answer it follows
    enabled: bool = True


class AudienceDefault(BaseModel):
    """The hardcoded audience — who you're writing for. Editable JSON; rendered to the draft layer."""

    writing_for: str = ""
    goal: str = ""
    play_to: str = ""
    tone_refs: list[str] = []  # reference voices to adapt MOVES from — never to imitate
    adapt_note: str = ""  # the clone-trap guard
    anatomy: list[str] = []  # the build-post shape
    playbook: list[str] = []  # what to optimize toward
    openers: list[str] = []  # real opener moves to adapt


class Defaults(BaseModel):
    audience: AudienceDefault = AudienceDefault()


class OnboardingConfig(BaseModel):
    welcome: str
    defaults: Defaults = Defaults()
    questions: list[Question] = []

    def active(self) -> list[Question]:
        """The enabled questions, in flow order — what the plugin actually asks."""
        return sorted((q for q in self.questions if q.enabled), key=lambda q: q.order)


def load_onboarding(path: Path | None = None) -> OnboardingConfig:
    p = path or ONBOARDING_PATH
    if not p.exists():
        raise FileNotFoundError(f"onboarding config not found at {p}")
    return OnboardingConfig.model_validate_json(p.read_text(encoding="utf-8"))


def render_audience(a: AudienceDefault) -> str:
    """Render the JSON audience to the prose 'audience layer' the draft pipeline reads.

    Same JSON-is-truth / prose-is-derived pattern as the voice profile. Empty fields are
    skipped, so trimming the JSON trims the briefing.
    """
    out: list[str] = ["# Audience layer", ""]
    lead = "Who you're writing for tilts topic and proof, not your voice."
    if a.writing_for:
        lead += f" Audience = {a.writing_for}."
    if a.tone_refs:
        lead += f" Tone modeled on {', '.join(a.tone_refs)}."
    if a.goal:
        lead += f" Goal: {a.goal}."
    out += [lead, ""]
    if a.play_to:
        out += [f"What they value: {a.play_to}.", ""]
    if a.adapt_note:
        out += [f"> **Adapt the move, don't copy the post.** {a.adapt_note}", ""]
    if a.anatomy:
        out += ["## The build-post anatomy", *[f"{i}. {s}" for i, s in enumerate(a.anatomy, 1)], ""]
    if a.playbook:
        out += ["## The playbook (optimize toward these)", *[f"- {s}" for s in a.playbook], ""]
    if a.openers:
        out += [
            "## Real openers (moves to adapt, not lines to copy)",
            *[f"- {s}" for s in a.openers],
            "",
        ]
    return "\n".join(out).rstrip() + "\n"


def onboarding_summary(cfg: OnboardingConfig) -> str:
    """One-line health check for `tb doctor`."""
    qs = cfg.active()
    kinds = ", ".join(f"{q.id}:{q.type}" for q in qs)
    return f"onboarding ok: {len(qs)} question(s) [{kinds}]"
