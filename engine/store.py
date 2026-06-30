"""Local-first post storage — every approved post is a plain folder on your machine.

`posts/<date>-<slug>/` holds `final.md` (the post) and `post.json` (its metadata).
No database, no cloud, no account (V1 spec: local-first). The UI lists posts via
`list_posts()` or `bf posts --json`.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from .blocks.intake import Intake
from .config import POSTS_DIR
from .post import PostResult


def _slug(text: str, words: int = 5) -> str:
    clean = re.sub(r"[^a-z0-9\s-]", "", text.lower())
    return "-".join(clean.split()[:words]) or "post"


def save_post(result: PostResult, intake: Intake, date: str, base: Path = POSTS_DIR) -> Path:
    """Write the approved post + metadata to posts/<date>-<slug>/. Returns the folder."""
    pdir = base / f"{date}-{_slug(intake.idea.topic)}"
    pdir.mkdir(parents=True, exist_ok=True)
    (pdir / "final.md").write_text(result.final_draft, encoding="utf-8")
    meta = {
        "date": date,
        "topic": intake.idea.topic,
        "channels": intake.output.channels,
        "score": {
            "quality": result.score.quality_avg,
            "gates_passed": result.score.gates_passed,
            "gates_total": result.score.gates_total,
        },
        "open_gates": [g.name for g in result.score.gates if not g.passed],
        "receipts": result.proof,
    }
    (pdir / "post.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    return pdir


def list_posts(base: Path = POSTS_DIR) -> list[dict]:
    """Every saved post's metadata, newest folder name last. Empty if none yet."""
    if not base.exists():
        return []
    out: list[dict] = []
    for d in sorted(base.iterdir()):
        meta = d / "post.json"
        if meta.exists():
            out.append(json.loads(meta.read_text(encoding="utf-8")))
    return out
