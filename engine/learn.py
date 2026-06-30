"""Self-learning loop — turn your edits into a tighter profile, never a bloated one.

When you edit a draft, that edit reveals something about your voice or who you are. This
reads the edit and updates the SOURCE (data/intake.json) so the next draft is closer. It
updates in place (replace) and only adds genuinely new info — the profile never bloats.
See docs/self_learning.md.
"""

from __future__ import annotations

import json
import re

from .blocks.intake import Intake
from .providers.base import Provider

# Only these fields are learnable. SET replaces a value in place; ADD appends to a list
# (de-duplicated). Everything else (especially the per-post idea) is off-limits.
SET_FIELDS = {
    "voice.look",
    "voice.sentence_length",
    "voice.emojis",
    "voice.notes",
    "typed.identity",
    "typed.known_for",
    "typed.background",
    "typed.beliefs",
    "typed.lessons",
}
ADD_FIELDS = {"voice.tone_words", "voice.banned", "voice.signatures"}


def _get(intake: Intake, dotted: str):
    obj, attr = dotted.split(".")
    return getattr(getattr(intake, obj), attr)


def _set(intake: Intake, dotted: str, value) -> None:
    obj, attr = dotted.split(".")
    setattr(getattr(intake, obj), attr, value)


def build_learn_prompt(original: str, edited: str, intake: Intake) -> str:
    fields = {f: _get(intake, f) for f in sorted(SET_FIELDS | ADD_FIELDS)}
    return (
        "The user edited a post you drafted. Read ONLY for what the edit reveals about their "
        "VOICE or WHO THEY ARE — not the post's content. Propose conservative updates to their "
        "profile fields.\n\n"
        "RULES (anti-bloat, strict):\n"
        "- Prefer op 'set' (replace a field's value in place). Keep values short.\n"
        "- Use op 'add' ONLY for genuinely new info not already covered, and only for list fields.\n"
        "- If the edit is just a content tweak and reveals nothing about voice/identity, return [].\n\n"
        f"SET fields (replace the value): {sorted(SET_FIELDS)}\n"
        f"ADD fields (append only if new): {sorted(ADD_FIELDS)}\n\n"
        f"CURRENT FIELDS:\n{json.dumps(fields, indent=2)}\n\n"
        f"DRAFT (what the engine wrote):\n{original}\n\n"
        f"EDITED (what the user changed it to):\n{edited}\n\n"
        'Return ONLY JSON: [{"field":"voice.emojis","op":"set","value":"none","why":"..."}]'
    )


def parse_edits(raw: str) -> list[dict]:
    text = raw.strip()
    if "```" in text:
        text = re.sub(r"```(?:json)?", "", text).strip()
    start, end = text.find("["), text.rfind("]")
    if start == -1 or end == -1:
        return []
    return json.loads(text[start : end + 1])


def apply_edits(intake: Intake, edits: list[dict]) -> tuple[list[str], list[str]]:
    """Apply learnable edits in place. Returns (applied, skipped) human-readable summaries."""
    applied: list[str] = []
    skipped: list[str] = []
    for e in edits:
        field, op, value = e.get("field"), e.get("op"), e.get("value")
        if op == "set" and field in SET_FIELDS and isinstance(value, str):
            old = _get(intake, field)
            if value.strip() and value.strip() != old:
                _set(intake, field, value.strip())
                applied.append(f"set {field}: {old!r} -> {value.strip()!r}")
            else:
                skipped.append(f"{field} (no change)")
        elif op == "add" and field in ADD_FIELDS and isinstance(value, str):
            lst = _get(intake, field)
            if value.strip() and value.strip().lower() not in [x.lower() for x in lst]:
                lst.append(value.strip())
                applied.append(f"add {field}: +{value.strip()!r}")
            else:
                skipped.append(f"{field} (already present)")
        else:
            skipped.append(f"{field} ({op}: not learnable)")
    return applied, skipped


def learn(
    original: str, edited: str, intake: Intake, provider: Provider
) -> tuple[list[str], list[str]]:
    raw = provider.complete("learn", build_learn_prompt(original, edited, intake))
    return apply_edits(intake, parse_edits(raw))
