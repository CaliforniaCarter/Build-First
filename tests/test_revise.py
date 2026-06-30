"""Revise by command: the prompt carries the user's instruction, the post, and the voice."""

from engine.revise import build_revise_prompt


def test_revise_prompt_carries_command_post_and_voice():
    p = build_revise_prompt(
        "the post body", "make it shorter", "VOICE-RULES", "LAYERS", ["no emojis"]
    )
    assert "make it shorter" in p
    assert "the post body" in p
    assert "VOICE-RULES" in p
    assert "no emojis" in p
    assert "Output ONLY the revised post text." in p
