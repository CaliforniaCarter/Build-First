"""Brief — the one editable spec a post is generated from. Deterministic, no LLM.

Same philosophy as profile.py: pure restatement of the intake (plus the post-type
defaults), nothing invented. The Brief bundles the swappable knobs as structured fields
(structure / cadence / tone / format) and points at the big prose voice context
(persona.md) rather than inlining it — so the JSON stays small and hand-editable.

`bf generate` writes brief.json (canonical) + brief.md (readable), pauses for you to
edit, then renders the draft prompt straight from the edited brief.
"""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel

from ..posttypes import get_post_type
from .intake import ContentIdea, Intake


class Brief(BaseModel):
    post_type: str
    output: str  # what to write, in plain language — e.g. "a LinkedIn post" (model interprets)
    constraints: list[str] = []  # hard rules only (char limits, etc.); soft form is interpreted
    content_idea: ContentIdea  # reuse the intake model — no new idea fields
    tone: list[str] = []  # soft voice hints, from the intake
    cadence: str = ""
    length: str = ""
    voice_ref: str = ""  # pointer to the prose voice doc (kept out of the JSON)
    banned: list[str] = []
    hard_nevers: list[str] = []


def build_brief(intake: Intake, post_type: str, voice_ref: str = "profiles/persona.md") -> Brief:
    """Compose a Brief from the intake + the post-type template. Intake wins on overlap."""
    pt = get_post_type(post_type)
    v, o = intake.voice, intake.output
    return Brief(
        post_type=pt.key,
        output=o.format or pt.output,  # intake.output.format overrides the type's label
        constraints=list(pt.constraints),
        content_idea=intake.idea,
        tone=list(v.tone_words),
        cadence=v.sentence_length,
        length=o.length,
        voice_ref=voice_ref,
        banned=list(v.banned),
        hard_nevers=list(o.hard_nevers),
    )


def render_brief_md(brief: Brief) -> str:
    """A readable view of the brief (edit brief.json — this is the eyeball copy)."""
    i = brief.content_idea
    out = [
        "# brief.md",
        "",
        "_The post spec. Edit `brief.json`, then re-run `bf generate`. Deterministic — nothing invented._",
        "",
        f"- **Post type:** {brief.post_type}",
        f"- **Output:** {brief.output}",
        f"- **Constraints (hard):** {'; '.join(brief.constraints) or '—'}",
        f"- **Cadence:** {brief.cadence or '—'}",
        f"- **Tone:** {', '.join(brief.tone) or '—'}",
        f"- **Length:** {brief.length or '—'}",
        f"- **Voice ref:** {brief.voice_ref or '—'}",
        f"- **Banned:** {', '.join(brief.banned) or '—'}",
        f"- **Hard nevers:** {', '.join(brief.hard_nevers) or '—'}",
        "",
        "## Content idea",
        f"- Topic: {i.topic or '—'}",
    ]
    for label, val in (
        ("Take", i.take),
        ("How it works", i.mechanism),
        ("Scene", i.scene),
        ("Number", i.number),
        ("Lesson", i.lesson),
        ("Only-you", i.only_you),
        ("Close", i.close),
    ):
        if val:
            out.append(f"- {label}: {val}")
    if i.proof:
        out += ["- Proof:", *[f"  - {p}" for p in i.proof]]
    return "\n".join(out).rstrip() + "\n"


def write_brief(brief: Brief, run_dir: Path) -> dict[str, Path]:
    run_dir = Path(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)
    json_path = run_dir / "brief.json"
    md_path = run_dir / "brief.md"
    json_path.write_text(brief.model_dump_json(indent=2), encoding="utf-8")
    md_path.write_text(render_brief_md(brief), encoding="utf-8")
    return {"json": json_path, "md": md_path}


def load_brief(run_dir: Path) -> Brief:
    return Brief.model_validate_json((Path(run_dir) / "brief.json").read_text(encoding="utf-8"))
