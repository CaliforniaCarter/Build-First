"""Local-first post storage: save writes a folder, list reads it back, status persists."""

import json

from engine.blocks.intake import ContentIdea, Intake
from engine.post import PostResult
from engine.rubric.schemas import DIM_NAMES, GATE_NAMES, Score
from engine.store import (
    clear_local_data,
    list_posts,
    posting_streak,
    save_post,
    set_status,
    shipped_count,
)


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


def test_shipped_count_and_streak_are_derived(tmp_path):
    def _save(topic, date, status):
        save_post(
            PostResult(first_draft="d", final_draft="v", score=_score()),
            Intake(name="T", idea=ContentIdea(topic=topic)),
            date,
            status=status,
            base=tmp_path,
        )

    _save("post one", "2026-06-29", "posted")
    _save("post two", "2026-06-30", "posted")
    _save("post three", "2026-06-30", "draft")  # a draft doesn't count
    posts = list_posts(base=tmp_path)
    assert shipped_count(posts) == 2
    assert posting_streak(posts) == 2  # 06-29 and 06-30 are consecutive posted days
    assert posting_streak([]) == 0


def test_clear_local_data_resets_to_cold_start(tmp_path):
    prof, data, posts, runs = (tmp_path / n for n in ("profiles", "data", "posts", "runs"))
    for d in (prof, data, posts, runs):
        d.mkdir()
    (prof / "voice.json").write_text("{}")
    (prof / ".gitkeep").write_text("")
    (data / "intake.json").write_text("{}")
    (data / "signals.json").write_text("[]")
    (posts / "my-post").mkdir()
    (posts / "my-post" / "final.md").write_text("hi")
    (posts / ".gitkeep").write_text("")
    (runs / "r1").mkdir()

    removed = clear_local_data(prof, data, posts, runs)

    assert not (prof / "voice.json").exists()
    assert not (data / "intake.json").exists()
    assert not (posts / "my-post").exists()
    assert not (runs / "r1").exists()
    assert (prof / ".gitkeep").exists() and (posts / ".gitkeep").exists()  # .gitkeep kept
    assert "voice.json" in removed and "posts/my-post" in removed
