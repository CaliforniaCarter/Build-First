"""Writer's Council — the eval that revises to a threshold (the Reflexion loop).

A panel critiques the draft against the rubric and rewrites it without changing the
central claim or the voice. Reflexion stop rule: stop when it passes, or when another
pass won't help. Bounded by COUNCIL_MAX_PASSES so it never loops forever.
"""

from __future__ import annotations

import json
import re
from typing import Callable

from ..config import COUNCIL_MAX_PASSES
from ..providers.base import Provider
from ..rubric.shared import rubric_text


# Best-in-class moves (adapt the move, NOT the wording — never imitate another person's voice).
PLAYBOOK = (
    "PLAYBOOK — optimize toward these (adapt the move in the author's own voice; never copy):\n"
    "  1. Open on a real moment or admission, not a thesis. Never 'excited to share.'\n"
    "  2. Lead with the number / ship the receipts. One real metric beats ten adjectives.\n"
    "  3. Vulnerability beats the flex. 'I was wrong' / 'this didn't work' outperforms 'I crushed it.'\n"
    "  4. Show the mechanism, don't just claim the result.\n"
    "  5. 'How,' not 'wow' — explain the workflow behind it.\n"
    "  6. Teach something saveable (a guide, a rule, a checklist).\n"
    "  7. One spiky, ownable claim per post — debatable and only-you.\n"
    "  8. Plain language, zero jargon.\n"
    "  9. Give the playbook away; generosity is the flex.\n"
    "  10. Human and imperfect beats buffed and lifeless."
)


def build_council_prompt(draft: str, persona_md: str, layers: str) -> str:
    return (
        "You are the Writer's Council: Shaan Puri (hooks), Morgan Housel (clarity), "
        "David Perell (resonance). Critique the draft against the rubric and the playbook, then "
        "rewrite it to fix the issues WITHOUT changing the central claim or the voice. The most "
        "common miss is no turn: add a real admission, cost, or contrarian edge. Decide whether to "
        "stop (it passes, or another pass won't help) or continue.\n\n"
        f"{rubric_text()}\n\n"
        f"{PLAYBOOK}\n\n"
        f"PERSONA (keep this voice):\n{persona_md}\n\n"
        f"LAYERS:\n{layers}\n\n"
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
    on_pass: Callable[[int, dict], None] | None = None,
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
        entry = {
            "pass": n,
            "critique": parsed.get("critique", ""),
            "reason": parsed.get("reason", ""),
            "stop": stop,
        }
        log.append(entry)
        if on_pass:
            on_pass(n, entry)
        if stop:
            break
    return current, log
