"""Posting — describe the idea, watch the draft build live, copy it out. Never auto-posts.

The ONLY sinks here are local files (via generate_post / the human gate) and the browser's
own clipboard/download. There is deliberately no publish path.
"""

from __future__ import annotations

import datetime as _dt
import json

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, PlainTextResponse, RedirectResponse

from ...blocks.intake import load_intake
from ...config import PROFILES_DIR, RUNS_DIR
from ...post import generate_post
from ..app import onboarded
from ..jobs import run_in_thread
from ..sse import sse_response

router = APIRouter()

_IDEA_FIELDS = ("topic", "take", "scene", "number", "lesson", "only_you", "mechanism", "close")


def _persona_summary() -> str:
    path = PROFILES_DIR / "persona.md"
    if not path.exists():
        return ""
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip(" #*-")
        if line:
            return line
    return ""


@router.get("/post")
def post_page(request: Request):
    if not onboarded():
        return RedirectResponse("/onboarding")
    intake = load_intake()
    i = intake.idea
    ctx = {
        "idea": {f: getattr(i, f) for f in _IDEA_FIELDS},
        "proof": "\n".join(i.proof),
        "persona": _persona_summary(),
        "channels": ", ".join(intake.output.channels),
    }
    return request.app.state.templates.TemplateResponse(request, "post.html", ctx)


@router.post("/post/generate")
async def post_generate(request: Request):
    if not onboarded():
        return JSONResponse({"error": "not onboarded"}, status_code=400)

    form = dict(await request.form())
    intake = load_intake()
    for f in _IDEA_FIELDS:
        if form.get(f"idea__{f}") is not None:
            setattr(intake.idea, f, form.get(f"idea__{f}", ""))
    if form.get("idea__proof") is not None:
        intake.idea.proof = [s.strip() for s in form["idea__proof"].splitlines() if s.strip()]

    persona_md = (PROFILES_DIR / "persona.md").read_text(encoding="utf-8")
    run_id = _dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    jobs = request.app.state.jobs
    job = jobs.create("generate", run_id=run_id)
    factory = request.app.state.provider_factory

    def work():
        try:
            provider = factory(run_id, on_event=lambda k, p: job.emit(k, p))
            res = generate_post(
                intake, persona_md, provider, run_id, on_stage=lambda s, p: job.emit(s, p)
            )
            job.finish("done", result=res.model_dump())
        except Exception as exc:  # ClaudeNotLoggedIn, timeout, parse errors, ...
            job.emit("error", {"message": str(exc)})
            job.finish("error", error=str(exc))

    run_in_thread(work)
    return JSONResponse({"job_id": job.id, "run_id": run_id})


@router.get("/post/stream/{job_id}")
async def post_stream(job_id: str, request: Request):
    job = request.app.state.jobs.get(job_id)
    if job is None:
        return JSONResponse({"error": "unknown job"}, status_code=404)
    return sse_response(job, request)


@router.get("/post/draft/{run_id}")
def post_draft(run_id: str, request: Request):
    run_dir = RUNS_DIR / run_id
    draft_path = run_dir / "draft.md"
    if not draft_path.exists():
        return RedirectResponse("/post")
    draft = draft_path.read_text(encoding="utf-8")
    headline = ""
    score_path = run_dir / "score.json"
    if score_path.exists():
        try:
            data = json.loads(score_path.read_text(encoding="utf-8"))
            dims = data.get("dimensions", [])
            gates = data.get("gates", [])
            avg = round(sum(d["score"] for d in dims) / len(dims), 1) if dims else 0
            passed = sum(1 for g in gates if g.get("passed"))
            headline = f"{avg}/10 · gates {passed}/{len(gates)}"
        except Exception:
            headline = ""
    ctx = {"run_id": run_id, "draft": draft, "headline": headline}
    return request.app.state.templates.TemplateResponse(request, "draft.html", ctx)


@router.get("/post/draft/{run_id}/export")
def post_export(run_id: str):
    draft_path = RUNS_DIR / run_id / "draft.md"
    if not draft_path.exists():
        return PlainTextResponse("not found", status_code=404)
    return PlainTextResponse(
        draft_path.read_text(encoding="utf-8"),
        headers={"Content-Disposition": f'attachment; filename="post-{run_id}.md"'},
    )
