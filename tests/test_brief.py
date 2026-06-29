"""The brief is deterministic, validates, and fully drives the draft prompt."""

import pytest

from engine.blocks.brief import Brief, build_brief, render_brief_md
from engine.blocks.draft import build_draft_prompt_from_brief
from engine.blocks.intake import ContentIdea, Intake, OutputPrefs, Voice
from engine.posttypes import get_post_type


def _intake():
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
        output=OutputPrefs(length="medium", hard_nevers=["no emojis"]),
    )


def test_build_brief_is_deterministic():
    assert build_brief(_intake(), "linkedin_build").model_dump() == (
        build_brief(_intake(), "linkedin_build").model_dump()
    )


def test_build_brief_pulls_from_intake_and_type():
    b = build_brief(_intake(), "linkedin_build")
    assert b.channel == "LinkedIn"
    assert b.tone == ["plain", "warm"]
    assert b.cadence == "short lines"  # intake.voice.sentence_length overrides the type default
    assert b.length == "medium"  # intake.output.length overrides the type default
    assert b.banned == ["leverage"]
    assert b.hard_nevers == ["no emojis"]
    assert b.content_idea.topic == "Shipping an eval harness"
    assert b.structure == get_post_type("linkedin_build").structure


def test_cadence_and_length_fall_back_to_type_defaults():
    intake = _intake()
    intake.voice.sentence_length = ""
    intake.output.length = ""
    b = build_brief(intake, "linkedin_build")
    pt = get_post_type("linkedin_build")
    assert b.cadence == pt.cadence
    assert b.length == pt.length


def test_brief_json_roundtrips():
    b = build_brief(_intake(), "linkedin_build")
    assert Brief.model_validate_json(b.model_dump_json()).model_dump() == b.model_dump()


def test_rendered_prompt_contains_every_structure_step_and_the_idea():
    b = build_brief(_intake(), "linkedin_build")
    prompt = build_draft_prompt_from_brief(b, persona_md="(the voice)", layers="(the layers)")
    for step in b.structure:
        assert step in prompt
    assert b.content_idea.topic in prompt
    assert "42%" in prompt  # the real number is carried through, not invented
    assert "(the voice)" in prompt


def test_render_brief_md_lists_the_structure():
    md = render_brief_md(build_brief(_intake(), "linkedin_build"))
    assert "## Structure" in md
    assert "Shipping an eval harness" in md


def test_unknown_post_type_raises():
    with pytest.raises(ValueError):
        build_brief(_intake(), "tiktok_dance")
