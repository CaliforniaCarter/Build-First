"""Timbre Labs config is editable JSON: the rubric (gates + dimensions, engine/rubric.json) and
the ablation ladder (engine/labs.json) load, validate, and stay in sync with the code."""

import json

from engine.ablation import load_ladder
from engine.config import LABS_PATH, RUBRIC_PATH
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
