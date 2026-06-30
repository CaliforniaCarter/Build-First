"""Provider factory."""

from __future__ import annotations

from pathlib import Path

from .anthropic import AnthropicProvider
from .base import NeedsCompletion, Provider
from .stub import StubProvider
from .terminal import TerminalProvider


def get_provider(name: str, run_dir: Path) -> Provider:
    if name == "terminal":
        return TerminalProvider(run_dir)
    if name == "anthropic":
        return AnthropicProvider()
    if name == "stub":
        return StubProvider()
    raise ValueError(f"unknown provider: {name!r} (use 'terminal', 'anthropic', or 'stub')")


__all__ = [
    "Provider",
    "NeedsCompletion",
    "TerminalProvider",
    "AnthropicProvider",
    "StubProvider",
    "get_provider",
]
