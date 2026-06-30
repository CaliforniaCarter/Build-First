"""Intake — the single source of truth assembled across the onboarding screens."""

from __future__ import annotations

from fastapi import APIRouter, Body, HTTPException
from pydantic import ValidationError

from engine.blocks.intake import Intake

from ..deps import deep_merge, empty_intake, read_intake, write_intake

router = APIRouter(prefix="/api/intake", tags=["intake"])


@router.get("")
def get_intake() -> Intake:
    return read_intake() or empty_intake()


@router.put("")
def put_intake(intake: Intake) -> dict:
    write_intake(intake)
    return {"ok": True, "intake": intake.model_dump()}


@router.patch("")
def patch_intake(patch: dict = Body(...)) -> dict:
    """Deep-merge a partial intake onto the saved one — onboarding autosave."""
    current = (read_intake() or empty_intake()).model_dump()
    merged = deep_merge(current, patch)
    try:
        intake = Intake.model_validate(merged)
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=exc.errors()) from exc
    write_intake(intake)
    return {"ok": True, "intake": intake.model_dump()}
