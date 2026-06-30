"""Pydantic schemas — every machine output is validated against these or rejected.

The rubric (hard gates + quality dimensions) is editable JSON: engine/rubric.json. It's loaded
here once, so the Score validation, the LLM score prompt (rubric/shared.py), and the stub all
key off the same source — retune a gate or reword a dimension by editing the JSON, no code.
"""

from __future__ import annotations

import json
from statistics import mean

from pydantic import BaseModel, Field, model_validator

from ..config import RUBRIC_PATH


def _load_rubric() -> tuple[list[dict], list[dict]]:
    try:
        data = json.loads(RUBRIC_PATH.read_text(encoding="utf-8"))
        return list(data["gates"]), list(data["dimensions"])
    except (OSError, ValueError, KeyError) as e:
        raise RuntimeError(f"invalid rubric config at {RUBRIC_PATH}: {e}") from e


_GATES, _DIMS = _load_rubric()
# The hard gates (must-contain / must-be-true, pass/fail) and the 0-10 quality dimensions.
GATE_NAMES = [g["name"] for g in _GATES]
DIM_NAMES = [d["name"] for d in _DIMS]
GATE_DESCRIPTIONS = {g["name"]: g.get("description", "") for g in _GATES}
DIM_DESCRIPTIONS = {d["name"]: d.get("description", "") for d in _DIMS}


class Gate(BaseModel):
    name: str
    passed: bool
    reason: str


class Dimension(BaseModel):
    name: str
    score: int = Field(ge=0, le=10)
    reason: str


class Score(BaseModel):
    gates: list[Gate]
    dimensions: list[Dimension]
    delta_vs_prev: str = ""

    @model_validator(mode="after")
    def _check_completeness(self) -> "Score":
        gates = {g.name for g in self.gates}
        dims = {d.name for d in self.dimensions}
        if gates != set(GATE_NAMES):
            raise ValueError(f"gates must be exactly {GATE_NAMES}, got {sorted(gates)}")
        if dims != set(DIM_NAMES):
            raise ValueError(f"dimensions must be exactly {DIM_NAMES}, got {sorted(dims)}")
        return self

    @property
    def gates_passed(self) -> int:
        return sum(1 for g in self.gates if g.passed)

    @property
    def gates_total(self) -> int:
        return len(self.gates)

    @property
    def quality_avg(self) -> float:
        return round(mean(d.score for d in self.dimensions), 1)

    @property
    def passes_threshold(self) -> bool:
        """Clean on every hard gate and a solid quality dial — a draft worth your time."""
        return self.gates_passed == self.gates_total and self.quality_avg >= 7.0

    def headline(self) -> str:
        return f"{self.quality_avg}/10  ·  gates {self.gates_passed}/{self.gates_total}"


class LevelResult(BaseModel):
    level: str  # e.g. "L0"
    label: str  # e.g. "Online"
    adds: str  # what this tier adds
    inputs_active: list[str]
    draft: str
    score: Score


class RunReport(BaseModel):
    run_id: str
    topic: str
    generated: str
    provider: str
    levels: list[LevelResult]
    places_to_refine: list[str]
