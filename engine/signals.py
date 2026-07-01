"""Learning signals — a token-free log of the picks and edits the profile learns from.

Every pick (you chose option A over B, maybe with a why) and every edit is recorded here
as plain text, with NO AI call — so most interactions cost zero tokens. The learning loop
(engine/learn.py) reads the pending batch on demand, makes ONE call to update the profile
in place, and marks them processed. Learning fires occasionally over a tiny batch, never
per keystroke. The profile is the long-term memory; this log is capped.
"""

from __future__ import annotations

import json
from pathlib import Path

from .config import DATA_DIR

SIGNALS_PATH = DATA_DIR / "signals.json"
CAP = 30  # keep only the most recent signals — the profile is the durable memory


def _load(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def _save(sigs: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(sigs[-CAP:], indent=2) + "\n", encoding="utf-8")


def record_signal(kind: str, data: dict, path: Path = SIGNALS_PATH) -> None:
    """Append a signal (kind 'pick' | 'edit'). No AI — this is free."""
    sigs = _load(path)
    sigs.append({"kind": kind, "processed": False, **data})
    _save(sigs, path)


def pending_signals(path: Path = SIGNALS_PATH) -> list[dict]:
    """Signals not yet folded into the profile."""
    return [s for s in _load(path) if not s.get("processed")]


def mark_processed(path: Path = SIGNALS_PATH) -> None:
    """Mark every signal as folded in, so the next learn pass starts clean."""
    sigs = _load(path)
    for s in sigs:
        s["processed"] = True
    if sigs:
        _save(sigs, path)
