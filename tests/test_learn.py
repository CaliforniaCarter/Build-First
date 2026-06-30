"""Self-learning loop: edits refine the profile in place, never bloat it; idea is off-limits."""

from engine.blocks.intake import ContentIdea, Intake, Voice
from engine.learn import apply_edits, parse_edits


def _intake() -> Intake:
    return Intake(
        name="Tester",
        idea=ContentIdea(topic="t"),
        voice=Voice(emojis="sparingly", banned=["jargon"]),
    )


def test_set_replaces_in_place():
    intake = _intake()
    applied, _ = apply_edits(
        intake, [{"field": "voice.emojis", "op": "set", "value": "none", "why": "x"}]
    )
    assert intake.voice.emojis == "none"
    assert any("voice.emojis" in a for a in applied)


def test_add_dedupes_and_appends_new():
    intake = _intake()
    applied, skipped = apply_edits(
        intake,
        [
            {"field": "voice.banned", "op": "add", "value": "jargon", "why": "dup"},
            {"field": "voice.banned", "op": "add", "value": "synergy", "why": "new"},
        ],
    )
    assert intake.voice.banned == ["jargon", "synergy"]  # no bloat: duplicate skipped
    assert any("synergy" in a for a in applied)
    assert any("already present" in s for s in skipped)


def test_non_learnable_field_is_skipped():
    intake = _intake()
    apply_edits(intake, [{"field": "idea.topic", "op": "set", "value": "hacked", "why": "x"}])
    assert intake.idea.topic == "t"  # per-post idea is off-limits


def test_parse_edits_handles_fences_and_junk():
    assert parse_edits("```json\n[]\n```") == []
    assert parse_edits("no json here") == []
    assert (
        parse_edits('[{"field":"voice.notes","op":"set","value":"x"}]')[0]["field"] == "voice.notes"
    )
