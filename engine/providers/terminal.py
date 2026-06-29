"""Terminal provider: the model is whatever agent drives the terminal (no key).

For each stage it writes the assembled prompt to `runs/<id>/prompts/<stage>.md`
and reads the answer from `runs/<id>/completions/<stage>.txt`. Missing answer ->
NeedsCompletion (resumable). Every prompt and answer is kept as an audit trail.
"""
from __future__ import annotations

from pathlib import Path

from .base import NeedsCompletion, Provider


class TerminalProvider(Provider):
    name = "terminal"

    def __init__(self, run_dir: Path):
        self.run_dir = Path(run_dir)
        self.prompts_dir = self.run_dir / "prompts"
        self.completions_dir = self.run_dir / "completions"
        self.prompts_dir.mkdir(parents=True, exist_ok=True)
        self.completions_dir.mkdir(parents=True, exist_ok=True)

    def complete(self, stage: str, prompt: str) -> str:
        prompt_path = self.prompts_dir / f"{stage}.md"
        prompt_path.write_text(prompt, encoding="utf-8")

        completion_path = self.completions_dir / f"{stage}.txt"
        if completion_path.exists():
            answer = completion_path.read_text(encoding="utf-8")
            if answer.strip():
                return answer
        raise NeedsCompletion(stage, prompt_path, completion_path)
