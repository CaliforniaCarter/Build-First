"""Anthropic provider — the synchronous, real-model path.

Dormant during the overnight CLI build (TerminalProvider uses the local agent), this is
the drop-in the web API (api/) uses for live generation. Enable with:
  uv pip install -e '.[api]'  and  ANTHROPIC_API_KEY.
"""

from __future__ import annotations

import os

from .base import Provider
from ..config import DEFAULT_MODEL

# Stages that return long structured JSON (the full score sheet, or a revised draft +
# critique) need more room than a short draft, or json.loads sees truncated output.
_LONG_STAGE_TOKENS = 8192


class AnthropicProvider(Provider):
    name = "anthropic"

    def __init__(self, model: str | None = None, max_tokens: int = 4096):
        self.model = model or os.environ.get("BF_MODEL", DEFAULT_MODEL)
        self.max_tokens = max_tokens

    def _tokens_for(self, stage: str) -> int:
        if stage.startswith(("score", "council", "compose_score")):
            return max(self.max_tokens, _LONG_STAGE_TOKENS)
        return self.max_tokens

    def complete(self, stage: str, prompt: str) -> str:
        try:
            import anthropic
        except ImportError as exc:
            raise RuntimeError("anthropic not installed; run: uv pip install -e '.[api]'") from exc

        key = os.environ.get("ANTHROPIC_API_KEY")
        if not key:
            raise RuntimeError("ANTHROPIC_API_KEY not set (see .env.example)")

        client = anthropic.Anthropic(api_key=key)
        resp = client.messages.create(
            model=self.model,
            max_tokens=self._tokens_for(stage),
            messages=[{"role": "user", "content": prompt}],
        )
        return "".join(b.text for b in resp.content if getattr(b, "type", None) == "text")
