"""Compose — turn 'what you did' into one in-voice, scored, receipt-backed post."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from engine.blocks.intake import Intake
from engine.compose import compose_post
from engine.providers.anthropic import AnthropicProvider

from .. import store
from ..deps import get_provider, require_intake, require_persona
from ..schemas import ComposeRequest, serialize_score

router = APIRouter(prefix="/api/compose", tags=["compose"])


@router.post("")
def compose(
    req: ComposeRequest,
    intake: Intake = Depends(require_intake),
    persona_md: str = Depends(require_persona),
    provider: AnthropicProvider = Depends(get_provider),
) -> dict:
    if not req.work.strip():
        raise HTTPException(status_code=400, detail="tell me what you did first — even one line")

    result = compose_post(intake, req.work, persona_md, provider)
    record = store.new_record(
        body=result.body,
        score=serialize_score(result.score),
        proof=result.proof,
        redactions=result.redactions,
        council_log=result.council_log,
        topic=req.work,
    )
    if req.save:
        store.add_post(record)
    return {"post": record}
