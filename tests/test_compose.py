"""The web path's two new engine capabilities: persona insights + fast compose.

A FakeProvider returns canned text per stage so we can test the orchestration and the
verbatim-quote guard without a model or an API key.
"""

import json

from engine.blocks.intake import ContentIdea, Intake, Voice
from engine.blocks.persona import build_persona_insights
from engine.compose import compose_post
from engine.providers.base import Provider
from engine.rubric.schemas import DIM_NAMES, GATE_NAMES


class FakeProvider(Provider):
    name = "fake"

    def __init__(self, by_stage: dict[str, str]):
        # keys are stage prefixes (e.g. "compose_score"), matched by startswith
        self.by_stage = by_stage

    def complete(self, stage: str, prompt: str) -> str:
        for prefix, text in self.by_stage.items():
            if stage.startswith(prefix):
                return text
        raise KeyError(f"no fake response for stage {stage!r}")


def _valid_score_json() -> str:
    return json.dumps(
        {
            "gates": [{"name": n, "passed": True, "reason": "ok"} for n in GATE_NAMES],
            "dimensions": [{"name": n, "score": 9, "reason": "ok"} for n in DIM_NAMES],
            "delta_vs_prev": "baseline",
        }
    )


def test_persona_insights_keeps_only_verbatim_quotes():
    intake = Intake(
        name="Carter",
        idea=ContentIdea(topic="t"),
        voice=Voice(answers={"weekend?": "honestly nothing crazy — slept in and made coffee"}),
    )
    insights_json = json.dumps(
        [
            # real: an exact span of the answer (lowercased here on purpose)
            {"observation": "writes like he talks", "verbatim_quote": "HONESTLY nothing crazy",
             "trait_label": "lowercase"},
            # invented: never appears in their words → must be dropped
            {"observation": "made up", "verbatim_quote": "synergistic paradigm shift",
             "trait_label": "x"},
        ]
    )
    provider = FakeProvider({"persona_insights": insights_json})

    out = build_persona_insights(intake, provider)

    assert len(out) == 1
    # the returned quote is the person's ORIGINAL casing, not the model's
    assert out[0].verbatim_quote == "honestly nothing crazy"
    assert out[0].trait_label == "lowercase"


def test_compose_post_returns_scored_post():
    intake = Intake(name="Carter", idea=ContentIdea(topic="placeholder"))
    provider = FakeProvider(
        {
            "compose_draft": "shipped the thing today. it broke. i fixed it.",
            "council_pass1": json.dumps(
                {"critique": "good", "revised_draft": "shipped the thing today — it broke, i fixed it.",
                 "stop": True, "reason": "passes"}
            ),
            "compose_score": _valid_score_json(),
        }
    )

    result = compose_post(intake, "rebuilt onboarding in an afternoon", "lowercase, dry.", provider)

    assert "shipped the thing" in result.body
    assert result.score.gates_passed == len(GATE_NAMES)
    assert result.score.quality_avg == 9.0
    assert result.council_log and result.council_log[0]["stop"] is True
