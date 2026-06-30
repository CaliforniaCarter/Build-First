"""Draft — write the post from only what's known at this input level, in voice.

The ablation passes a different `context_block` (and maybe a persona) per level; the
prompt is otherwise identical, so the eval isolates what each input is worth.
"""

from __future__ import annotations

from ..providers.base import Provider


def build_draft_prompt(
    topic: str,
    context_block: str,
    persona_md: str | None,
    layers: str,
    hard_nevers: list[str],
    channels: list[str],
    recent_openings: list[str] = (),
) -> str:
    if persona_md:
        voice = f"VOICE — write in this voice and obey its never-do list:\n{persona_md}\n\n"
    else:
        voice = (
            "VOICE: none yet — write a clean, plain professional post (no fake personality).\n\n"
        )
    recent = ""
    if recent_openings:
        joined = "\n".join(f"- {o}" for o in recent_openings)
        recent = (
            "RECENT POSTS — vary the shape and the opening from these; do not reuse the same "
            f"structure twice in a row:\n{joined}\n\n"
        )
    return (
        f"Write one post for {', '.join(channels) or 'LinkedIn'}. Output ONLY the post text, "
        "no preamble, no title, no hashtags.\n\n"
        f"TOPIC:\n{topic}\n\n"
        f"WHAT YOU KNOW (use only this):\n{context_block}\n\n"
        f"{voice}"
        f"LAYERS:\n{layers}\n\n"
        f"{recent}"
        f"HARD NEVERS: {', '.join(hard_nevers) or '—'}\n"
        "Rules: use only the material above — never invent a fact, name, number, or quote; if a "
        "specific isn't there, leave it out. No slop. Hook on the first line. One idea. Short "
        "lines. Vary the shape from recent posts — don't default to a how-it-works list with a "
        "question close."
    )


def draft(stage: str, prompt: str, provider: Provider) -> str:
    return provider.complete(stage, prompt).strip()
