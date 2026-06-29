"""Provider factory."""

from __future__ import annotations

from pathlib import Path

from .anthropic import AnthropicProvider
from .base import NeedsCompletion, Provider
from .claudecode import ClaudeCodeProvider
from .terminal import TerminalProvider


def get_provider(name: str, run_dir: Path) -> Provider:
    if name == "terminal":
        return TerminalProvider(run_dir)
    if name == "claudecode":
        return ClaudeCodeProvider(run_dir)
    if name == "anthropic":
        return AnthropicProvider()
    raise ValueError(f"unknown provider: {name!r} (use 'terminal', 'claudecode', or 'anthropic')")


__all__ = [
    "Provider",
    "NeedsCompletion",
    "TerminalProvider",
    "ClaudeCodeProvider",
    "AnthropicProvider",
    "get_provider",
]
