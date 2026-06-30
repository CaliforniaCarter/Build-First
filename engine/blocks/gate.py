"""Human gate — the engine never auto-posts. It writes a draft and copies it for review."""

from __future__ import annotations

import subprocess
from pathlib import Path


def human_gate(final_draft: str, run_dir: Path) -> Path:
    run_dir = Path(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)
    out = run_dir / "draft.md"
    out.write_text(final_draft, encoding="utf-8")
    try:  # best-effort clipboard on macOS; never fatal
        subprocess.run(["pbcopy"], input=final_draft.encode("utf-8"), check=False)
    except Exception:
        pass
    return out
