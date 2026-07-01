"""Receipts — pin proof to the post, and redact anything private before it ships.

Redaction matters even though the run is local: a post is public, so emails, phone
numbers, and keys must never leak into the draft body.
"""

from __future__ import annotations

import re

from .intake import Intake

_EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
_PHONE = re.compile(r"\(?\b\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b")
_KEY = re.compile(r"\bsk-[A-Za-z0-9-]{8,}\b")


def redact(text: str) -> tuple[str, list[str]]:
    found: list[str] = []
    for pattern, label in ((_EMAIL, "email"), (_PHONE, "phone"), (_KEY, "key")):
        if pattern.search(text):
            found.append(label)
            text = pattern.sub(f"[{label} redacted]", text)
    return text, found


def attach_receipts(draft: str, intake: Intake) -> tuple[str, list[str], list[str]]:
    """Return (redacted_draft, proof_items, redactions)."""
    redacted, redactions = redact(draft)
    proof = list(intake.idea.proof)
    return redacted, proof, redactions
