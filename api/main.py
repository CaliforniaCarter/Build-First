"""Timbre API entrypoint.

load_dotenv() runs FIRST — the engine reads ANTHROPIC_API_KEY straight from os.environ
and never loads .env itself, so the API must. Run:
  uv run python -m uvicorn api.main:app --reload --port 8000
"""

from __future__ import annotations

from dotenv import load_dotenv

load_dotenv()  # before anything reads os.environ

from fastapi import FastAPI  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402

from .routers import (  # noqa: E402
    compose,
    intake,
    learn,
    online,
    persona,
    posts,
    profile,
    takes,
)

app = FastAPI(title="Timbre API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1):3000",
    allow_methods=["*"],
    allow_headers=["*"],
)

for module in (intake, online, profile, persona, compose, posts, learn, takes):
    app.include_router(module.router)


@app.get("/api/health")
def health() -> dict:
    return {"ok": True}
