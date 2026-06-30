"""Request/response models + the Score serializer.

`serialize_score` exists because Score's useful numbers (quality_avg, gates_passed,
passes_threshold, headline) are computed @property values that `model_dump()` omits.
"""

from __future__ import annotations

from pydantic import BaseModel

from engine.rubric.schemas import Score


# --- online scan (scraper pending) -------------------------------------------
class ScanRequest(BaseModel):
    linkedin: str = ""
    x: str = ""


class ScanProfile(BaseModel):
    handle: str = ""
    post_count: int = 0
    posts: list[dict] = []


class ScanResponse(BaseModel):
    linkedin: ScanProfile
    x: ScanProfile
    pending: bool = False  # true while the engine scraper module is not yet wired


# --- profile / persona -------------------------------------------------------
class PersonaMdBody(BaseModel):
    persona_md: str


# --- compose / posts ---------------------------------------------------------
class ComposeRequest(BaseModel):
    work: str
    save: bool = True


class OptionsRequest(BaseModel):
    work: str


class PickRequest(BaseModel):
    chosen: str  # the option body the user picked
    rejected_opening: str = ""  # first line of the option they passed on
    why: str = ""  # optional reason — the strongest learning signal
    topic: str = ""  # what the post was about (for the saved record)


class PostPatch(BaseModel):
    body: str | None = None
    rescore: bool = False


def serialize_score(s: Score) -> dict:
    d = s.model_dump()
    d.update(
        quality_avg=s.quality_avg,
        gates_passed=s.gates_passed,
        gates_total=s.gates_total,
        passes_threshold=s.passes_threshold,
        headline=s.headline(),
    )
    return d
