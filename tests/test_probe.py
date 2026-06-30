"""The gap-driven probe: it flags what's missing and writes answers back, never inventing."""

from engine.blocks.intake import ContentIdea, Intake
from engine.blocks.probe import apply_answers, find_gaps, unfilled_gaps


def _intake(**idea) -> Intake:
    return Intake(name="Tester", idea=ContentIdea(topic="t", **idea))


def test_find_gaps_flags_missing():
    gaps = {g["key"]: g["filled"] for g in find_gaps(_intake(number="42"))}
    assert gaps == {"number": True, "scene": False, "lesson": False, "only_you": False}


def test_unfilled_gaps_excludes_filled():
    keys = [g["key"] for g in unfilled_gaps(_intake(number="42", scene="a moment"))]
    assert keys == ["lesson", "only_you"]


def test_apply_answers_writes_and_skips_blanks():
    intake = _intake()
    apply_answers(intake, {"number": "80 things", "scene": "   ", "bogus": "x"})
    assert intake.idea.number == "80 things"
    assert intake.idea.scene == ""  # blank skipped, nothing invented
