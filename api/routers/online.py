"""Online scan — find the person's recent posts from their handles.

PENDING ENGINE MODULE: the scraper is being added to the engine. Until it lands, this
route returns the real contract shape with empty results and pending=true (it never
invents a post count). When the engine function exists, call it here and the front-end
needs no change. A non-empty result writes online.existing_posts + flips cold_start.
"""

from __future__ import annotations

from fastapi import APIRouter

from ..deps import read_intake, write_intake
from ..schemas import ScanProfile, ScanRequest, ScanResponse

router = APIRouter(prefix="/api/online", tags=["online"])


@router.post("/scan")
def scan(req: ScanRequest) -> ScanResponse:
    # TODO(engine): replace with the real scraper, e.g. engine.online.scan(linkedin, x).
    linkedin = ScanProfile(handle=req.linkedin, post_count=0, posts=[])
    x = ScanProfile(handle=req.x, post_count=0, posts=[])

    total = linkedin.post_count + x.post_count
    if total > 0:  # real corpus found → fold into the intake
        intake = read_intake()
        if intake is not None:
            corpus = "\n\n".join(
                p.get("text", "") for prof in (linkedin, x) for p in prof.posts
            )
            intake.online.linkedin = req.linkedin or intake.online.linkedin
            intake.online.x = req.x or intake.online.x
            intake.online.existing_posts = corpus
            intake.online.cold_start = False
            write_intake(intake)

    return ScanResponse(linkedin=linkedin, x=x, pending=total == 0)
