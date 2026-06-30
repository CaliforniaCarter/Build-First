"""The onboarding scaffolding is data: the shipped engine/onboarding.json must load + validate,
and the hardcoded audience default must only ever fill blanks (a real answer always wins).
"""

from engine.onboarding import load_onboarding, render_audience


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


def test_audience_renders_to_the_draft_layer():
    cfg = load_onboarding()
    prose = render_audience(cfg.defaults.audience)
    # the editable JSON audience drives drafts as prose (rendered to the draft layer)
    assert "Audience layer" in prose
    assert cfg.defaults.audience.writing_for.split()[0] in prose  # the 'who' makes it in
    assert "anatomy" in prose.lower()  # the playbook moves make it in
    # empty fields are skipped, not rendered as blanks
    assert "\n\n\n" not in prose
