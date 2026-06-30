"""End-to-end: make_post and the shared evaluate/revise paths run through the stub and
produce a valid scored post (no provider mocking — the stub is the offline engine)."""

from engine.ablation import load_layers
from engine.blocks.draft import build_draft_prompt
from engine.blocks.intake import ContentIdea, Intake
from engine.post import evaluate, make_options, make_post
from engine.providers.stub import StubProvider
from engine.revise import revise


def _intake() -> Intake:
    return Intake(name="Tester", idea=ContentIdea(topic="a topic", number="42"))


def test_make_post_end_to_end(tmp_path, monkeypatch):
    monkeypatch.setattr("engine.post.RUNS_DIR", tmp_path)  # don't write into the repo
    result = make_post(_intake(), "persona", StubProvider(), "qa")
    assert result.final_draft
    assert result.score.gates_total == 6
    assert len(result.score.dimensions) == 9
    assert (tmp_path / "qa" / "post" / "final.md").exists()


def test_evaluate_and_revise_paths():
    intake = _intake()
    layers = load_layers()
    revised = revise("the post", "make it shorter", "persona", layers, [], StubProvider())
    final, proof, redactions, score = evaluate(
        revised, intake, "persona", layers, StubProvider(), "score_revise"
    )
    assert final
    assert len(score.dimensions) == 9


def test_draft_prompt_varies_from_recent_posts():
    p = build_draft_prompt(
        "topic", "ctx", "voice", "layers", [], ["LinkedIn"], ["I've quit every second brain"]
    )
    assert "I've quit every second brain" in p  # the recent opening is fed in
    assert "vary" in p.lower()  # and it's told to vary the shape


def test_make_options_produces_two_scored_variations(tmp_path, monkeypatch):
    monkeypatch.setattr("engine.post.RUNS_DIR", tmp_path)
    opts = make_options(_intake(), "persona", StubProvider(), "qa", n=2)
    assert len(opts) == 2
    assert all(r.final_draft and len(r.score.dimensions) == 9 for r in opts)
    assert (tmp_path / "qa" / "post" / "option_0.md").exists()
    assert (tmp_path / "qa" / "post" / "option_1.md").exists()
