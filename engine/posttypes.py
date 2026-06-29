"""Post types — kept light and AI-interpreted on purpose.

A post type is mostly a plain-language label ("a LinkedIn post") that the model reads
and interprets, plus the prose layers it should follow. We only pin down *hard*
constraints when they actually exist (e.g. an X character limit) — everything softer
(structure, rhythm) is left for the model to interpret from the layers, not prescribed.

V1 ships two. Adding another is one more entry in POST_TYPES.
"""

from __future__ import annotations

from pydantic import BaseModel


class PostType(BaseModel):
    key: str
    output: str  # plain-language label the model interprets, e.g. "a LinkedIn post"
    constraints: list[str] = []  # hard rules ONLY when they exist (char limits, etc.)
    layer_files: list[str]  # prose the model interprets for structure/voice


LINKEDIN = PostType(
    key="linkedin",
    output="a LinkedIn post",
    constraints=[],
    layer_files=["format.md", "audience_tenex.md"],
)

X = PostType(
    key="x",
    output="an X / Twitter post",
    constraints=["under 300 characters", "no thread — a single post"],
    layer_files=["format.md", "audience_tenex.md"],
)

POST_TYPES: dict[str, PostType] = {LINKEDIN.key: LINKEDIN, X.key: X}


def get_post_type(key: str) -> PostType:
    try:
        return POST_TYPES[key]
    except KeyError:
        raise ValueError(f"unknown post type: {key!r} (known: {', '.join(POST_TYPES)})") from None
