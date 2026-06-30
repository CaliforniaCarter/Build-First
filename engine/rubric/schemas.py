"""Pydantic schemas — every machine output is validated against these or rejected."""

from __future__ import annotations

from statistics import mean

from pydantic import BaseModel, Field, model_validator

# The six hard gates (must-contain / must-be-true). Pass/fail.
GATE_NAMES = [
    "only_you",  # an observation only this person could make
    "real_number_or_specific",  # a real number or a concrete, checkable detail
    "concrete_scene",  # a real moment, shown not summarized
    "non_obvious_lesson",  # a takeaway most people would miss
    "no_slop",  # none of the banned slop phrases
    "central_claim_human",  # the core claim is the human's, not the model's
]

# The nine 0-10 quality dimensions, each scored with a one-line reason.
DIM_NAMES = [
    "story_strength",
    "opinion_edge",
    "specificity_surprise",
    "emotional_resonance",
    "ownability",
    "voice_match",
    "format_adherence",
    "audience_fit",
    "stakes_turn",
]


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
