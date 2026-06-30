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
    writing_for: str = ""
    goal: str = ""
    play_to: str = ""


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


def apply_audience_default(cfg: OnboardingConfig, audience) -> bool:
    """Fill an empty audience from the hardcoded default. Returns True if anything changed.

    Only fills blanks — a real answer the user gave always wins.
    """
    d = cfg.defaults.audience
    changed = False
    for field in ("writing_for", "goal", "play_to"):
        if not getattr(audience, field) and getattr(d, field):
            setattr(audience, field, getattr(d, field))
            changed = True
    return changed


def onboarding_summary(cfg: OnboardingConfig) -> str:
    """One-line health check for `tb doctor`."""
    qs = cfg.active()
    kinds = ", ".join(f"{q.id}:{q.type}" for q in qs)
    return f"onboarding ok: {len(qs)} question(s) [{kinds}]"
