"""Takes — spiky opinions the user could post, for the home content-playground tile."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from engine.blocks.intake import Intake
from engine.providers.anthropic import AnthropicProvider
from engine.takes import form_takes

from ..deps import get_provider, read_persona, require_intake

router = APIRouter(prefix="/api/takes", tags=["takes"])


@router.get("")
def takes(
    intake: Intake = Depends(require_intake),
    provider: AnthropicProvider = Depends(get_provider),
) -> dict:
    return {"takes": form_takes(intake, read_persona() or "", provider)}
