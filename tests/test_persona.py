"""build_persona preserves a hand-edited persona.md unless forced — the 'that's me?' confirm
must survive the next post."""

from engine.blocks.intake import ContentIdea, Intake, Voice
from engine.blocks.persona import build_persona, build_persona_prompt
from engine.providers.stub import StubProvider


def test_persona_prompt_weights_writing_samples():
    intake = Intake(
        name="T", idea=ContentIdea(topic="t"), voice=Voice(writing_samples=["SAMPLE-ESSAY-XYZ"])
    )
    assert "SAMPLE-ESSAY-XYZ" in build_persona_prompt(intake)


def test_persona_preserves_hand_edit_unless_forced(tmp_path, monkeypatch):
    monkeypatch.setattr("engine.blocks.persona.PROFILES_DIR", tmp_path)
    intake = Intake(name="Tester", idea=ContentIdea(topic="t"))

    build_persona(intake, StubProvider())  # first build writes the proposal
    (tmp_path / "persona.md").write_text("MY HAND EDIT\n", encoding="utf-8")

    # a normal post-time build must NOT clobber the hand edit
    assert build_persona(intake, StubProvider()) == "MY HAND EDIT\n"
    # an explicit `tb onboard` (force) rebuilds it
    assert "MY HAND EDIT" not in build_persona(intake, StubProvider(), force=True)
