"""The FastAPI app — onboarding, posting, and a status page. Localhost only, never publishes.

`create_app` takes an optional `provider_factory` so tests can inject a fake model. In
production the factory builds a streaming `ClaudeCodeProvider` (your subscription, no key).
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable

from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from ..config import DATA_DIR, PROFILES_DIR
from ..providers.base import Provider
from .jobs import JobRegistry

_HERE = Path(__file__).resolve().parent
TEMPLATES = Jinja2Templates(directory=str(_HERE / "templates"))

# (run_id, on_event) -> Provider
ProviderFactory = Callable[..., Provider]


def _default_provider_factory(run_id: str, on_event=None) -> Provider:
    from ..providers.claudecode import ClaudeCodeProvider

    return ClaudeCodeProvider(run_id, stream=True, on_event=on_event)


def onboarded() -> bool:
    return (DATA_DIR / "intake.json").exists() and (PROFILES_DIR / "persona.md").exists()


def create_app(provider_factory: ProviderFactory | None = None) -> FastAPI:
    app = FastAPI(title="Content", docs_url=None, redoc_url=None)
    app.state.jobs = JobRegistry()
    app.state.provider_factory = provider_factory or _default_provider_factory
    app.state.templates = TEMPLATES

    app.mount("/static", StaticFiles(directory=str(_HERE / "static")), name="static")

    from .routes import onboarding, posting, status

    app.include_router(status.router)
    app.include_router(onboarding.router)
    app.include_router(posting.router)

    @app.get("/")
    def index(request: Request):
        return RedirectResponse("/post" if onboarded() else "/onboarding")

    return app
