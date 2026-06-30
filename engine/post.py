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
from .blocks import proof as proof_block
from .blocks import receipts as receipts_block
from .blocks.intake import Intake
from .blocks.proof import ProofReport
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
    proof_report: ProofReport | None = None


def evaluate(
    text: str,
    intake: Intake,
    persona_md: str,
    layers: str,
    provider: Provider,
    score_stage: str = "score_post",
    prev: str | None = None,
) -> tuple[str, list[str], list[str], Score, ProofReport]:
    """Attach receipts (+ redact), run the deterministic proof check, and score. Shared by post and revise."""
    final_draft, proof, redactions = receipts_block.attach_receipts(text, intake)
    report = proof_block.proof_report(final_draft, proof, redactions, intake)
    score = parse_score(
        provider.complete(score_stage, build_score_prompt(final_draft, persona_md, layers, prev))
    )
    return final_draft, proof, redactions, score, report


def make_post(
    intake: Intake,
    persona_md: str,
    provider: Provider,
    run_id: str,
    recent_openings: list[str] = (),
) -> PostResult:
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
        recent_openings,
    )
    first_draft = draft_block.draft("draft_post", prompt, provider)

    polished, clog = council.revise(first_draft, persona_md, layers, provider)
    final_draft, proof, redactions, score, report = evaluate(
        polished, intake, persona_md, layers, provider
    )

    (run_dir / "first_draft.md").write_text(first_draft, encoding="utf-8")
    (run_dir / "final.md").write_text(final_draft, encoding="utf-8")
    (run_dir / "score.json").write_text(score.model_dump_json(indent=2), encoding="utf-8")
    if clog:
        (run_dir / "council_log.json").write_text(json.dumps(clog, indent=2), encoding="utf-8")
    if proof or redactions:
        (run_dir / "receipts.json").write_text(
            json.dumps({"proof": proof, "redacted": redactions}, indent=2), encoding="utf-8"
        )

    return PostResult(first_draft, final_draft, score, proof, redactions, clog, report)


def make_options(
    intake: Intake,
    persona_md: str,
    provider: Provider,
    run_id: str,
    n: int = 2,
    recent_openings: list[str] = (),
) -> list[PostResult]:
    """Draft n variations in deliberately different shapes and score each (no council yet).

    The product hands you a few options to pick from; the chosen one gets polished (see polish).
    """
    layers = load_layers()
    run_dir = RUNS_DIR / run_id / "post"
    run_dir.mkdir(parents=True, exist_ok=True)
    ctx = context_for(ALL_INPUTS, intake)
    results: list[PostResult] = []
    avoid = list(recent_openings)
    for i in range(n):
        prompt = draft_block.build_draft_prompt(
            intake.idea.topic,
            ctx,
            persona_md,
            layers,
            intake.output.hard_nevers,
            intake.output.channels,
            avoid,
        )
        text = draft_block.draft(f"draft_post_{i}", prompt, provider)
        final, proof, redactions, score, report = evaluate(
            text, intake, persona_md, layers, provider, f"score_post_{i}"
        )
        results.append(PostResult(text, final, score, proof, redactions, [], report))
        if text.strip():
            avoid = avoid + [text.splitlines()[0]]  # the next option must differ
        (run_dir / f"option_{i}.md").write_text(final, encoding="utf-8")
    return results


def polish(text: str, intake: Intake, persona_md: str, provider: Provider) -> PostResult:
    """Run the Writer's Council on the chosen option, attach receipts, re-score. For `tb pick`."""
    layers = load_layers()
    polished, clog = council.revise(text, persona_md, layers, provider)
    final, proof, redactions, score, report = evaluate(
        polished, intake, persona_md, layers, provider, "score_pick"
    )
    return PostResult(text, final, score, proof, redactions, clog, report)
