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


def test_personalized_pick_is_generated_not_hardcoded():
    cfg = load_onboarding()
    picks = [q for q in cfg.active() if q.type == "adaptive_ab"]
    assert picks, "expected a personalized this-or-that question"
    for q in picks:
        # the two options are written from the person's own material, not shipped as leading
        # hardcoded examples — so the question carries a `generate` instruction, not `options`
        assert q.generate.strip(), "adaptive_ab must carry a generate instruction"
        assert q.writes_to  # the chosen example lands somewhere in intake


def test_audience_renders_to_the_draft_layer():
    cfg = load_onboarding()
    prose = render_audience(cfg.defaults.audience)
    # the editable JSON audience drives drafts as prose (rendered to the draft layer)
    assert "Audience layer" in prose
    assert cfg.defaults.audience.writing_for.split()[0] in prose  # the 'who' makes it in
    assert "anatomy" in prose.lower()  # the playbook moves make it in
    # empty fields are skipped, not rendered as blanks
    assert "\n\n\n" not in prose
