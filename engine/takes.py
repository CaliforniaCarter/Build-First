"""Takes — spiky, ownable opinions you could turn into a post.

The content playground: from what you believe and work on, surface a few debatable takes in
your voice. Grounded ONLY in your material — it never invents an opinion you don't hold.
"""

from __future__ import annotations

import json
import re

from .blocks.intake import Intake
from .providers.base import Provider


def build_takes_prompt(intake: Intake, persona_md: str, n: int) -> str:
    t = intake.typed
    material = {
        "known_for": t.known_for,
        "beliefs": t.beliefs,
        "lessons": t.lessons,
        "background": t.background,
        "topic": intake.idea.topic,
    }
    return (
        f"From this person's material, surface up to {n} spiky, ownable TAKES they could post — "
        "each a debatable, only-they opinion in their voice. Ground every take ONLY in the "
        "material; never invent a belief, fact, or example. If the material is thin, return "
        "fewer.\n\n"
        f"VOICE:\n{persona_md or '(none yet)'}\n\n"
        f"MATERIAL:\n{json.dumps(material, indent=2)}\n\n"
        'Return ONLY JSON: [{"take":"one debatable sentence","based_on":"the material it draws on"}]'
    )


def parse_takes(raw: str) -> list[dict]:
    text = raw.strip()
    if "```" in text:
        text = re.sub(r"```(?:json)?", "", text).strip()
    start, end = text.find("["), text.rfind("]")
    return json.loads(text[start : end + 1]) if start != -1 and end != -1 else []


def form_takes(intake: Intake, persona_md: str, provider: Provider, n: int = 3) -> list[dict]:
    """A few takes the user could post, grounded in their material. Empty if nothing to say."""
    raw = provider.complete("takes", build_takes_prompt(intake, persona_md, n))
    return [t for t in parse_takes(raw) if isinstance(t, dict) and t.get("take")]
