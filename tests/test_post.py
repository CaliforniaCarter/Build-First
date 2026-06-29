"""The product path: generate_post drafts -> councils -> scores -> gates, with progress events."""

from __future__ import annotations

from engine.blocks.intake import ContentIdea, Intake
from engine.post import generate_post
from engine.rubric.schemas import Score
from tests.conftest import FakeProvider


def _intake() -> Intake:
    return Intake(
        name="Tester",
        idea=ContentIdea(
            topic="shipping an overnight build",
            mechanism="a provider seam",
            number="5 calls",
            scene="2am, it broke",
        ),
    )


def test_generate_post_happy_path():
    events: list[tuple[str, dict]] = []
    res = generate_post(
        _intake(), "voice", FakeProvider(), "r-test", on_stage=lambda s, p: events.append((s, p))
    )

    assert res.draft  # produced a draft
    assert isinstance(res.score, Score)
    assert res.council_log, "council ran at least one pass"
    assert res.draft_path.endswith("draft.md")

    stages = [s for s, _ in events]
    assert stages[0] == "draft"
    assert "council" in stages
    assert "score" in stages
    assert stages[-1] == "done"


def test_generate_post_redacts_pii_before_gate():
    leaky = "i shipped it. reach me at carter@example.com if you want the code."
    res = generate_post(_intake(), "voice", FakeProvider(revised=leaky), "r-redact")
    assert "carter@example.com" not in res.draft
    assert "email" in res.redactions


def test_generate_post_can_skip_score():
    res = generate_post(_intake(), "voice", FakeProvider(), "r-noscore", do_score=False)
    assert res.score is None
