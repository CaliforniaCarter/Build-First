"""Paths and a few tunables. No magic — everything is relative to the repo root."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENGINE = Path(__file__).resolve().parent

PROFILES_DIR = ROOT / "profiles"
RUNS_DIR = ROOT / "runs"
POSTS_DIR = ROOT / "posts"
DATA_DIR = ROOT / "data"
LAYERS_DIR = ENGINE / "layers"

# The onboarding scaffolding — welcome + audience default + the question flow.
# Plain, hand-editable JSON; the plugin reads it to drive the conversation.
ONBOARDING_PATH = ENGINE / "onboarding.json"

# Council target and stop behaviour (Reflexion: stop when revisions stop helping).
COUNCIL_TARGET = 9.0
COUNCIL_MAX_PASSES = 3

DEFAULT_MODEL = "claude-opus-4-8"
