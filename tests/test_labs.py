"""Timbre Labs config is editable JSON: the rubric (gates + dimensions, engine/rubric.json) and
the ablation ladder (engine/labs.json) load, validate, and stay in sync with the code."""

import json

from engine.ablation import (
    ablatable_fields,
    ablatable_voice_fields,
    load_ladder,
    run_field_ablation,
    run_persona_ablation,
)
from engine.blocks.intake import ContentIdea, Intake, Voice
from engine.config import LABS_PATH, RUBRIC_PATH
from engine.providers.stub import StubProvider
from engine.rubric.schemas import DIM_DESCRIPTIONS, DIM_NAMES, GATE_DESCRIPTIONS, GATE_NAMES


def test_rubric_loads_with_descriptions():
    assert len(GATE_NAMES) == 6 and len(DIM_NAMES) == 9
    # every gate/dimension carries a non-empty description (it's fed into the score prompt)
    assert all(GATE_DESCRIPTIONS[g] for g in GATE_NAMES)
    assert all(DIM_DESCRIPTIONS[d] for d in DIM_NAMES)


def test_rubric_json_is_the_single_source():
    data = json.loads(RUBRIC_PATH.read_text(encoding="utf-8"))
    assert [g["name"] for g in data["gates"]] == GATE_NAMES
    assert [d["name"] for d in data["dimensions"]] == DIM_NAMES


def test_ladder_loads_and_is_cumulative():
    ladder = load_ladder()
    assert [t[0] for t in ladder] == ["L0", "L1", "L2", "L3", "L4", "L5"]
    seen: set[str] = set()
    for _level, _label, _adds, inputs in ladder:
        assert seen.issubset(set(inputs))  # each tier keeps all prior inputs
        seen = set(inputs)


def test_labs_json_matches_loader():
    data = json.loads(LABS_PATH.read_text(encoding="utf-8"))
    assert [t["level"] for t in data["ladder"]] == [t[0] for t in load_ladder()]


def test_field_ablation_auto_discovers_and_scores_each_field():
    intake = Intake(
        name="T",
        idea=ContentIdea(
            topic="shipped a tool", number="cut it 22%", scene="friday 5pm", lesson="ship the eval"
        ),
    )
    fields = ablatable_fields(intake)
    # populated fields are discovered automatically; the topic (the seed) never is
    assert {"idea.number", "idea.scene", "idea.lesson"} <= set(fields)
    assert "idea.topic" not in fields

    baseline, results = run_field_ablation(intake, "voice", StubProvider(), "qa")
    assert isinstance(baseline, (int, float))
    assert len(results) == len(fields)  # one leave-one-out result per field
    assert all(set(r) == {"field", "score_without", "contribution"} for r in results)
    # the handles are footprint, not draft material — never ablated as a draft field
    assert "online.linkedin" not in fields and "online.x" not in fields


def test_persona_ablation_discovers_voice_inputs_and_reextracts():
    # the voice corpus feeds the PERSONA, not the draft — so it's tested by re-extracting the
    # voice profile with one input dropped, not by editing the draft context.
    intake = Intake(
        name="T",
        idea=ContentIdea(topic="shipped a tool"),
        voice=Voice(
            writing_samples=["a real post i wrote"],
            answers={"weekend": "fixed my bike on the kitchen floor"},
            style_pick="the warm, building one",
        ),
    )
    vf = ablatable_voice_fields(intake)
    assert {"voice.writing_samples", "voice.answers", "voice.style_pick"} <= set(vf)

    baseline, results = run_persona_ablation(intake, StubProvider(), "qa")
    assert isinstance(baseline, (int, float))
    assert len(results) == len(vf)  # one leave-one-out result per voice input
    assert all(set(r) == {"field", "score_without", "contribution"} for r in results)
