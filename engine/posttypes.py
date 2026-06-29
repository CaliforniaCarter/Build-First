"""Post types — the editable 'settings page' for each kind of post.

A post type is platform x type x content plus a hard character cap and a soft length.
Structure/shape stay AI-interpreted (read from the layers); the only thing we pin is the
character count, which is always enforced. All layers apply to every type.

Settings live in `data/posttypes.json` (committed, hand-editable). The BUILTINS below are
the fallback so the engine runs even if that file is missing; the file overrides/extends
them by key, so adding a platform or a new type is a small JSON edit, not a code change.
"""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel

from .config import DATA_DIR


class PostType(BaseModel):
    key: str
    output: str  # platform — "LinkedIn" | "X/Twitter" | "Instagram"
    type: str = "post"  # "post" | "connection request" | ...
    content: str = "words"  # "words" now; "carousel" / "video" can branch later
    character_count: int = 0  # hard max chars; 0 = no limit. Always enforced when > 0.
    length: str = ""  # soft target (guidance, not enforced)

    def describe(self) -> str:
        """The plain-language label the model interprets, e.g. 'a post for LinkedIn'."""
        desc = f"a {self.type or 'post'} for {self.output}"
        if self.content and self.content != "words":
            desc += f" as a {self.content}"
        return desc


# Fallback defaults. Character caps are the real platform limits (edit in data/posttypes.json).
BUILTINS: dict[str, PostType] = {
    "linkedin_post": PostType(
        key="linkedin_post",
        output="LinkedIn",
        character_count=3000,
        length="medium — front-load the value, as long as it needs and no longer",
    ),
    "x_post": PostType(
        key="x_post",
        output="X/Twitter",
        character_count=280,
        length="one breath — very short",
    ),
    "instagram_post": PostType(
        key="instagram_post",
        output="Instagram",
        character_count=2200,
        length="short, punchy caption",
    ),
}


def load_post_types(path: Path | None = None) -> dict[str, PostType]:
    """Builtins overlaid with data/posttypes.json (the settings page), if present."""
    path = path or (DATA_DIR / "posttypes.json")
    types = dict(BUILTINS)
    if path.exists():
        for key, cfg in json.loads(path.read_text(encoding="utf-8")).items():
            types[key] = PostType(key=key, **cfg)
    return types


def get_post_type(key: str, path: Path | None = None) -> PostType:
    types = load_post_types(path)
    try:
        return types[key]
    except KeyError:
        raise ValueError(f"unknown post type: {key!r} (known: {', '.join(types)})") from None
