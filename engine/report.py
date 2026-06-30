"""Assemble the run report: post progression, scores, per-dimension reasons, diffs,
and a places-to-refine list. Output is Markdown (also what gets posted to Notion).
"""

from __future__ import annotations

import difflib
from pathlib import Path

from .config import RUNS_DIR
from .rubric.schemas import LevelResult, RunReport, Score


def _diff(prev: str, cur: str) -> str:
    lines = list(
        difflib.unified_diff(
            prev.splitlines(), cur.splitlines(), lineterm="", n=1, fromfile="prev", tofile="this"
        )
    )
    return "\n".join(lines[:40]) if lines else "(no textual change)"


def compute_places_to_refine(results: list[LevelResult]) -> list[str]:
    final = results[-1].score
    places: list[str] = []
    for gate in final.gates:
        if not gate.passed:
            places.append(f"Hard gate still failing — {gate.name}: {gate.reason}")
    weak = sorted(final.dimensions, key=lambda d: d.score)[:2]
    for d in weak:
        if d.score < 8:
            places.append(f"Lowest dimension — {d.name} ({d.score}/10): {d.reason}")
    return places or ["No blocking gaps in the final draft; tune wording to taste."]


def _score_block(score: Score) -> str:
    rows = "\n".join(f"| {d.name} | {d.score} | {d.reason} |" for d in score.dimensions)
    gates = "\n".join(
        f"- {'✅' if g.passed else '❌'} **{g.name}** — {g.reason}" for g in score.gates
    )
    return (
        f"**Score: {score.headline()}**\n\n"
        "| dimension | score | reason |\n| --- | --- | --- |\n"
        f"{rows}\n\n"
        f"{gates}\n"
    )


def build_report(report: RunReport) -> str:
    out = [
        f"# Build Report — {report.topic}",
        "",
        f"_Run `{report.run_id}` · provider `{report.provider}` · {report.generated}_",
        "",
        "> Scores are the engine's own (LLM-as-judge). They're **calibration-pending** — "
        "correct them and the rubric tunes over time.",
        "",
        "## Scoreboard",
        "",
        "| level | adds | quality | gates | what changed |",
        "| --- | --- | --- | --- | --- |",
    ]
    for lvl in report.levels:
        s = lvl.score
        out.append(
            f"| {lvl.level} {lvl.label} | {lvl.adds} | {s.quality_avg}/10 | "
            f"{s.gates_passed}/{s.gates_total} | {s.delta_vs_prev or '—'} |"
        )
    out.append("")

    prev = None
    for lvl in report.levels:
        out += [
            f"## {lvl.level} — {lvl.label}",
            "",
            f"*Adds: {lvl.adds}. Inputs: {', '.join(lvl.inputs_active)}.*",
            "",
        ]
        out += ["**Post:**", "", "```", lvl.draft, "```", ""]
        out += [_score_block(lvl.score), ""]
        if prev is not None:
            out += ["**Diff vs previous level:**", "", "```diff", _diff(prev, lvl.draft), "```", ""]
        prev = lvl.draft

    out += ["## Places to refine", ""]
    out += [f"{n}. {p}" for n, p in enumerate(compute_places_to_refine(report.levels), 1)]
    out += [
        "",
        "## Method",
        "",
        "Same idea held constant; one input tier added per level (online → +docs → +typed → "
        "+persona → +specifics → +eval pass). Each draft scored against the shared rubric "
        "(six hard gates + nine 0–10 dimensions). The +eval pass is the Writer's Council "
        "revising to a 9/10 target with a Reflexion stop rule. No facts or numbers were "
        "invented; gaps are flagged above, not filled.",
    ]
    return "\n".join(out).rstrip() + "\n"


def write_report(report: RunReport) -> Path:
    path = RUNS_DIR / report.run_id / "report.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(build_report(report), encoding="utf-8")
    return path
