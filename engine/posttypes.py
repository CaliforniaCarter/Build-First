"""Post types — the deterministic seam for 'grab different fields by post type'.

Each type names the swappable knobs (structure, cadence, length, channel) and which
prose layer files apply. The structure is the post skeleton, promoted out of the prose
in `layers/audience_tenex.md` so it can be selected and edited as data, not buried text.

V1 ships one type. Adding `x_thread` / `lesson` later is one more entry in POST_TYPES.
"""

from __future__ import annotations

from pydantic import BaseModel


class PostType(BaseModel):
    key: str
    channel: str
    structure: list[str]  # ordered skeleton for this kind of post
    cadence: str  # default sentence rhythm (intake.voice.sentence_length overrides)
    length: str  # default length (intake.output.length overrides)
    layer_files: list[str]  # prose layers to load for this type


LINKEDIN_BUILD = PostType(
    key="linkedin_build",
    channel="LinkedIn",
    structure=[
        "Hook — a real moment or admission, or the build plus an analogy; front-load it",
        "The pain / the turn — concrete, with a real cost or something that didn't work",
        "The mechanism — in plain language, shown not just claimed",
        "What it looks like in practice — scannable",
        "One spiky, ownable claim plus the honest lesson, or the number",
        "A soft close — a real question — plus the proof / receipt",
    ],
    cadence="Short lines, one idea per line, generous white space; restraint wins.",
    length="As long as it needs and no longer; front-load the value.",
    layer_files=["format.md", "audience_tenex.md"],
)

POST_TYPES: dict[str, PostType] = {LINKEDIN_BUILD.key: LINKEDIN_BUILD}


def get_post_type(key: str) -> PostType:
    try:
        return POST_TYPES[key]
    except KeyError:
        raise ValueError(f"unknown post type: {key!r} (known: {', '.join(POST_TYPES)})") from None
