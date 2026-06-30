"""Self-learning loop: picks/edits refine voice.json in place, never bloat it; the voice
signature is off-limits."""

from engine.blocks.persona import VoiceProfile
from engine.learn import apply_edits, parse_edits


def _voice() -> VoiceProfile:
    return VoiceProfile(
        signature="dry, concrete", punctuation="emojis sparingly", banned=["jargon"]
    )


def test_set_replaces_in_place():
    voice = _voice()
    applied, _ = apply_edits(
        voice, [{"field": "punctuation", "op": "set", "value": "no emojis", "why": "x"}]
    )
    assert voice.punctuation == "no emojis"
    assert any("punctuation" in a for a in applied)


def test_add_dedupes_and_appends_new():
    voice = _voice()
    applied, skipped = apply_edits(
        voice,
        [
            {"field": "banned", "op": "add", "value": "jargon", "why": "dup"},
            {"field": "banned", "op": "add", "value": "synergy", "why": "new"},
        ],
    )
    assert voice.banned == ["jargon", "synergy"]  # no bloat: duplicate skipped
    assert any("synergy" in a for a in applied)
    assert any("already present" in s for s in skipped)


def test_signature_is_not_learnable():
    voice = _voice()
    apply_edits(voice, [{"field": "signature", "op": "set", "value": "hacked", "why": "x"}])
    assert voice.signature == "dry, concrete"  # the core voice signature is never auto-rewritten


def test_parse_edits_handles_fences_and_junk():
    assert parse_edits("```json\n[]\n```") == []
    assert parse_edits("no json here") == []
    assert parse_edits('[{"field":"notes","op":"set","value":"x"}]')[0]["field"] == "notes"
