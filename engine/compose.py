"""Compose — the fast, single-post path the app's "write a post" screen uses.

The ablation ladder (ablation.py) is the eval: it drafts 6 times to show what each input
tier is worth. That's the moat, but it's ~12 model calls — too slow for an in-app click.
This is the production path: build context once with everything we know, draft in voice,
run the Writer's Council to threshold, attach receipts, score once. Pure reuse of the same
blocks the ladder uses, so a composed post is graded by the identical rubric.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .ablation import context_for, load_layers
from .blocks import council
from .blocks import draft as draft_block
from .blocks import receipts as receipts_block
from .blocks.intake import Intake
from .providers.base import Provider
from .rubric.schemas import Score
from .rubric.shared import build_score_prompt, parse_score


@dataclass
class ComposeResult:
    body: str  # the redacted, council-revised post
    score: Score
    proof: list[str] = field(default_factory=list)
    redactions: list[str] = field(default_factory=list)
    council_log: list[dict] = field(default_factory=list)


def compose_post(
    intake: Intake, work: str, persona_md: str, provider: Provider
) -> ComposeResult:
    """Turn `work` (what the person did) into one in-voice, scored post.

    `work` becomes the idea topic; any specifics already on `intake.idea`
    (scene, number, mechanism, proof…) are folded in via the 'specifics' context tier.
    """
    idea = intake.idea.model_copy(update={"topic": work or intake.idea.topic})
    intake = intake.model_copy(update={"idea": idea})

    layers = load_layers()
    ctx = context_for(["online", "docs", "typed", "specifics"], intake)
    prompt = draft_block.build_draft_prompt(
        intake.idea.topic,
        ctx,
        persona_md or None,
        layers,
        intake.output.hard_nevers,
        intake.output.channels,
    )

    drafted = draft_block.draft("compose_draft", prompt, provider)
    revised, clog = council.revise(drafted, persona_md, layers, provider)
    body, proof, redactions = receipts_block.attach_receipts(revised, intake)

    score = parse_score(
        provider.complete(
            "compose_score",
            build_score_prompt(body, persona_md or "(no persona)", layers, None),
        )
    )
    return ComposeResult(
        body=body, score=score, proof=proof, redactions=redactions, council_log=clog
    )
