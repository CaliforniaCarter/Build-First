"""Read/write `data/intake.json` for the web intake — deterministic, no model calls.

Answers arrive keyed by their `writes_to` dotted path (the same paths the engine's
`onboarding.json` declares), e.g. `{"name": "Carter", "voice.answers.weekend": "skied"}`.
We start from the blank `intake.example.json` shape, set each path, validate against the
`Intake` pydantic model (so a bad write fails loudly), and write the whole file back.
"""

from __future__ import annotations

import json
from typing import Any

from engine.blocks.intake import Intake
from engine.config import DATA_DIR

INTAKE_PATH = DATA_DIR / "intake.json"
EXAMPLE_PATH = DATA_DIR / "intake.example.json"


def blank_intake() -> dict[str, Any]:
    """The empty intake shape (from the committed example)."""
    return json.loads(EXAMPLE_PATH.read_text(encoding="utf-8"))


def current_intake() -> dict[str, Any]:
    """The in-progress intake, or a blank shape if onboarding hasn't started."""
    if INTAKE_PATH.exists():
        return json.loads(INTAKE_PATH.read_text(encoding="utf-8"))
    return blank_intake()


def set_by_path(data: dict[str, Any], dotted: str, value: Any) -> None:
    """Set `value` at a dotted path (e.g. "voice.answers.weekend"), creating dicts as needed."""
    parts = dotted.split(".")
    cur = data
    for p in parts[:-1]:
        nxt = cur.get(p)
        if not isinstance(nxt, dict):
            nxt = {}
            cur[p] = nxt
        cur = nxt
    cur[parts[-1]] = value


def write_intake(data: dict[str, Any]) -> dict[str, Any]:
    """Validate against the Intake schema and write the normalized JSON."""
    validated = Intake.model_validate(data).model_dump()
    INTAKE_PATH.write_text(json.dumps(validated, indent=2) + "\n", encoding="utf-8")
    return validated


def begin() -> dict[str, Any]:
    """Start a fresh onboarding: reset intake.json to the blank shape."""
    return write_intake(blank_intake())


def apply_answers(answers: dict[str, Any]) -> dict[str, Any]:
    """Merge a batch of `{writes_to: value}` answers into the current intake and persist."""
    data = current_intake()
    for path, value in answers.items():
        set_by_path(data, path, value)
    return write_intake(data)


def set_resume(text: str) -> dict[str, Any]:
    """Store résumé text at `docs.resume`."""
    return apply_answers({"docs.resume": text})


def extract_pdf_text(raw: bytes) -> str:
    """Best-effort plain text from an uploaded PDF (empty string if it can't be read)."""
    import io

    from pypdf import PdfReader

    try:
        reader = PdfReader(io.BytesIO(raw))
        return "\n".join((page.extract_text() or "") for page in reader.pages).strip()
    except Exception:  # noqa: BLE001 — best-effort; the UI always offers paste as a fallback
        return ""
