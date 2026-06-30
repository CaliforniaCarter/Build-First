"""Shared dependencies: intake load/save, the live provider, small helpers."""

from __future__ import annotations

from fastapi import HTTPException

from engine.blocks.intake import ContentIdea, Intake
from engine.config import DATA_DIR, PROFILES_DIR
from engine.providers.anthropic import AnthropicProvider

INTAKE_PATH = DATA_DIR / "intake.json"


def empty_intake() -> Intake:
    """A blank-but-valid intake — name/topic are empty strings, everything else default."""
    return Intake(name="", idea=ContentIdea(topic=""))


def read_intake() -> Intake | None:
    if not INTAKE_PATH.exists():
        return None
    return Intake.model_validate_json(INTAKE_PATH.read_text(encoding="utf-8"))


def write_intake(intake: Intake) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    INTAKE_PATH.write_text(intake.model_dump_json(indent=2), encoding="utf-8")


def require_intake() -> Intake:
    intake = read_intake()
    if intake is None:
        raise HTTPException(status_code=409, detail="no intake yet — start onboarding first")
    return intake


def read_persona() -> str | None:
    path = PROFILES_DIR / "persona.md"
    return path.read_text(encoding="utf-8") if path.exists() else None


def require_persona() -> str:
    persona = read_persona()
    if persona is None:
        raise HTTPException(status_code=409, detail="no persona yet — finish onboarding first")
    return persona


def get_provider() -> AnthropicProvider:
    """A fresh live provider per request (reads the key at call time)."""
    return AnthropicProvider()


def deep_merge(base: dict, patch: dict) -> dict:
    """Recursively merge `patch` onto `base`; lists and scalars overwrite."""
    out = dict(base)
    for key, value in patch.items():
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = deep_merge(out[key], value)
        else:
            out[key] = value
    return out
