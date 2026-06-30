"""Compose — turn 'what you did' into in-voice, scored, receipt-backed posts.

Three shapes:
- POST ""         one post (fast path, used by the simple compose screen).
- POST "/options" TWO options in different shapes to pick between (no council yet).
- POST "/pick"    polish the chosen option (Writer's Council), save it, and log the choice
                  as a token-free learning signal.
"""

from __future__ import annotations

from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException

from engine import signals
from engine.blocks.intake import Intake
from engine.compose import compose_post
from engine.post import make_options, polish
from engine.providers.anthropic import AnthropicProvider

from .. import store
from ..deps import get_provider, require_intake, require_persona
from ..schemas import ComposeRequest, OptionsRequest, PickRequest, serialize_score

router = APIRouter(prefix="/api/compose", tags=["compose"])


def _with_topic(intake: Intake, work: str) -> Intake:
    """Fold 'what you did' into the idea topic without mutating the stored intake."""
    return intake.model_copy(update={"idea": intake.idea.model_copy(update={"topic": work})})


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


@router.post("/options")
def options(
    req: OptionsRequest,
    intake: Intake = Depends(require_intake),
    persona_md: str = Depends(require_persona),
    provider: AnthropicProvider = Depends(get_provider),
) -> dict:
    if not req.work.strip():
        raise HTTPException(status_code=400, detail="tell me what you did first — even one line")
    openings = [
        p["body"].splitlines()[0]
        for p in store.list_posts()[:2]
        if p.get("body", "").strip()
    ]
    results = make_options(
        _with_topic(intake, req.work), persona_md, provider, uuid4().hex[:12],
        recent_openings=openings,
    )
    return {
        "options": [
            {"body": r.final_draft, "score": serialize_score(r.score), "proof": r.proof}
            for r in results
        ]
    }


@router.post("/pick")
def pick(
    req: PickRequest,
    intake: Intake = Depends(require_intake),
    persona_md: str = Depends(require_persona),
    provider: AnthropicProvider = Depends(get_provider),
) -> dict:
    if not req.chosen.strip():
        raise HTTPException(status_code=400, detail="pick one of the options first")
    result = polish(req.chosen, intake, persona_md, provider)
    record = store.new_record(
        body=result.final_draft,
        score=serialize_score(result.score),
        proof=result.proof,
        redactions=result.redactions,
        council_log=result.council_log,
        topic=req.topic,
    )
    store.add_post(record)
    # Log the A-vs-B choice token-free; POST /api/learn folds it in later.
    signals.record_signal(
        "pick",
        {
            "chosen_opening": req.chosen.strip().splitlines()[0],
            "rejected_opening": req.rejected_opening,
            "why": req.why,
        },
    )
    return {"post": record}
