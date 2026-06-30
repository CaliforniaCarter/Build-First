"""Posts store — a single local JSON file (data/posts.json). One user, no DB.

Source of truth for the feed/home screens. Each record is a generated post plus its
real eval score, proof, and council log.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from uuid import uuid4

from engine.config import DATA_DIR

POSTS_PATH = DATA_DIR / "posts.json"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load() -> list[dict]:
    if not POSTS_PATH.exists():
        return []
    return json.loads(POSTS_PATH.read_text(encoding="utf-8") or "[]")


def _save(posts: list[dict]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    POSTS_PATH.write_text(json.dumps(posts, indent=2), encoding="utf-8")


def new_record(
    body: str,
    score: dict,
    proof: list[str],
    redactions: list[str],
    council_log: list[dict],
    topic: str,
) -> dict:
    now = _now()
    return {
        "id": uuid4().hex[:12],
        "body": body,
        "score": score,
        "proof": proof,
        "redactions": redactions,
        "council_log": council_log,
        "status": "draft",
        "topic": topic,
        "created_at": now,
        "updated_at": now,
    }


def list_posts(status: str | None = None) -> list[dict]:
    posts = _load()
    if status:
        posts = [p for p in posts if p.get("status") == status]
    return sorted(posts, key=lambda p: p.get("created_at", ""), reverse=True)


def get_post(post_id: str) -> dict | None:
    return next((p for p in _load() if p.get("id") == post_id), None)


def add_post(record: dict) -> dict:
    posts = _load()
    posts.append(record)
    _save(posts)
    return record


def update_post(post_id: str, **fields) -> dict | None:
    posts = _load()
    for p in posts:
        if p.get("id") == post_id:
            p.update(fields)
            p["updated_at"] = _now()
            _save(posts)
            return p
    return None
