"""Status page — is Claude logged in (subscription), and where does data live? Pure read."""

from __future__ import annotations

from fastapi import APIRouter, Request

from ...config import DATA_DIR, HOME, PROFILES_DIR, RUNS_DIR
from ...providers.claudecode import check_claude
from ..app import onboarded

router = APIRouter()


@router.get("/status")
def status(request: Request):
    st = check_claude()
    ctx = {
        "claude": st,
        "home": str(HOME),
        "data_dir": str(DATA_DIR),
        "profiles_dir": str(PROFILES_DIR),
        "runs_dir": str(RUNS_DIR),
        "onboarded": onboarded(),
    }
    return request.app.state.templates.TemplateResponse(request, "status.html", ctx)
