"""Persona — extract the writing voice from HOW the person answered easy questions.

Recognition > description: people can't describe their voice but the model can read
it from raw, unpolished answers. The prompt forbids inventing traits not in evidence.
"""

from __future__ import annotations

import json
import re

from pydantic import BaseModel

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


def build_persona(intake: Intake, provider: Provider) -> str:
    md = provider.complete("persona", build_persona_prompt(intake)).strip() + "\n"
    PROFILES_DIR.mkdir(parents=True, exist_ok=True)
    (PROFILES_DIR / "persona.md").write_text(md, encoding="utf-8")
    return md


# --- persona insights: the reveal screen's "you said" receipts ---------------
# Each insight is an observation about the voice, grounded in a VERBATIM quote from
# what the person actually wrote. A code guard (below) drops any quote that isn't an
# exact span of their own words, so the reveal can never show an invented quote.


class Insight(BaseModel):
    observation: str  # what the voice does
    verbatim_quote: str  # an exact span of the person's own words
    trait_label: str  # short tag, e.g. "lowercase", "understated"


def voice_corpus(intake: Intake) -> list[str]:
    """The raw spans an insight is allowed to quote from — the person's own words."""
    v, t = intake.voice, intake.typed
    spans = list(v.answers.values())
    spans += [t.identity, t.known_for, t.background, t.beliefs, t.lessons, v.notes]
    return [s for s in spans if s and s.strip()]


def build_persona_insights_prompt(intake: Intake, max_insights: int) -> str:
    corpus = "\n\n".join(f"- {a}" for a in voice_corpus(intake)) or "(none)"
    return (
        f"Read how this person actually writes, below. Surface up to {max_insights} short "
        "insights about their VOICE (how they sound — not what they said).\n\n"
        "For each insight, you MUST include a verbatim_quote: an EXACT, word-for-word span "
        "copied from their words below (no paraphrasing, no fixing spelling/casing). If you "
        "cannot quote them exactly to support an insight, omit that insight. Never invent.\n\n"
        f"THEIR WORDS:\n{corpus}\n\n"
        'Return ONLY a JSON array: [{"observation":"...","verbatim_quote":"...",'
        '"trait_label":"one or two words"}]'
    )


def _parse_insight_array(raw: str) -> list[dict]:
    text = raw.strip()
    if "```" in text:
        text = re.sub(r"```(?:json)?", "", text).strip()
    start, end = text.find("["), text.rfind("]")
    if start == -1 or end == -1:
        raise ValueError("no JSON array found in insights completion")
    data = json.loads(text[start : end + 1])
    return [d for d in data if isinstance(d, dict)]


def _exact_span(quote: str, sources: list[str]) -> str | None:
    """Return the person's exact original substring matching `quote`, or None.

    Whitespace-tolerant and case-insensitive on the lookup, but returns the ORIGINAL
    text (their casing/punctuation) so the receipt is provably their own words.
    """
    q = quote.strip().strip("\"'“”‘’").strip()
    tokens = [re.escape(tok) for tok in re.split(r"\s+", q) if tok]
    if not tokens:
        return None
    rx = re.compile(r"\s+".join(tokens), re.IGNORECASE)
    for s in sources:
        m = rx.search(s)
        if m:
            return m.group(0)
    return None


def build_persona_insights(
    intake: Intake, provider: Provider, max_insights: int = 4
) -> list[Insight]:
    raw = provider.complete(
        "persona_insights", build_persona_insights_prompt(intake, max_insights)
    )
    sources = voice_corpus(intake)
    out: list[Insight] = []
    for item in _parse_insight_array(raw):
        span = _exact_span(str(item.get("verbatim_quote", "")), sources)
        if span is None:  # not an exact quote of their words — drop it
            continue
        out.append(
            Insight(
                observation=str(item.get("observation", "")).strip(),
                verbatim_quote=span,
                trait_label=str(item.get("trait_label", "")).strip(),
            )
        )
        if len(out) >= max_insights:
            break
    return out
