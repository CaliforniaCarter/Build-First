"""Claude Code provider — runs every stage on your Claude *subscription*, no API key.

It shells out to the locally logged-in `claude` CLI in headless mode (`claude -p`). When
you've run `claude login` (Pro/Max) and no ANTHROPIC_API_KEY is set, those calls bill your
subscription over OAuth — which is the whole point: zero keys, your plan.

Design notes:
- Prompt goes in on **stdin** (drafts + layers are large; argv would hit ARG_MAX).
- The env is scrubbed of ANTHROPIC_API_KEY / ANTHROPIC_AUTH_TOKEN so OAuth is used, not a key.
- `--max-turns 1`: one text completion, no agentic tool loop.
- An isolated empty cwd keeps the repo's CLAUDE.md out of generations.
- We never pass `--bare` (that mode forces API-key auth and ignores the subscription).
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from .base import Provider

# (kind, payload) — e.g. ("token", {"stage": ..., "text": ...}) for live streaming.
EventCb = Callable[[str, dict], None]

# stderr / result fragments that mean "auth problem", not a transient failure.
_AUTH_HINTS = (
    "not logged in",
    "please run",
    "claude login",
    "invalid api key",
    "authentication",
    "unauthorized",
    "oauth",
    "401",
)


class ClaudeCodeError(RuntimeError):
    """A claude invocation failed for a reason we couldn't classify."""


class ClaudeNotFound(ClaudeCodeError):
    """The `claude` binary isn't on PATH."""


class ClaudeNotLoggedIn(ClaudeCodeError):
    """`claude` is installed but not authenticated — run `claude login`."""


class ClaudeTimeout(ClaudeCodeError):
    """A stage took longer than the timeout."""


def _oauth_env() -> dict[str, str]:
    """A copy of the environment with API-key auth removed, forcing subscription OAuth."""
    env = os.environ.copy()
    env.pop("ANTHROPIC_API_KEY", None)
    env.pop("ANTHROPIC_AUTH_TOKEN", None)
    return env


class ClaudeCodeProvider(Provider):
    name = "claudecode"

    def __init__(
        self,
        run_dir: Path | None = None,
        *,
        binary: str = "claude",
        model: str | None = None,
        timeout: float = 240.0,
        stream: bool = False,
        on_event: EventCb | None = None,
    ):
        self.run_dir = run_dir  # accepted for factory parity; this provider needs no disk
        self.binary = binary
        # DEFAULT_MODEL is a label, not a guaranteed CLI alias — default to Claude Code's
        # own configured model unless BF_CLAUDE_MODEL is set (e.g. "opus" or a full id).
        self.model = model or os.environ.get("BF_CLAUDE_MODEL")
        self.timeout = timeout
        self.stream = stream
        self.on_event = on_event
        self._cwd = tempfile.mkdtemp(prefix="content-cc-")  # no CLAUDE.md here

    # -- public seam ---------------------------------------------------------

    def complete(self, stage: str, prompt: str) -> str:
        if shutil.which(self.binary) is None:
            raise ClaudeNotFound(f"`{self.binary}` not found on PATH — install Claude Code.")
        if self.on_event:
            self.on_event("stage_start", {"stage": stage})
        text = (
            self._complete_stream(stage, prompt)
            if self.stream
            else self._complete_json(stage, prompt)
        ).strip()
        if self.on_event:
            self.on_event("stage_done", {"stage": stage, "chars": len(text)})
        return text

    # -- json (reliable result path) ----------------------------------------

    def _argv(self) -> list[str]:
        argv = [self.binary, "-p", "--max-turns", "1"]
        if self.model:
            argv += ["--model", self.model]
        return argv

    def _complete_json(self, stage: str, prompt: str) -> str:
        argv = self._argv() + ["--output-format", "json"]
        try:
            proc = subprocess.run(
                argv,
                input=prompt,
                text=True,
                capture_output=True,
                env=_oauth_env(),
                cwd=self._cwd,
                timeout=self.timeout,
            )
        except FileNotFoundError as exc:
            raise ClaudeNotFound(str(exc)) from exc
        except subprocess.TimeoutExpired as exc:
            raise ClaudeTimeout(f"stage {stage!r} timed out after {self.timeout}s") from exc

        self._raise_for_auth(proc.returncode, proc.stderr or "")
        try:
            data = json.loads(proc.stdout)
        except json.JSONDecodeError as exc:
            raise ClaudeCodeError(
                f"unparseable claude output for {stage!r}: {proc.stdout[:300]!r}"
            ) from exc
        if data.get("is_error"):
            self._raise_for_auth(1, str(data.get("result", "")))
            raise ClaudeCodeError(f"claude error ({data.get('subtype')}): {data.get('result')}")
        return data.get("result", "")

    # -- streaming (best-effort progress) -----------------------------------

    def _complete_stream(self, stage: str, prompt: str) -> str:
        argv = self._argv() + [
            "--output-format",
            "stream-json",
            "--include-partial-messages",
            "--verbose",
        ]
        try:
            proc = subprocess.Popen(
                argv,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                env=_oauth_env(),
                cwd=self._cwd,
            )
        except FileNotFoundError as exc:
            raise ClaudeNotFound(str(exc)) from exc

        assert proc.stdin and proc.stdout
        proc.stdin.write(prompt)
        proc.stdin.close()

        final = ""
        for line in proc.stdout:  # one JSON object per line
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue  # tolerate banner / non-json lines across CLI versions
            kind = obj.get("type")
            if kind == "stream_event":
                ev = obj.get("event", {})
                if ev.get("type") == "content_block_delta":
                    delta = ev.get("delta", {})
                    if delta.get("type") == "text_delta" and self.on_event:
                        self.on_event("token", {"stage": stage, "text": delta.get("text", "")})
            elif kind == "result":
                final = obj.get("result", final)

        try:
            rc = proc.wait(timeout=self.timeout)
        except subprocess.TimeoutExpired as exc:
            proc.kill()
            raise ClaudeTimeout(f"stage {stage!r} timed out after {self.timeout}s") from exc
        stderr = proc.stderr.read() if proc.stderr else ""
        self._raise_for_auth(rc, stderr)
        if not final:
            # Streaming gave us nothing usable — fall back to the reliable json path.
            return self._complete_json(stage, prompt)
        return final

    @staticmethod
    def _raise_for_auth(returncode: int, stderr: str) -> None:
        low = stderr.lower()
        if any(h in low for h in _AUTH_HINTS):
            raise ClaudeNotLoggedIn(
                "Claude Code isn't logged in (or the session expired). Run `claude login`."
            )
        if returncode != 0:
            raise ClaudeCodeError(f"claude exited {returncode}: {stderr[:300]}")


# -- preflight ---------------------------------------------------------------


@dataclass
class ClaudeStatus:
    installed: bool
    logged_in: bool
    version: str | None
    detail: str


def check_claude(binary: str = "claude", timeout: float = 25.0) -> ClaudeStatus:
    """Probe whether `claude` is installed and authenticated (cheap one-token ping)."""
    if shutil.which(binary) is None:
        return ClaudeStatus(
            False, False, None, "Claude Code isn't installed. Install it, then run `claude login`."
        )

    version: str | None = None
    try:
        v = subprocess.run([binary, "--version"], capture_output=True, text=True, timeout=10)
        version = (v.stdout or "").strip() or None
    except Exception:
        pass

    try:
        p = subprocess.run(
            [binary, "-p", "--max-turns", "1", "--output-format", "json"],
            input="Reply with the single word: ok",
            text=True,
            capture_output=True,
            env=_oauth_env(),
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return ClaudeStatus(True, False, version, "Login check timed out — try again.")
    except Exception as exc:  # pragma: no cover - defensive
        return ClaudeStatus(True, False, version, f"Login check failed: {exc}")

    ok = p.returncode == 0 and not any(h in (p.stderr or "").lower() for h in _AUTH_HINTS)
    if ok:
        try:
            ok = not json.loads(p.stdout).get("is_error", False)
        except Exception:
            ok = False
    detail = (
        "Logged in — using your Claude subscription (no API key)."
        if ok
        else "Installed, but not logged in. Run `claude login`."
    )
    return ClaudeStatus(True, ok, version, detail)
