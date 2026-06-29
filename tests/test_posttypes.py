"""Post-type settings: builtins, the editable data/posttypes.json overlay, and describe()."""

import json

import pytest

from engine.posttypes import BUILTINS, get_post_type, load_post_types


def test_builtins_ship_the_three_platforms():
    assert {"linkedin_post", "x_post", "instagram_post"} <= set(BUILTINS)


def test_describe_reads_as_plain_language():
    assert BUILTINS["linkedin_post"].describe() == "a post for LinkedIn"


def test_settings_file_overrides_and_extends(tmp_path):
    cfg = {
        "x_post": {"output": "X/Twitter", "character_count": 300},  # override the cap
        "tiktok_caption": {"output": "TikTok", "character_count": 150},  # brand-new type
    }
    path = tmp_path / "posttypes.json"
    path.write_text(json.dumps(cfg), encoding="utf-8")
    types = load_post_types(path)
    assert types["x_post"].character_count == 300  # file wins over the builtin 280
    assert types["tiktok_caption"].output == "TikTok"  # new type merged in
    assert "linkedin_post" in types  # untouched builtin still present


def test_unknown_type_raises():
    with pytest.raises(ValueError):
        get_post_type("myspace_bulletin")
