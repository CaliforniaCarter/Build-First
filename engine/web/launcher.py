"""`Content` — the one command you run. Preflight Claude login, serve locally, open the browser.

Binds to 127.0.0.1 only: this drives your own logged-in Claude Code on your own machine.
(Driving other people's subscriptions, or hosting this multi-tenant, needs Anthropic's
approval — see the README.)
"""

from __future__ import annotations

import socket
import sys
import threading
import time
import webbrowser

from ..config import HOME
from ..providers.claudecode import check_claude

_PREFERRED_PORT = 8765


def _pick_port(preferred: int = _PREFERRED_PORT) -> int:
    for candidate in (preferred, 0):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                s.bind(("127.0.0.1", candidate))
                return s.getsockname()[1]
        except OSError:
            continue
    return preferred


def _preflight() -> int | None:
    st = check_claude()
    if not st.installed:
        print(
            "Content runs on your Claude subscription via the `claude` CLI — no API key.\n"
            "  1) Install Claude Code\n"
            "  2) Run:  claude login   (uses your Claude Pro/Max plan)\n"
            f"\n  {st.detail}",
            file=sys.stderr,
        )
        return 1
    if not st.logged_in:
        print(
            "Claude Code is installed but not logged in.\n"
            "  Run:  claude login\n"
            "  (Content drives your subscription locally — no ANTHROPIC_API_KEY needed.)\n"
            f"\n  {st.detail}",
            file=sys.stderr,
        )
        return 1
    return None


def main(argv: list[str] | None = None) -> int:
    rc = _preflight()
    if rc is not None:
        return rc

    import uvicorn

    from .app import create_app

    port = _pick_port()
    url = f"http://127.0.0.1:{port}"
    print(f"Content is running at {url}")
    print(f"  data lives in: {HOME}")
    print("  Press Ctrl+C to stop.")

    def _open_browser() -> None:
        time.sleep(1.0)
        try:
            webbrowser.open(url)
        except Exception:
            pass  # headless / SSH — the URL is already printed

    threading.Thread(target=_open_browser, daemon=True).start()

    try:
        uvicorn.run(create_app(), host="127.0.0.1", port=port, log_level="warning")
    except KeyboardInterrupt:
        print("\nStopped.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
