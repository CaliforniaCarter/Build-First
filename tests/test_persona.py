"""build_voice preserves a hand-edited voice.json unless forced — the 'that's me?' confirm
must survive the next post. The profile is JSON; the draft pipeline gets it rendered to prose.
"""

from engine.blocks.intake import ContentIdea, Intake, Voice
from engine.blocks.persona import (
    VoiceProfile,
    build_voice,
    build_voice_prompt,
    render_voice,
)
from engine.providers.stub import StubProvider


def test_voice_prompt_weights_writing_samples():
    intake = Intake(
        name="T", idea=ContentIdea(topic="t"), voice=Voice(writing_samples=["SAMPLE-ESSAY-XYZ"])
    )
    assert "SAMPLE-ESSAY-XYZ" in build_voice_prompt(intake)


def test_render_voice_includes_banned_and_signatures():
    vp = VoiceProfile(
        signature="dry, concrete", banned=["delve", "leverage"], signatures=["ship it"]
    )
    prose = render_voice(vp)
    assert "delve" in prose and "leverage" in prose and "ship it" in prose


def test_build_voice_writes_json_and_returns_prose(tmp_path, monkeypatch):
    monkeypatch.setattr("engine.blocks.persona.PROFILES_DIR", tmp_path)
    monkeypatch.setattr("engine.blocks.persona.VOICE_PATH", tmp_path / "voice.json")
    intake = Intake(name="Tester", idea=ContentIdea(topic="t"))

    prose = build_voice(intake, StubProvider(), force=True)
    assert (tmp_path / "voice.json").exists()
    assert "delve" in prose  # the stub's banned list flows through the render
    VoiceProfile.model_validate_json((tmp_path / "voice.json").read_text())  # valid JSON


def test_build_voice_preserves_hand_edit_unless_forced(tmp_path, monkeypatch):
    monkeypatch.setattr("engine.blocks.persona.PROFILES_DIR", tmp_path)
    monkeypatch.setattr("engine.blocks.persona.VOICE_PATH", tmp_path / "voice.json")
    intake = Intake(name="Tester", idea=ContentIdea(topic="t"))

    build_voice(intake, StubProvider(), force=True)  # first build writes the proposal
    (tmp_path / "voice.json").write_text(
        VoiceProfile(signature="MY HAND EDIT").model_dump_json(indent=2), encoding="utf-8"
    )

    # a normal post-time build must NOT clobber the hand edit
    assert "MY HAND EDIT" in build_voice(intake, StubProvider())
    # an explicit `tb onboard` (force) rebuilds it
    assert "MY HAND EDIT" not in build_voice(intake, StubProvider(), force=True)
