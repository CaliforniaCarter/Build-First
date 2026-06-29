"""The ablation's integrity invariants: levels are cumulative, and the rich
specifics must NOT leak before L4 (or the ladder would show no progression)."""
from engine.ablation import LEVELS, context_for
from engine.blocks.intake import ContentIdea, Intake
from engine.report import build_report, compute_places_to_refine
from engine.rubric.schemas import DIM_NAMES, GATE_NAMES, LevelResult, RunReport, Score


def _intake() -> Intake:
    return Intake(
        name="Tester",
        idea=ContentIdea(topic="TOPIC-LINE", mechanism="SECRET-MECHANISM", number="42", scene="A-SCENE"),
    )


def test_levels_are_cumulative():
    seen: set[str] = set()
    for _level, _label, _adds, inputs in LEVELS:
        assert seen.issubset(set(inputs)), "each level must keep all prior inputs"
        seen = set(inputs)
    assert LEVELS[0][3] == ["online"]
    assert "eval" in LEVELS[-1][3]


def test_specifics_hidden_until_l4():
    intake = _intake()
    for _level, _label, _adds, inputs in LEVELS:
        ctx = context_for(inputs, intake)
        assert "TOPIC-LINE" in ctx, "topic is known at every level"
        if "specifics" in inputs:
            assert "SECRET-MECHANISM" in ctx
        else:
            assert "SECRET-MECHANISM" not in ctx, "specifics must not leak before L4"


def _full_score() -> Score:
    return Score.model_validate({
        "gates": [{"name": n, "passed": True, "reason": "ok"} for n in GATE_NAMES],
        "dimensions": [{"name": n, "score": 7, "reason": "ok"} for n in DIM_NAMES],
        "delta_vs_prev": "baseline",
    })


def test_build_report_smoke():
    lr = LevelResult(
        level="L0", label="Online", adds="footprint", inputs_active=["online"],
        draft="hello world", score=_full_score(),
    )
    report = RunReport(
        run_id="r", topic="t", generated="2026-06-29", provider="terminal",
        levels=[lr], places_to_refine=compute_places_to_refine([lr]),
    )
    md = build_report(report)
    assert "Scoreboard" in md and "L0" in md and "Places to refine" in md
