"""Intake — load and validate the user's inputs (the onboarding answers).

The real file (`data/intake.json`) is personal and gitignored. `intake.example.json` shows the
blank shape; `intake.sample.json` is a filled synthetic example used as the cold-start fallback.
Nothing here is invented: every field is something the user gave.
"""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel

from ..config import DATA_DIR


class ContentIdea(BaseModel):
    topic: str
    take: str = ""
    scene: str = ""
    number: str = ""  # leave blank if no real number was given
    lesson: str = ""
    only_you: str = ""
    mechanism: str = ""  # how it actually works (real specifics)
    proof: list[str] = []  # receipts to attach / cite
    close: str = ""


class Online(BaseModel):
    linkedin: str = ""
    x: str = ""
    other: str = ""
    existing_posts: str = ""
    cold_start: bool = True


class Docs(BaseModel):
    resume: str = ""  # plain text
    portfolio: str = ""


class Typed(BaseModel):
    identity: str = ""
    known_for: str = ""
    background: str = ""
    beliefs: str = ""
    lessons: str = ""


class Voice(BaseModel):
    answers: dict[str, str] = {}  # question -> raw, unpolished answer
    # real work you're proud of (essays, chats, posts) — the strongest voice corpus
    writing_samples: list[str] = []
    tone_words: list[str] = []
    look: str = ""
    sentence_length: str = ""
    banned: list[str] = []
    signatures: list[str] = []
    emojis: str = ""  # e.g. "none"
    humor: str = ""  # the onboarding A/B pick, e.g. "dry & deadpan"
    shape: str = ""  # the onboarding A/B pick, e.g. "short & punchy"
    notes: str = ""


class Audience(BaseModel):
    writing_for: str = ""
    goal: str = ""
    play_to: str = ""


class OutputPrefs(BaseModel):
    channels: list[str] = ["LinkedIn"]
    length: str = ""
    format: str = ""
    hard_nevers: list[str] = []
    off_limits: str = ""


class Intake(BaseModel):
    name: str
    idea: ContentIdea
    online: Online = Online()
    docs: Docs = Docs()
    typed: Typed = Typed()
    voice: Voice = Voice()
    audience: Audience = Audience()
    output: OutputPrefs = OutputPrefs()


def load_intake(path: Path | None = None) -> Intake:
    if path is None:
        # Personal intake.json wins if present; otherwise fall back to the committed
        # synthetic sample so a fresh checkout runs cold with no setup.
        primary = DATA_DIR / "intake.json"
        path = primary if primary.exists() else (DATA_DIR / "intake.sample.json")
    if not path.exists():
        raise FileNotFoundError(f"intake not found at {path} — see data/intake.example.json")
    return Intake.model_validate_json(path.read_text(encoding="utf-8"))
