"""Revise by command — you say what to change, the LLM does it.

The engine doesn't decide the edit; you do, in plain words. The LLM keeps your voice and
the central claim and changes only what you asked. No invented facts or numbers.
"""

from __future__ import annotations

from .providers.base import Provider


def build_revise_prompt(
    post: str, command: str, persona_md: str, layers: str, hard_nevers: list[str]
) -> str:
    return (
        "Revise the post below to do exactly what the user asks, and nothing more. Keep their "
        "voice and the central claim. Do not invent facts or numbers.\n\n"
        f"VOICE (obey this):\n{persona_md}\n\n"
        f"LAYERS:\n{layers}\n\n"
        f"HARD NEVERS: {', '.join(hard_nevers) or '—'}\n\n"
        f"WHAT THE USER WANTS CHANGED:\n{command}\n\n"
        f"POST:\n{post}\n\n"
        "Output ONLY the revised post text."
    )


def revise(
    post: str,
    command: str,
    persona_md: str,
    layers: str,
    hard_nevers: list[str],
    provider: Provider,
) -> str:
    prompt = build_revise_prompt(post, command, persona_md, layers, hard_nevers)
    return provider.complete("revise", prompt).strip()
