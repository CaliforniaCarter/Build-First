"""The provider seam: one method, `complete(stage, prompt) -> text`.

This is the only place the pipeline talks to a 'model'. It lets the same code run
through the terminal agent (no API key) tonight, or the Anthropic API later.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path


class NeedsCompletion(Exception):
    """Raised by the terminal provider when a stage's answer isn't on disk yet.

    The run is resumable: write the answer to `completion_path`, re-run the same
    command, and the pipeline picks up where it left off.
    """

    def __init__(self, stage: str, prompt_path: Path, completion_path: Path):
        self.stage = stage
        self.prompt_path = prompt_path
        self.completion_path = completion_path
        super().__init__(
            f"stage '{stage}' needs a completion\n"
            f"  prompt:  {prompt_path}\n"
            f"  answer:  {completion_path}  (write this, then re-run)"
        )


class Provider(ABC):
    name: str

    @abstractmethod
    def complete(self, stage: str, prompt: str) -> str:
        """Return the model's text for a stage given its assembled prompt."""
