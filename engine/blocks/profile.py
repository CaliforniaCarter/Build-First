"""Profile + context — deterministic. Pure restatement of the intake, nothing invented.

profile.md = stable identity (who you are). context.md = today's specific work.
These are templated straight from the intake so they can never hallucinate. The draft draws the
same facts from the intake; these are the human-readable mirror you (and the UI) review via
`tb inspect`.
"""

from __future__ import annotations

from ..config import PROFILES_DIR
from .intake import Intake


def build_profile(intake: Intake) -> str:
    t, o = intake.typed, intake.online
    out = [
        "# profile.md",
        "",
        "_Stable identity — restated from your intake. Nothing invented._",
        "",
        "## Identity",
        t.identity or "—",
        "",
    ]
    if t.known_for:
        out += ["## Known for", t.known_for, ""]
    foot = []
    if o.linkedin:
        foot.append(f"- LinkedIn: {o.linkedin}")
    if o.x:
        foot.append(f"- X: {o.x}")
    if o.other:
        foot.append(f"- Other: {o.other}")
    foot.append(
        f"- Start: {'cold start (no existing posts)' if o.cold_start else o.existing_posts}"
    )
    out += ["## Public footprint", *foot, ""]
    if t.background:
        out += ["## Unique background", t.background, ""]
    if t.beliefs:
        out += ["## Beliefs & hot takes", t.beliefs, ""]
    if t.lessons:
        out += ["## Lessons learned the hard way", t.lessons, ""]
    return "\n".join(out).rstrip() + "\n"


def build_context(intake: Intake) -> str:
    i = intake.idea
    out = [
        "# context.md",
        "",
        "_Today's specific work — what this post is about. Restated from your intake._",
        "",
        "## Topic",
        i.topic,
        "",
    ]
    if i.take:
        out += ["## The take", i.take, ""]
    if i.mechanism:
        out += ["## How it works", i.mechanism, ""]
    if i.scene:
        out += ["## The scene", i.scene, ""]
    out += ["## Real number", i.number or "_(none provided — see places to refine)_", ""]
    if i.lesson:
        out += ["## Non-obvious lesson", i.lesson, ""]
    if i.only_you:
        out += ["## Only-you angle", i.only_you, ""]
    if i.proof:
        out += ["## Proof / receipts", *[f"- {p}" for p in i.proof], ""]
    if i.close:
        out += ["## Close", i.close, ""]
    return "\n".join(out).rstrip() + "\n"


def write_profile_docs(intake: Intake) -> dict[str, object]:
    PROFILES_DIR.mkdir(parents=True, exist_ok=True)
    profile_path = PROFILES_DIR / "profile.md"
    context_path = PROFILES_DIR / "context.md"
    profile_path.write_text(build_profile(intake), encoding="utf-8")
    context_path.write_text(build_context(intake), encoding="utf-8")
    return {"profile": profile_path, "context": context_path}
