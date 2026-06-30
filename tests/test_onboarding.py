"""The onboarding scaffolding is data: the shipped engine/onboarding.json must load + validate,
and the hardcoded audience default must only ever fill blanks (a real answer always wins).
"""

from engine.blocks.intake import Audience
from engine.onboarding import OnboardingConfig, apply_audience_default, load_onboarding


def test_onboarding_json_loads_and_is_ordered():
    cfg = load_onboarding()  # the real shipped config — fails loudly if someone breaks it
    qs = cfg.active()
    assert qs, "expected at least one enabled question"
    assert [q.order for q in qs] == sorted(q.order for q in qs)
    assert all(q.enabled for q in qs)
    # the disabled adaptive follow-up is filtered out of the live flow
    assert "teach_followup" not in [q.id for q in qs]


def test_ab_pick_questions_carry_two_real_examples():
    cfg = load_onboarding()
    ab = [q for q in cfg.active() if q.type == "ab_pick"]
    assert ab, "expected ab_pick questions"
    for q in ab:
        assert len(q.options) == 2
        assert all(o.example.strip() for o in q.options)  # real content, never bare labels


def test_audience_default_only_fills_blanks():
    cfg = OnboardingConfig.model_validate(
        {
            "welcome": "hi",
            "defaults": {"audience": {"writing_for": "Tenex", "goal": "ship", "play_to": "fast"}},
        }
    )
    a = Audience(writing_for="my own crowd")  # already set — must not be overwritten
    changed = apply_audience_default(cfg, a)
    assert changed is True
    assert a.writing_for == "my own crowd"
    assert a.goal == "ship"  # blank got filled from the default
    assert a.play_to == "fast"
