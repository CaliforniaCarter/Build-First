"""Persona — the voice profile (persona.md) and the reveal-screen insights."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from engine.blocks.intake import Intake
from engine.blocks.persona import build_persona, build_persona_insights
from engine.providers.anthropic import AnthropicProvider

from ..deps import get_provider, require_intake

router = APIRouter(prefix="/api/persona", tags=["persona"])


@router.post("/build")
def build(
    intake: Intake = Depends(require_intake),
    provider: AnthropicProvider = Depends(get_provider),
) -> dict:
    return {"persona_md": build_persona(intake, provider)}


@router.post("/insights")
def insights(
    intake: Intake = Depends(require_intake),
    provider: AnthropicProvider = Depends(get_provider),
) -> dict:
    items = build_persona_insights(intake, provider)
    return {"insights": [i.model_dump() for i in items]}
