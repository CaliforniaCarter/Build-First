"""Writer's Council — the eval that revises to a threshold (the Reflexion loop).

A panel critiques the draft against the rubric and rewrites it without changing the
central claim or the voice. Reflexion stop rule: stop when it passes, or when another
pass won't help. Bounded by COUNCIL_MAX_PASSES so it never loops forever.
"""

from __future__ import annotations

import json
import re

from ..config import COUNCIL_MAX_PASSES
from ..providers.base import Provider


def build_council_prompt(draft: str, persona_md: str, layers: str) -> str:
    return (
        "Sharp editor (Shaan Puri on hooks, Morgan Housel on clarity, David Perell on resonance). "
        "Make this post stronger — sharper hook, tighter lines, a real turn (an admission or "
        "contrarian edge) — without changing the central claim or the voice. The usual miss is no "
        "turn. NEVER invent specifics: every fact, name, number, and example must already be in "
        "the draft; if a stronger post would need one you don't have, say so in the critique "
        "instead of inventing it. Stop when it passes or another pass won't help.\n\n"
        f"VOICE (keep it):\n{persona_md}\n\n"
        f"FORMAT:\n{layers}\n\n"
        f"DRAFT:\n{draft}\n\n"
        'Return ONLY JSON: {"critique":"...","revised_draft":"...","stop":true|false,"reason":"..."}'
    )


def _parse_pass(raw: str) -> dict:
    text = raw.strip()
    if "```" in text:
        text = re.sub(r"```(?:json)?", "", text).strip()
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("no JSON object in council completion")
    return json.loads(text[start : end + 1])


def revise(
    draft: str,
    persona_md: str,
    layers: str,
    provider: Provider,
    max_passes: int = COUNCIL_MAX_PASSES,
) -> tuple[str, list[dict]]:
    log: list[dict] = []
    current = draft
    for n in range(1, max_passes + 1):
        out = provider.complete(
            f"council_pass{n}", build_council_prompt(current, persona_md, layers)
        )
        parsed = _parse_pass(out)
        current = (parsed.get("revised_draft") or current).strip()
        stop = bool(parsed.get("stop"))
        log.append(
            {
                "pass": n,
                "critique": parsed.get("critique", ""),
                "reason": parsed.get("reason", ""),
                "stop": stop,
            }
        )
        if stop:
            break
    return current, log
