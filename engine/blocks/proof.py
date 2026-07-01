"""Proof — the deterministic anti-slop / anti-fabrication check.

Code, not the LLM, certifies a post: no banned/slop phrase appears, every number (and, in
the wider scope, code/path-like specifics) traces back to the user's real material, and
private data is redacted. The model can't grade its own homework here.

Config is editable JSON (`engine/proof.json`): the universal slop list + the check settings.
The user's personal never-say list lives in `voice.json` (`banned`). Flags are warnings — the
human is always the gate; nothing here blocks or rewrites a post.
"""

from __future__ import annotations

import re
from pathlib import Path

from pydantic import BaseModel

from ..config import PROOF_PATH
from .intake import Intake
from .receipts import attach_receipts


class ProofConfig(BaseModel):
    slop_phrases: list[str] = []
    grounding_scope: str = "numbers_and_specifics"  # "numbers" | "numbers_and_specifics"
    on_flag: str = (
        "warn"  # "warn" | "block" (advisory: the plugin decides; the engine never blocks)
    )


class ProofReport(BaseModel):
    receipts: list[str] = []  # the real proof attached to the post
    redactions: list[str] = []  # private data stripped (email/phone/key)
    slop_hits: list[str] = []  # banned/slop phrases present in the post
    ungrounded: list[str] = []  # numbers/specifics that don't trace to the user's material

    @property
    def clean(self) -> bool:
        return not self.slop_hits and not self.ungrounded


def load_proof_config(path: Path | None = None) -> ProofConfig:
    p = path or PROOF_PATH
    if not p.exists():
        return ProofConfig()
    return ProofConfig.model_validate_json(p.read_text(encoding="utf-8"))


def source_corpus(intake: Intake) -> str:
    """Everything the user actually gave us — the only material a post is allowed to draw on."""
    i, t, v, d, o = intake.idea, intake.typed, intake.voice, intake.docs, intake.online
    parts = [
        i.topic,
        i.take,
        i.scene,
        i.number,
        i.lesson,
        i.only_you,
        i.mechanism,
        i.close,
        *i.proof,
        t.identity,
        t.background,
        t.beliefs,
        t.lessons,
        d.resume,
        d.portfolio,
        o.other,
        o.existing_posts,
        *v.answers.values(),
        *v.writing_samples,
        v.notes,
    ]
    return "\n".join(p for p in parts if p)


def check_slop(text: str, personal_banned: list[str], cfg: ProofConfig | None = None) -> list[str]:
    """Banned/slop phrases present in the post — universal list (proof.json) + personal (voice.json)."""
    cfg = cfg or load_proof_config()
    low = text.lower()
    banned = [*cfg.slop_phrases, *personal_banned]
    hits: list[str] = []
    for phrase in banned:
        p = (phrase or "").strip()
        if p and p.lower() in low and p not in hits:
            hits.append(p)
    return hits


# A "figure": an optional $, digits (with commas/decimal), an optional unit (% x k m b/bn).
_FIGURE = re.compile(r"\$?\d[\d,]*(?:\.\d+)?\s?(?:%|x|k|m|bn|b)?", re.IGNORECASE)
# A code/path-like specific: file.ext or a/b/c — catches an invented file or identifier.
_CODEISH = re.compile(r"\b\w+(?:[./]\w+)+\b")


def _digit_core(token: str) -> str:
    return re.sub(r"[^\d]", "", token)


def _claim_like(token: str, core: str) -> bool:
    """Skip bare single digits (noisy); a 2+ digit number or any unit-bearing figure is a claim."""
    return len(core) >= 2 or any(u in token.lower() for u in ("%", "$", "x", "k", "m", "b"))


def check_grounding(text: str, intake: Intake, cfg: ProofConfig | None = None) -> list[str]:
    """Figures (and, in the wider scope, code/path specifics) in the post that don't appear in
    the user's material — a deterministic tripwire for invented facts."""
    cfg = cfg or load_proof_config()
    src = source_corpus(intake)
    src_cores = {c for c in (_digit_core(m) for m in _FIGURE.findall(src)) if c}
    src_low = src.lower()

    out: list[str] = []
    for m in _FIGURE.findall(text):
        token = m.strip()
        core = _digit_core(token)
        if core and _claim_like(token, core) and core not in src_cores and token not in out:
            out.append(token)

    if cfg.grounding_scope == "numbers_and_specifics":
        for m in _CODEISH.findall(text):
            if m.lower() not in src_low and m not in out:
                out.append(m)
    return out


def proof_report(
    redacted_draft: str,
    receipts: list[str],
    redactions: list[str],
    intake: Intake,
    cfg: ProofConfig | None = None,
) -> ProofReport:
    """Run the full check on an already-redacted draft (redaction happens in attach_receipts)."""
    cfg = cfg or load_proof_config()
    return ProofReport(
        receipts=receipts,
        redactions=redactions,
        slop_hits=check_slop(redacted_draft, intake.voice.banned, cfg),
        ungrounded=check_grounding(redacted_draft, intake, cfg),
    )


def check_text(draft: str, intake: Intake, cfg: ProofConfig | None = None) -> ProofReport:
    """Redact + attach receipts + run the proof check on any text — the one-call entry point."""
    redacted, receipts, redactions = attach_receipts(draft, intake)
    return proof_report(redacted, receipts, redactions, intake, cfg)
