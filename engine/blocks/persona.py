"""Persona — extract the writing voice from HOW the person answered easy questions.

Recognition > description: people can't describe their voice but the model can read
it from raw, unpolished answers. The prompt forbids inventing traits not in evidence.
"""

from __future__ import annotations

from ..config import PROFILES_DIR
from ..providers.base import Provider
from .intake import Intake


def build_persona_prompt(intake: Intake) -> str:
    v = intake.voice
    answers = "\n\n".join(f"Q: {q}\nA: {a}" for q, a in v.answers.items()) or "(none)"
    return (
        "Extract this person's writing VOICE from how they answered below. Read HOW they "
        "write, not what they say. Do NOT invent traits that aren't in evidence. Tag each "
        "trait with a confidence label: HARD RULE / STRONG TENDENCY / LIGHT PREFERENCE.\n\n"
        f"RAW ANSWERS (unpolished, may be voice-to-text):\n{answers}\n\n"
        f"Tone words they picked: {', '.join(v.tone_words) or '—'}\n"
        f"Look: {v.look or '—'}\n"
        f"Sentence length: {v.sentence_length or '—'}\n"
        f"Emojis: {v.emojis or '—'}\n"
        f"Banned: {', '.join(v.banned) or '—'}\n"
        f"Signature phrases: {', '.join(v.signatures) or '—'}\n"
        f"Notes: {v.notes or '—'}\n\n"
        "Write persona.md with these sections:\n"
        "- Voice signature (3-5 words)\n"
        "- Vocabulary & how technical (and the no-jargon rule)\n"
        "- Sentence style\n"
        "- Favorite words/phrases\n"
        "- BANNED words/phrases\n"
        "- Punctuation & formatting\n"
        "- Humor\n"
        "- Structural habits (open / develop / close)\n"
        "- NEVER-DO list\n"
        "- Signature / verbatim phrases\n"
        "- Anti-overfitting labels\n\n"
        "Output ONLY the markdown."
    )


def build_persona(intake: Intake, provider: Provider, force: bool = False) -> str:
    """Build persona.md from the intake. If it already exists, keep it — your hand-edit is the
    confirmation — unless force=True (an explicit `tb onboard`)."""
    path = PROFILES_DIR / "persona.md"
    if path.exists() and not force:
        return path.read_text(encoding="utf-8")
    md = provider.complete("persona", build_persona_prompt(intake)).strip() + "\n"
    PROFILES_DIR.mkdir(parents=True, exist_ok=True)
    path.write_text(md, encoding="utf-8")
    return md
