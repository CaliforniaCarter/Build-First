"""Draft — write the post from only what's known at this input level, in voice.

The ablation passes a different `context_block` (and maybe a persona) per level; the
prompt is otherwise identical, so the eval isolates what each input is worth.
"""

from __future__ import annotations

from ..providers.base import Provider
from .brief import Brief


def build_draft_prompt(
    topic: str,
    context_block: str,
    persona_md: str | None,
    layers: str,
    hard_nevers: list[str],
    channels: list[str],
) -> str:
    if persona_md:
        voice = f"VOICE — write in this voice and obey its never-do list:\n{persona_md}\n\n"
    else:
        voice = (
            "VOICE: none yet — write a clean, plain professional post (no fake personality).\n\n"
        )
    return (
        f"Write one post for {', '.join(channels) or 'LinkedIn'}. Output ONLY the post text, "
        "no preamble, no title, no hashtags.\n\n"
        f"TOPIC:\n{topic}\n\n"
        f"WHAT YOU KNOW (use only this — do not invent facts, numbers, or quotes):\n{context_block}\n\n"
        f"{voice}"
        f"LAYERS:\n{layers}\n\n"
        f"HARD NEVERS: {', '.join(hard_nevers) or '—'}\n"
        "Rules: no invented facts or numbers — if there's no real number, don't fake one. "
        "No slop phrases. Hook in the first line. One idea. Short lines."
    )


def build_draft_prompt_from_brief(brief: Brief, persona_md: str | None, layers: str) -> str:
    """Render the draft prompt from one inspectable Brief — the deterministic 'plug it in'.

    The prompt is now a pure function of the (hand-editable) brief, the voice doc, and the
    prose layers; no facts are sourced from anywhere else.
    """
    i = brief.content_idea
    idea = [f"Topic: {i.topic}"]
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
            idea.append(f"{label}: {val}")
    if i.proof:
        idea.append("Proof: " + "; ".join(i.proof))
    structure = "\n".join(f"  {n}. {s}" for n, s in enumerate(brief.structure, 1))

    if persona_md:
        voice = f"VOICE — write in this voice and obey its never-do list:\n{persona_md}\n\n"
    else:
        voice = (
            "VOICE: none yet — write a clean, plain professional post (no fake personality).\n\n"
        )

    return (
        f"Write one post for {brief.channel or 'LinkedIn'}. Output ONLY the post text, "
        "no preamble, no title, no hashtags.\n\n"
        "CONTENT IDEA (use only this — do not invent facts, numbers, or quotes):\n"
        + "\n".join(idea)
        + "\n\n"
        f"STRUCTURE — follow this skeleton:\n{structure}\n\n"
        f"CADENCE: {brief.cadence or '—'}\n"
        f"TONE: {', '.join(brief.tone) or '—'}\n"
        f"LENGTH: {brief.length or '—'}\n\n"
        f"{voice}"
        f"LAYERS:\n{layers}\n\n"
        f"BANNED: {', '.join(brief.banned) or '—'}\n"
        f"HARD NEVERS: {', '.join(brief.hard_nevers) or '—'}\n"
        "Rules: no invented facts or numbers — if there's no real number, don't fake one. "
        "No slop phrases. Hook in the first line. One idea. Short lines."
    )


def draft(stage: str, prompt: str, provider: Provider) -> str:
    return provider.complete(stage, prompt).strip()
