"""Learn — fold the pending picks + edits into the voice profile, in one call (anti-bloat)."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from engine import signals
from engine.blocks.intake import Intake
from engine.config import DATA_DIR
from engine.learn import learn
from engine.providers.anthropic import AnthropicProvider

from ..deps import get_provider, require_intake

router = APIRouter(prefix="/api/learn", tags=["learn"])


@router.post("")
def learn_now(
    intake: Intake = Depends(require_intake),
    provider: AnthropicProvider = Depends(get_provider),
) -> dict:
    batch = signals.pending_signals()
    if not batch:
        return {"applied": [], "skipped": [], "folded": 0}
    applied, skipped = learn(batch, intake, provider)
    if applied:
        (DATA_DIR / "intake.json").write_text(
            intake.model_dump_json(indent=2) + "\n", encoding="utf-8"
        )
    signals.mark_processed()
    return {"applied": applied, "skipped": skipped, "folded": len(batch)}
