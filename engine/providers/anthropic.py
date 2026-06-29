"""Anthropic provider — DORMANT. The overnight build does not use this.

Enable the re-eval path with:  uv pip install -e '.[api]'  and  ANTHROPIC_API_KEY.
Kept deliberately thin: it is the drop-in that lets the same evals re-run with a key.
"""

from __future__ import annotations

import os

from .base import Provider
from ..config import DEFAULT_MODEL


class AnthropicProvider(Provider):
    name = "anthropic"

    def __init__(self, model: str | None = None, max_tokens: int = 2048):
        self.model = model or os.environ.get("BF_MODEL", DEFAULT_MODEL)
        self.max_tokens = max_tokens

    def complete(self, stage: str, prompt: str) -> str:
        try:
            import anthropic
        except ImportError as exc:  # pragma: no cover - dormant path
            raise RuntimeError("anthropic not installed; run: uv pip install -e '.[api]'") from exc

        key = os.environ.get("ANTHROPIC_API_KEY")
        if not key:  # pragma: no cover - dormant path
            raise RuntimeError("ANTHROPIC_API_KEY not set (see .env.example)")

        client = anthropic.Anthropic(api_key=key)
        resp = client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        return "".join(b.text for b in resp.content if getattr(b, "type", None) == "text")
