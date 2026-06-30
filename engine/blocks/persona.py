"""Persona / Voice — extract the writing VOICE from HOW the person answered easy questions.

Recognition > description: people can't describe their voice but the model can read it from
raw, unpolished answers. The extracted profile is stored as plain, hand-editable JSON
(`profiles/voice.json`) — your edit IS the confirmation — and rendered to prose only when the
drafting pipeline needs it. The prompt forbids inventing traits not in evidence.
"""

from __future__ import annotations

import json
import re

from pydantic import BaseModel

from ..config import PROFILES_DIR
from ..providers.base import Provider
from .intake import Intake

VOICE_PATH = PROFILES_DIR / "voice.json"


class VoiceProfile(BaseModel):
    """The editable voice profile. Each field maps to a section of the prose the model reads."""

    signature: str = ""  # 3-5 words
    vocabulary: str = ""  # how technical + the no-jargon rule
    sentence_style: str = ""
    favorite_phrases: list[str] = []
    banned: list[str] = []
    punctuation: str = ""
    humor: str = ""
    structure: str = ""  # open / develop / close habits
    never_do: list[str] = []
    signatures: list[str] = []
    notes: str = ""  # anti-overfitting / confidence labels


def build_voice_prompt(intake: Intake) -> str:
    v = intake.voice
    answers = "\n\n".join(f"Q: {q}\nA: {a}" for q, a in v.answers.items()) or "(none)"
    samples = "\n\n---\n\n".join(v.writing_samples) or "(none)"
    return (
        "Extract this person's writing VOICE from the material below. Read HOW they write, "
        "not what they say. Do NOT invent traits that aren't in evidence. In `notes`, tag "
        "uncertain traits with a confidence label: HARD RULE / STRONG TENDENCY / LIGHT "
        "PREFERENCE. Write every field in the SECOND PERSON ('you open on...', 'your "
        "sentences...') and stay gender-neutral — never use he/she/him/her.\n\n"
        f"REAL WRITING SAMPLES (their actual work — the strongest signal; weight this most):\n{samples}\n\n"
        f"RAW ANSWERS (unpolished, may be voice-to-text):\n{answers}\n\n"
        f"Tone words they picked: {', '.join(v.tone_words) or '—'}\n"
        f"Look: {v.look or '—'}\n"
        f"Sentence length: {v.sentence_length or '—'}\n"
        f"Humor pick: {v.humor or '—'}\n"
        f"Sentence-shape pick: {v.shape or '—'}\n"
        f"Emojis: {v.emojis or '—'}\n"
        f"Banned: {', '.join(v.banned) or '—'}\n"
        f"Signature phrases: {', '.join(v.signatures) or '—'}\n"
        f"Notes: {v.notes or '—'}\n\n"
        "Return ONLY a JSON object with these keys:\n"
        '{"signature": "3-5 words", "vocabulary": "...", "sentence_style": "...", '
        '"favorite_phrases": ["..."], "banned": ["..."], "punctuation": "...", '
        '"humor": "...", "structure": "open / develop / close", "never_do": ["..."], '
        '"signatures": ["verbatim phrases"], "notes": "confidence labels"}'
    )


def _parse_voice_json(raw: str) -> VoiceProfile:
    text = raw.strip()
    if "```" in text:
        text = re.sub(r"```(?:json)?", "", text).strip()
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("no JSON object found in voice completion")
    return VoiceProfile.model_validate_json(text[start : end + 1])


def render_voice(vp: VoiceProfile) -> str:
    """Render the JSON profile to the prose voice block the drafting pipeline consumes."""

    def line(label: str, val: str) -> str:
        return f"- {label}: {val}" if val else ""

    def listline(label: str, vals: list[str]) -> str:
        return f"- {label}: {', '.join(vals)}" if vals else ""

    rows = [
        "# voice",
        "",
        line("Voice signature", vp.signature),
        line("Vocabulary & how technical", vp.vocabulary),
        line("Sentence style", vp.sentence_style),
        listline("Favorite words/phrases", vp.favorite_phrases),
        listline("BANNED words/phrases", vp.banned),
        line("Punctuation & formatting", vp.punctuation),
        line("Humor", vp.humor),
        line("Structural habits (open / develop / close)", vp.structure),
        listline("NEVER-DO", vp.never_do),
        listline("Signature / verbatim phrases", vp.signatures),
        line("Notes (confidence labels)", vp.notes),
    ]
    return "\n".join(r for r in rows if r) + "\n"


def load_voice() -> VoiceProfile | None:
    """The stored, hand-editable profile — or None if onboarding hasn't run."""
    if not VOICE_PATH.exists():
        return None
    return VoiceProfile.model_validate_json(VOICE_PATH.read_text(encoding="utf-8"))


def build_voice(intake: Intake, provider: Provider, force: bool = False) -> str:
    """Build profiles/voice.json from the intake and return its rendered prose.

    If voice.json already exists, keep it — your hand-edit IS the confirmation — unless
    force=True (an explicit `tb onboard`). Callers get prose, so the draft pipeline is
    unchanged; the JSON is what you (and `/timbre-voice`) edit.
    """
    existing = load_voice()
    if existing is not None and not force:
        return render_voice(existing)
    vp = _parse_voice_json(provider.complete("voice", build_voice_prompt(intake)))
    PROFILES_DIR.mkdir(parents=True, exist_ok=True)
    VOICE_PATH.write_text(vp.model_dump_json(indent=2) + "\n", encoding="utf-8")
    return render_voice(vp)


# --- persona insights: the reveal's "you said" receipts -----------------------
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
    raw = provider.complete("persona_insights", build_persona_insights_prompt(intake, max_insights))
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
