"""Local-first post storage: save writes a folder, list reads it back."""

from engine.blocks.intake import ContentIdea, Intake
from engine.post import PostResult
from engine.rubric.schemas import DIM_NAMES, GATE_NAMES, Score
from engine.store import list_posts, save_post


def _score() -> Score:
    return Score.model_validate(
        {
            "gates": [{"name": n, "passed": n != "no_slop", "reason": "x"} for n in GATE_NAMES],
            "dimensions": [{"name": n, "score": 8, "reason": "x"} for n in DIM_NAMES],
            "delta_vs_prev": "baseline",
        }
    )


def test_save_and_list_roundtrip(tmp_path):
    intake = Intake(name="Tester", idea=ContentIdea(topic="My Second Brain!!!"))
    result = PostResult(first_draft="d0", final_draft="final post", score=_score(), proof=["p1"])

    pdir = save_post(result, intake, "2026-06-29", base=tmp_path)
    assert (pdir / "final.md").read_text(encoding="utf-8") == "final post"
    assert pdir.name == "2026-06-29-my-second-brain"

    posts = list_posts(base=tmp_path)
    assert len(posts) == 1
    assert posts[0]["topic"] == "My Second Brain!!!"
    assert posts[0]["score"]["gates_passed"] == 5  # no_slop failed
    assert posts[0]["open_gates"] == ["no_slop"]
