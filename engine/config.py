"""Paths and a few tunables. No magic — everything hangs off one writable home.

HOME resolution (so the same code works from a dev checkout AND an installed app):
  1. $CONTENT_HOME if set — the explicit override.
  2. The repo root, when running from a checkout (it has a pyproject.toml and is writable).
  3. ~/.content — the fallback when installed into site-packages.
LAYERS_DIR is always package-relative (the prompt layers ship inside `engine/`).
"""

from __future__ import annotations

import os
from pathlib import Path

ENGINE = Path(__file__).resolve().parent
_PKG_PARENT = ENGINE.parent  # repo root in a dev checkout; site-packages when installed


def _resolve_home() -> Path:
    override = os.environ.get("CONTENT_HOME")
    if override:
        return Path(override).expanduser().resolve()
    if (_PKG_PARENT / "pyproject.toml").exists() or (_PKG_PARENT / "data").is_dir():
        return _PKG_PARENT  # running from the checkout — keep data alongside the code
    return Path.home() / ".content"  # installed elsewhere — user data lives here


HOME = _resolve_home()
ROOT = HOME  # kept for back-compat with imports that referenced ROOT

PROFILES_DIR = HOME / "profiles"
RUNS_DIR = HOME / "runs"
DATA_DIR = HOME / "data"
LAYERS_DIR = ENGINE / "layers"

# Council target and stop behaviour (Reflexion: stop when revisions stop helping).
COUNCIL_TARGET = 9.0
COUNCIL_MAX_PASSES = 3

DEFAULT_MODEL = "claude-opus-4-8"
