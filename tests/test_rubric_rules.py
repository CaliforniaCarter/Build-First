"""Slop detection and PII redaction behave."""
from engine.blocks.receipts import redact
from engine.rubric.shared import find_slop, parse_score


def test_find_slop_detects_banned():
    hits = find_slop("Excited to announce we will leverage synergy to unlock value")
    assert "leverage" in hits and "unlock" in hits


def test_find_slop_clean_text():
    assert find_slop("i shipped a thing today. it broke. i fixed it.") == []


def test_redact_email_and_phone():
    text = "reach me at carter@example.com or (858) 353-7434"
    out, found = redact(text)
    assert "carter@example.com" not in out
    assert "email" in found and "phone" in found


def test_parse_score_from_fenced_json():
    raw = (
        "```json\n"
        '{"gates":[{"name":"only_you","passed":true,"reason":"x"},'
        '{"name":"real_number_or_specific","passed":true,"reason":"x"},'
        '{"name":"concrete_scene","passed":true,"reason":"x"},'
        '{"name":"non_obvious_lesson","passed":true,"reason":"x"},'
        '{"name":"no_slop","passed":true,"reason":"x"},'
        '{"name":"central_claim_human","passed":true,"reason":"x"}],'
        '"dimensions":[{"name":"story_strength","score":7,"reason":"x"},'
        '{"name":"opinion_edge","score":7,"reason":"x"},'
        '{"name":"specificity_surprise","score":7,"reason":"x"},'
        '{"name":"emotional_resonance","score":7,"reason":"x"},'
        '{"name":"ownability","score":7,"reason":"x"},'
        '{"name":"voice_match","score":7,"reason":"x"},'
        '{"name":"format_adherence","score":7,"reason":"x"},'
        '{"name":"audience_fit","score":7,"reason":"x"},'
        '{"name":"stakes_turn","score":7,"reason":"x"}],'
        '"delta_vs_prev":"baseline"}'
        "\n```"
    )
    score = parse_score(raw)
    assert score.quality_avg == 7.0
