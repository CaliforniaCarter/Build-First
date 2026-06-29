"""Schemas reject malformed scores and accept complete ones."""

import pytest
from pydantic import ValidationError

from engine.rubric.schemas import DIM_NAMES, GATE_NAMES, Score


def _full_score(**over):
    data = {
        "gates": [{"name": n, "passed": True, "reason": "ok"} for n in GATE_NAMES],
        "dimensions": [{"name": n, "score": 8, "reason": "ok"} for n in DIM_NAMES],
        "delta_vs_prev": "baseline",
    }
    data.update(over)
    return data


def test_valid_score():
    s = Score.model_validate(_full_score())
    assert s.gates_passed == 6
    assert s.quality_avg == 8.0
    assert "/10" in s.headline()


def test_missing_gate_rejected():
    bad = _full_score(gates=[{"name": n, "passed": True, "reason": "x"} for n in GATE_NAMES[:-1]])
    with pytest.raises(ValidationError):
        Score.model_validate(bad)


def test_score_out_of_range_rejected():
    bad = _full_score(dimensions=[{"name": n, "score": 11, "reason": "x"} for n in DIM_NAMES])
    with pytest.raises(ValidationError):
        Score.model_validate(bad)
