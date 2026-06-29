"""The brief is deterministic, validates, and fully drives the draft prompt."""

import pytest

from engine.blocks.brief import Brief, build_brief, render_brief_md
from engine.blocks.draft import build_draft_prompt_from_brief
from engine.blocks.intake import ContentIdea, Intake, OutputPrefs, Voice
from engine.posttypes import get_post_type


def _intake(**output_over):
    return Intake(
        name="Carter",
        idea=ContentIdea(
            topic="Shipping an eval harness",
            number="42%",
            mechanism="an ablation ladder",
            proof=["runs/2026-06-29/report.md"],
        ),
        voice=Voice(
            tone_words=["plain", "warm"], sentence_length="short lines", banned=["leverage"]
        ),
        output=OutputPrefs(length="medium", hard_nevers=["no emojis"], **output_over),
    )


def test_build_brief_is_deterministic():
    assert build_brief(_intake(), "linkedin").model_dump() == (
        build_brief(_intake(), "linkedin").model_dump()
    )


def test_build_brief_pulls_from_intake_and_type():
    b = build_brief(_intake(), "linkedin")
    assert b.output == "a LinkedIn post"  # from the post type's plain-language label
    assert b.constraints == []  # LinkedIn pins no hard constraints
    assert b.tone == ["plain", "warm"]
    assert b.cadence == "short lines"
    assert b.length == "medium"
    assert b.banned == ["leverage"]
    assert b.hard_nevers == ["no emojis"]
    assert b.content_idea.topic == "Shipping an eval harness"


def test_intake_format_overrides_the_output_label():
    b = build_brief(_intake(format="a punchy LinkedIn post"), "linkedin")
    assert b.output == "a punchy LinkedIn post"


def test_x_type_carries_hard_constraints():
    b = build_brief(_intake(), "x")
    assert b.output == get_post_type("x").output
    assert "under 300 characters" in b.constraints


def test_brief_json_roundtrips():
    b = build_brief(_intake(), "linkedin")
    assert Brief.model_validate_json(b.model_dump_json()).model_dump() == b.model_dump()


def test_rendered_prompt_carries_output_idea_and_constraints():
    b = build_brief(_intake(), "x")
    prompt = build_draft_prompt_from_brief(b, persona_md="(the voice)", layers="(the layers)")
    assert "an X / Twitter post" in prompt
    assert "under 300 characters" in prompt  # hard constraint surfaced to the model
    assert b.content_idea.topic in prompt
    assert "42%" in prompt  # the real number is carried through, not invented
    assert "(the layers)" in prompt  # structure is interpreted from the layers
    assert "(the voice)" in prompt


def test_render_brief_md_shows_output_and_constraints():
    md = render_brief_md(build_brief(_intake(), "x"))
    assert "**Output:**" in md
    assert "under 300 characters" in md
    assert "Shipping an eval harness" in md


def test_unknown_post_type_raises():
    with pytest.raises(ValueError):
        build_brief(_intake(), "tiktok_dance")
