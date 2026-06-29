"""Onboarding — fill the form, Save writes everything to disk, then we build your persona.

Save flow: validate -> write data/intake.json -> write_profile_docs (instant, deterministic)
-> kick off the persona build (one model call) as a streamed job -> redirect to /post.
"""

from __future__ import annotations

from fastapi import APIRouter, Request
from pydantic import ValidationError

from ...blocks.intake import load_intake
from ...blocks.persona import build_persona
from ...blocks.profile import write_profile_docs
from ...config import DATA_DIR
from ..forms import VOICE_QUESTIONS, form_from_intake, intake_from_form
from ..jobs import run_in_thread
from ..sse import sse_response

router = APIRouter()


def _render_form(request: Request, values: dict, error: str | None = None):
    ctx = {
        "f": values,
        "voice_questions": VOICE_QUESTIONS,
        "voice_answers": values.get("voice__answers", {}),
        "error": error,
    }
    return request.app.state.templates.TemplateResponse(request, "onboarding.html", ctx)


@router.get("/onboarding")
def onboarding_form(request: Request):
    try:
        values = form_from_intake(load_intake())  # edit mode
    except FileNotFoundError:
        values = {"online__cold_start": True, "voice__answers": {}}
    return _render_form(request, values)


@router.post("/onboarding")
async def onboarding_save(request: Request):
    form = dict(await request.form())
    try:
        intake = intake_from_form(form)
    except ValidationError as exc:
        return _render_form(request, form, error=str(exc))

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    (DATA_DIR / "intake.json").write_text(intake.model_dump_json(indent=2), encoding="utf-8")
    write_profile_docs(intake)  # deterministic profile.md + context.md

    jobs = request.app.state.jobs
    job = jobs.create("onboard")
    factory = request.app.state.provider_factory

    def work():
        try:
            provider = factory("onboard", on_event=lambda k, p: job.emit(k, p))
            build_persona(intake, provider)  # writes profiles/persona.md
            job.finish("done", result={"redirect": "/post"})
        except Exception as exc:  # ClaudeNotLoggedIn, timeout, etc.
            job.emit("error", {"message": str(exc)})
            job.finish("error", error=str(exc))

    run_in_thread(work)
    ctx = {"job_id": job.id, "name": intake.name}
    return request.app.state.templates.TemplateResponse(request, "persona_build.html", ctx)


@router.get("/onboarding/stream/{job_id}")
async def onboarding_stream(job_id: str, request: Request):
    job = request.app.state.jobs.get(job_id)
    if job is None:
        return request.app.state.templates.TemplateResponse(
            request, "persona_build.html", {"job_id": "", "name": ""}, status_code=404
        )
    return sse_response(job, request)
