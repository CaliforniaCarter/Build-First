"""Local-first post storage: save writes a folder, list reads it back, status persists."""

import json

from engine.blocks.intake import ContentIdea, Intake
from engine.post import PostResult
from engine.rubric.schemas import DIM_NAMES, GATE_NAMES, Score
from engine.store import list_posts, save_post, set_status


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
    assert pdir.name == "my-second-brain"

    posts = list_posts(base=tmp_path)
    assert len(posts) == 1
    assert posts[0]["topic"] == "My Second Brain!!!"
    assert posts[0]["score"]["gates_passed"] == 5  # no_slop failed
    assert posts[0]["open_gates"] == ["no_slop"]


def test_status_defaults_draft_and_persists(tmp_path):
    intake = Intake(name="Tester", idea=ContentIdea(topic="My Post"))
    pdir = save_post(
        PostResult(first_draft="d", final_draft="v1", score=_score()),
        intake,
        "2026-06-29",
        base=tmp_path,
    )
    meta = json.loads((pdir / "post.json").read_text(encoding="utf-8"))
    assert meta["status"] == "draft" and meta["created"] == "2026-06-29"

    set_status(pdir.name, "posted", base=tmp_path)
    save_post(
        PostResult(first_draft="d", final_draft="v2", score=_score()),
        intake,
        "2026-06-30",
        base=tmp_path,
    )
    meta2 = json.loads((pdir / "post.json").read_text(encoding="utf-8"))
    assert meta2["status"] == "posted"  # preserved across the update
    assert meta2["created"] == "2026-06-29" and meta2["updated"] == "2026-06-30"
