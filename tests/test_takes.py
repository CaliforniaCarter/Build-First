"""Takes — spiky opinions surfaced from the user's material, robustly parsed."""

from engine.blocks.intake import ContentIdea, Intake
from engine.providers.stub import StubProvider
from engine.takes import form_takes, parse_takes


def test_parse_takes_handles_fences_and_junk():
    assert parse_takes("```json\n[]\n```") == []
    assert parse_takes("no json here") == []
    assert parse_takes('[{"take":"x","based_on":"y"}]')[0]["take"] == "x"


def test_form_takes_returns_only_real_takes():
    intake = Intake(name="T", idea=ContentIdea(topic="simplicity"))
    takes = form_takes(intake, "voice", StubProvider())
    assert takes and all(t.get("take") for t in takes)
