"""The product path — make one good post (not the eval ladder).

`run_ablation` answers "what is each input worth" with ~13 model calls; that's the eval/demo.
When you just want a post, you want the best-tier context once, drafted, then revised by the
Writer's Council. That's this module: ~5 calls, the same blocks, with progress callbacks so a
UI can stream it. It still ends at the human gate — drafts only, never auto-post.
"""

from __future__ import annotations

import json
from typing import Callable

from pydantic import BaseModel

from .ablation import context_for, load_layers
from .blocks import council
from .blocks import draft as draft_block
from .blocks import gate
from .blocks import receipts as receipts_block
from .blocks.intake import Intake
from .config import RUNS_DIR
from .providers.base import Provider
from .rubric.schemas import Score
from .rubric.shared import build_score_prompt, parse_score

# Everything the engine knows, all at once (the L4/L5-equivalent context).
BEST_TIER = ["online", "docs", "typed", "persona", "specifics"]

# (stage, payload) — coarse progress: draft / council / council_pass / score / done.
StageCb = Callable[[str, dict], None] | None


class PostResult(BaseModel):
    run_id: str
    draft: str
    score: Score | None = None
    council_log: list[dict] = []
    proof: list[str] = []
    redactions: list[str] = []
    draft_path: str


def generate_post(
    intake: Intake,
    persona_md: str,
    provider: Provider,
    run_id: str,
    *,
    do_score: bool = True,
    council_passes: int | None = None,
    on_stage: StageCb = None,
) -> PostResult:
    """Draft -> Writer's Council -> receipts -> (score) -> human gate. Drafts only."""

    def emit(stage: str, **payload) -> None:
        if on_stage:
            on_stage(stage, payload)

    run_dir = RUNS_DIR / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    layers = load_layers()
    ctx = context_for(BEST_TIER, intake)

    emit("draft", status="start")
    prompt = draft_block.build_draft_prompt(
        intake.idea.topic,
        ctx,
        persona_md,
        layers,
        intake.output.hard_nevers,
        intake.output.channels,
    )
    base = draft_block.draft("draft", prompt, provider)
    emit("draft", status="done", text=base)

    emit("council", status="start")
    revise_kwargs = {} if council_passes is None else {"max_passes": council_passes}
    final, clog = council.revise(
        base,
        persona_md,
        layers,
        provider,
        on_pass=lambda n, entry: emit(
            "council_pass", n=n, stop=entry["stop"], reason=entry["reason"]
        ),
        **revise_kwargs,
    )
    emit("council", status="done", passes=len(clog))

    final, proof, redactions = receipts_block.attach_receipts(final, intake)

    score: Score | None = None
    if do_score:
        emit("score", status="start")
        score = parse_score(
            provider.complete("score", build_score_prompt(final, persona_md, layers, None))
        )
        emit("score", status="done", headline=score.headline())

    # Persist alongside the gate's draft.md (same shape as an ablation level dir).
    if clog:
        (run_dir / "council_log.json").write_text(json.dumps(clog, indent=2), encoding="utf-8")
    if score is not None:
        (run_dir / "score.json").write_text(score.model_dump_json(indent=2), encoding="utf-8")
    if proof or redactions:
        (run_dir / "receipts.json").write_text(
            json.dumps({"proof": proof, "redacted": redactions}, indent=2), encoding="utf-8"
        )

    draft_path = gate.human_gate(final, run_dir)  # writes draft.md + clipboard; never posts
    emit("done", run_id=run_id, draft=final, headline=(score.headline() if score else None))

    return PostResult(
        run_id=run_id,
        draft=final,
        score=score,
        council_log=clog,
        proof=proof,
        redactions=redactions,
        draft_path=str(draft_path),
    )
