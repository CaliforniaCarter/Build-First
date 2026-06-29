"""The brief is deterministic, validates, drives the prompt, and enforces the char cap."""

import pytest

from engine.blocks.brief import Brief, build_brief, over_limit, render_brief_md
from engine.blocks.draft import build_draft_prompt_from_brief
from engine.blocks.intake import ContentIdea, Intake, OutputPrefs, Voice


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
    assert build_brief(_intake(), "linkedin_post").model_dump() == (
        build_brief(_intake(), "linkedin_post").model_dump()
    )


def test_build_brief_pulls_from_intake_and_type():
    b = build_brief(_intake(), "linkedin_post")
    assert b.output == "a post for LinkedIn"  # derived from platform + type
    assert b.character_count == 3000
    assert b.content == "words"
    assert b.tone == ["plain", "warm"]
    assert b.cadence == "short lines"
    assert b.length == "medium"  # intake.output.length overrides the type default
    assert b.content_idea.topic == "Shipping an eval harness"


def test_intake_format_overrides_the_output_label():
    b = build_brief(_intake(format="a spicy LinkedIn hot take"), "linkedin_post")
    assert b.output == "a spicy LinkedIn hot take"


def test_x_post_has_the_280_char_cap():
    b = build_brief(_intake(), "x_post")
    assert b.character_count == 280
    assert "X/Twitter" in b.output


def test_brief_json_roundtrips():
    b = build_brief(_intake(), "linkedin_post")
    assert Brief.model_validate_json(b.model_dump_json()).model_dump() == b.model_dump()


def test_over_limit_flags_but_never_trims():
    b = build_brief(_intake(), "x_post")  # 280 cap
    assert over_limit("x" * 281, b) == 1
    assert over_limit("x" * 280, b) == 0
    assert over_limit("anything", build_brief(_intake(), "linkedin_post")) <= 0  # 3000 cap


def test_rendered_prompt_carries_output_idea_and_char_cap():
    b = build_brief(_intake(), "x_post")
    prompt = build_draft_prompt_from_brief(b, persona_md="(the voice)", layers="(the layers)")
    assert "a post for X/Twitter" in prompt
    assert "at most 280 characters" in prompt  # hard cap surfaced to the model
    assert b.content_idea.topic in prompt
    assert "42%" in prompt  # the real number is carried through, not invented
    assert "(the layers)" in prompt  # structure is interpreted from the layers


def test_render_brief_md_shows_output_and_cap():
    md = render_brief_md(build_brief(_intake(), "x_post"))
    assert "**Output:**" in md
    assert "280" in md
    assert "Shipping an eval harness" in md


def test_unknown_post_type_raises():
    with pytest.raises(ValueError):
        build_brief(_intake(), "tiktok_dance")
