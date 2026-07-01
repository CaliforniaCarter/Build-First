"""The local intake server — serves the branded page + a tiny JSON API. No model calls.

Routes:
  GET  /                     → the intake page (static)
  GET  /api/onboarding       → welcome + the DETERMINISTIC questions (from onboarding.json)
  POST /api/intake/begin     → reset data/intake.json to a blank shape (fresh start)
  PATCH /api/intake          → save a batch of {writes_to: value} answers
  POST /api/intake/resume    → upload a résumé (PDF/txt) → docs.resume  (paste also works)
  POST /api/intake/complete  → mark done; signals the `tb welcome` launcher to stop and continue
  GET  /api/health           → {"ok": true}
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import FastAPI, Request, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from engine.onboarding import load_onboarding

from . import intake as intake_store

STATIC = Path(__file__).resolve().parent / "static"


class IntakePatch(BaseModel):
    answers: dict[str, Any]


def create_app() -> FastAPI:
    app = FastAPI(title="Timbre intake", version="0.1.0")

    @app.get("/api/health")
    async def health() -> dict[str, bool]:
        return {"ok": True}

    @app.get("/api/onboarding")
    async def onboarding() -> dict[str, Any]:
        cfg = load_onboarding()
        questions = [
            {
                "id": q.id,
                "type": q.type,
                "prompt": q.prompt or "",
                "subtext": q.subtext,
                "purpose": q.purpose,
                "writes_to": q.writes_to,
                "order": q.order,
                # writing_samples is the only optional/skippable question
                "required": q.id != "writing_samples",
            }
            for q in cfg.active()
            if q.type == "deterministic"
        ]
        return {"welcome": cfg.welcome, "questions": questions}

    @app.post("/api/intake/begin")
    async def begin() -> dict[str, bool]:
        intake_store.begin()
        return {"ok": True}

    @app.patch("/api/intake")
    async def patch_intake(body: IntakePatch) -> dict[str, bool]:
        intake_store.apply_answers(body.answers)
        return {"ok": True}

    @app.post("/api/intake/resume")
    async def upload_resume(file: UploadFile) -> dict[str, Any]:
        raw = await file.read()
        name = (file.filename or "").lower()
        if name.endswith(".pdf"):
            text = intake_store.extract_pdf_text(raw)
        else:
            text = raw.decode("utf-8", errors="ignore").strip()
        if text:
            intake_store.set_resume(text)
        return {"ok": bool(text), "chars": len(text)}

    @app.post("/api/intake/writing-sample")
    async def upload_sample(file: UploadFile) -> dict[str, Any]:
        # Parse a post/essay file and return its text; the client folds it into
        # voice.writing_samples alongside any pasted text (no server-side write here).
        raw = await file.read()
        name = (file.filename or "").lower()
        if name.endswith(".pdf"):
            text = intake_store.extract_pdf_text(raw)
        else:
            text = raw.decode("utf-8", errors="ignore").strip()
        return {"ok": bool(text), "text": text, "chars": len(text)}

    @app.post("/api/intake/complete")
    async def complete(request: Request) -> dict[str, bool]:
        # Stop the `tb welcome` launcher so the terminal flow auto-continues.
        server = getattr(request.app.state, "server", None)
        if server is not None:
            server.should_exit = True
        return {"ok": True}

    @app.get("/")
    async def index() -> FileResponse:
        return FileResponse(STATIC / "index.html")

    app.mount("/static", StaticFiles(directory=STATIC), name="static")
    return app


app = create_app()
