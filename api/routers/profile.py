"""Profile docs — deterministic profile.md + context.md, and the docs reader/writer."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from engine.blocks.intake import Intake
from engine.blocks.profile import build_context, build_profile, write_profile_docs
from engine.config import PROFILES_DIR

from ..deps import require_intake
from ..schemas import PersonaMdBody

router = APIRouter(prefix="/api/profile", tags=["profile"])


def _read(name: str) -> str:
    path = PROFILES_DIR / name
    return path.read_text(encoding="utf-8") if path.exists() else ""


@router.post("/build")
def build(intake: Intake = Depends(require_intake)) -> dict:
    write_profile_docs(intake)  # persists profile.md + context.md
    return {"profile_md": build_profile(intake), "context_md": build_context(intake)}


@router.get("/docs")
def docs() -> dict:
    return {
        "persona_md": _read("persona.md"),
        "profile_md": _read("profile.md"),
        "context_md": _read("context.md"),
    }


@router.put("/docs")
def put_docs(body: PersonaMdBody) -> dict:
    PROFILES_DIR.mkdir(parents=True, exist_ok=True)
    (PROFILES_DIR / "persona.md").write_text(body.persona_md, encoding="utf-8")
    return {"ok": True}
