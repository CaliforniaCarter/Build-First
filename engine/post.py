"""The product flow — make ONE final post (the thing you actually use).

This is deliberately separate from the ablation ladder (engine/ablation.py), which
is the build-time vetting lab. The product uses ALL your inputs at once: draft the
post, let the Writer's Council polish it to the rubric, attach receipts, score it
once, and hand it to you to approve. The engine never posts on its own.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field

from .ablation import context_for, load_layers  # shared context helpers
from .blocks import council
from .blocks import draft as draft_block
from .blocks import receipts as receipts_block
from .blocks.intake import Intake
from .config import RUNS_DIR
from .providers.base import Provider
from .rubric.schemas import Score
from .rubric.shared import build_score_prompt, parse_score

# The product uses every input at once (the lab adds them one tier at a time).
ALL_INPUTS = ["online", "docs", "typed", "persona", "specifics"]


@dataclass
class PostResult:
    first_draft: str
    final_draft: str
    score: Score
    proof: list[str] = field(default_factory=list)
    redactions: list[str] = field(default_factory=list)
    council_log: list[dict] = field(default_factory=list)


def evaluate(
    text: str,
    intake: Intake,
    persona_md: str,
    layers: str,
    provider: Provider,
    score_stage: str = "score_post",
    prev: str | None = None,
) -> tuple[str, list[str], list[str], Score]:
    """Attach receipts (+ redact) and score a piece of text. Shared by post and revise."""
    final_draft, proof, redactions = receipts_block.attach_receipts(text, intake)
    score = parse_score(
        provider.complete(score_stage, build_score_prompt(final_draft, persona_md, layers, prev))
    )
    return final_draft, proof, redactions, score


def make_post(intake: Intake, persona_md: str, provider: Provider, run_id: str) -> PostResult:
    layers = load_layers()
    run_dir = RUNS_DIR / run_id / "post"
    run_dir.mkdir(parents=True, exist_ok=True)

    ctx = context_for(ALL_INPUTS, intake)
    prompt = draft_block.build_draft_prompt(
        intake.idea.topic,
        ctx,
        persona_md,
        layers,
        intake.output.hard_nevers,
        intake.output.channels,
    )
    first_draft = draft_block.draft("draft_post", prompt, provider)

    polished, clog = council.revise(first_draft, persona_md, layers, provider)
    final_draft, proof, redactions, score = evaluate(polished, intake, persona_md, layers, provider)

    (run_dir / "first_draft.md").write_text(first_draft, encoding="utf-8")
    (run_dir / "final.md").write_text(final_draft, encoding="utf-8")
    (run_dir / "score.json").write_text(score.model_dump_json(indent=2), encoding="utf-8")
    if clog:
        (run_dir / "council_log.json").write_text(json.dumps(clog, indent=2), encoding="utf-8")
    if proof or redactions:
        (run_dir / "receipts.json").write_text(
            json.dumps({"proof": proof, "redacted": redactions}, indent=2), encoding="utf-8"
        )

    return PostResult(first_draft, final_draft, score, proof, redactions, clog)


def open_gaps(score: Score) -> list[str]:
    """Failing hard gates — what the post still needs before it's ready (e.g. a real number)."""
    return [f"{g.name}: {g.reason}" for g in score.gates if not g.passed]
