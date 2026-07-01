"""Self-learning loop — turn your picks and edits into a tighter VOICE, never a bloated one.

Every pick (option A over B, maybe with a why) and every edit reveals something about your
voice. Those are logged token-free (engine/signals.py). This reads the pending batch and, in
ONE call, updates `profiles/voice.json` — the profile your drafts actually obey and you edit
by hand. It updates in place (replace) and only adds genuinely new info, so the voice never
bloats or drifts. The voice signature and your identity are never auto-rewritten.
"""

from __future__ import annotations

import json
import re

from .blocks.persona import VoiceProfile
from .providers.base import Provider

# Only these voice.json fields are learnable. SET replaces a value in place; ADD appends to a
# list (de-duplicated). `signature` (the core of the voice) is deliberately left out.
SET_FIELDS = {"vocabulary", "sentence_style", "punctuation", "humor", "structure", "notes"}
ADD_FIELDS = {"favorite_phrases", "banned", "signatures", "never_do"}


def build_learn_prompt(signals: list[dict], voice: VoiceProfile) -> str:
    fields = {f: getattr(voice, f) for f in sorted(SET_FIELDS | ADD_FIELDS)}
    return (
        "Below are the user's recent signals: picks (which of two drafts they chose, and maybe "
        "why) and edits (how they changed a draft). Read ONLY for what they reveal about their "
        "writing VOICE — not post content. Propose conservative updates to the voice profile.\n\n"
        "RULES (anti-bloat, strict):\n"
        "- Name the trait in general terms — never copy a specific phrase, number, or example "
        "from the post (e.g. 'opens on a concrete moment', not 'Friday, 5 pm.').\n"
        "- Prefer op 'set' (replace a field's value in place). Keep values short.\n"
        "- Use op 'add' ONLY for genuinely new info not already covered, and only for list fields.\n"
        "- If the signals reveal nothing about voice, return [].\n\n"
        f"SET fields (replace the value): {sorted(SET_FIELDS)}\n"
        f"ADD fields (append only if new): {sorted(ADD_FIELDS)}\n\n"
        f"CURRENT VOICE:\n{json.dumps(fields, indent=2)}\n\n"
        f"SIGNALS:\n{json.dumps(signals, indent=2)}\n\n"
        'Return ONLY JSON: [{"field":"signatures","op":"add","value":"...","why":"..."}]'
    )


def parse_edits(raw: str) -> list[dict]:
    text = raw.strip()
    if "```" in text:
        text = re.sub(r"```(?:json)?", "", text).strip()
    start, end = text.find("["), text.rfind("]")
    if start == -1 or end == -1:
        return []
    return json.loads(text[start : end + 1])


def apply_edits(voice: VoiceProfile, edits: list[dict]) -> tuple[list[str], list[str]]:
    """Apply learnable edits to the voice profile in place. Returns (applied, skipped) summaries."""
    applied: list[str] = []
    skipped: list[str] = []
    for e in edits:
        field, op, value = e.get("field"), e.get("op"), e.get("value")
        if op == "set" and field in SET_FIELDS and isinstance(value, str):
            old = getattr(voice, field)
            if value.strip() and value.strip() != old:
                setattr(voice, field, value.strip())
                applied.append(f"set {field}: {old!r} -> {value.strip()!r}")
            else:
                skipped.append(f"{field} (no change)")
        elif op == "add" and field in ADD_FIELDS and isinstance(value, str):
            lst = getattr(voice, field)
            if value.strip() and value.strip().lower() not in [x.lower() for x in lst]:
                lst.append(value.strip())
                applied.append(f"add {field}: +{value.strip()!r}")
            else:
                skipped.append(f"{field} (already present)")
        else:
            skipped.append(f"{field} ({op}: not learnable)")
    return applied, skipped


def learn(
    signals: list[dict], voice: VoiceProfile, provider: Provider
) -> tuple[list[str], list[str]]:
    """Fold a batch of signals (picks + edits) into the voice profile in one call. Empty in, empty out."""
    if not signals:
        return [], []
    raw = provider.complete("learn", build_learn_prompt(signals, voice))
    return apply_edits(voice, parse_edits(raw))
