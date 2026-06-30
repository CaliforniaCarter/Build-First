"""CLI — the product (`post`, `gaps`, `posts`) and the vetting lab (`ablate`, `report`).

`post` makes one in-voice post you approve; `gaps` is the gap-driven probe; `posts`
lists the saved library. `ablate`/`report` are the build-time lab. Default provider is
`terminal` (Claude Code is the engine, no API key); `--json` emits UI-readable output.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import sys
from pathlib import Path

from .ablation import run_ablation
from .blocks.gate import human_gate
from .blocks.intake import load_intake
from .blocks.persona import build_persona
from .blocks.probe import unfilled_gaps
from .blocks.profile import write_profile_docs
from .config import PROFILES_DIR, RUNS_DIR
from .post import make_post, open_gaps
from .providers import get_provider
from .providers.base import NeedsCompletion
from .report import RunReport, build_report, compute_places_to_refine, write_report
from .store import list_posts, save_post


def _provider(args):
    return get_provider(args.provider, RUNS_DIR / args.run_id)


def _intake(args):
    return load_intake(Path(args.intake) if args.intake else None)


def _onboard(intake, provider):
    paths = write_profile_docs(intake)
    persona_md = build_persona(intake, provider)
    return paths, persona_md


def cmd_onboard(args):
    intake = _intake(args)
    paths, _ = _onboard(intake, _provider(args))
    print(f"wrote {paths['profile']} and {paths['context']} and {PROFILES_DIR / 'persona.md'}")


def cmd_ablate(args):
    intake = _intake(args)
    provider = _provider(args)
    persona_md = (PROFILES_DIR / "persona.md").read_text(encoding="utf-8")
    results = run_ablation(intake, persona_md, provider, args.run_id)
    for r in results:
        print(f"{r.level} {r.label:12s} {r.score.headline()}")


def cmd_report(args):
    intake = _intake(args)
    provider = _provider(args)
    persona_md = (PROFILES_DIR / "persona.md").read_text(encoding="utf-8")
    results = run_ablation(intake, persona_md, provider, args.run_id)
    report = RunReport(
        run_id=args.run_id,
        topic=intake.idea.topic,
        generated=args.date,
        provider=provider.name,
        levels=results,
        places_to_refine=compute_places_to_refine(results),
    )
    path = write_report(report)
    print(f"report -> {path}")


def cmd_run(args):
    intake = _intake(args)
    provider = _provider(args)
    _onboard(intake, provider)
    persona_md = (PROFILES_DIR / "persona.md").read_text(encoding="utf-8")
    results = run_ablation(intake, persona_md, provider, args.run_id)
    report = RunReport(
        run_id=args.run_id,
        topic=intake.idea.topic,
        generated=args.date,
        provider=provider.name,
        levels=results,
        places_to_refine=compute_places_to_refine(results),
    )
    path = write_report(report)
    print(build_report(report))
    print(f"\n--- report written to {path} ---")


def cmd_post(args):
    """The product: onboard, draft ONE post with every input, polish, and hand it to you."""
    intake = _intake(args)
    provider = _provider(args)
    _onboard(intake, provider)
    persona_md = (PROFILES_DIR / "persona.md").read_text(encoding="utf-8")
    result = make_post(intake, persona_md, provider, args.run_id)
    out = human_gate(result.final_draft, RUNS_DIR / args.run_id / "post")
    saved = save_post(result, intake, args.date)

    print(result.final_draft)
    print(f"\n--- score: {result.score.headline()} ---")
    gaps = open_gaps(result.score)
    if gaps:
        print("This post still needs (the engine won't fake these — add them, then re-run):")
        for g in gaps:
            print(f"  - {g}")
    if result.proof:
        print(f"receipts: {', '.join(result.proof)}")
    print(f"\nSaved to {saved} · copied to clipboard · review draft: {out}")


def cmd_gaps(args):
    """The gap-driven probe: what a strong post still needs. The UI reads --json."""
    intake = _intake(args)
    gaps = unfilled_gaps(intake)
    if args.json:
        print(json.dumps(gaps, indent=2))
        return
    if not gaps:
        print("No gaps — this idea already has a number, scene, lesson, and only-you angle.")
        return
    print("To make this post strong, the engine needs (it won't invent these):")
    for g in gaps:
        print(f"  [{g['key']}] {g['question']}")


def cmd_posts(args):
    """List the saved-post library. The UI reads --json."""
    posts = list_posts()
    if args.json:
        print(json.dumps(posts, indent=2))
        return
    if not posts:
        print("No saved posts yet. Run `bf post` to make one.")
        return
    for p in posts:
        s = p["score"]
        print(
            f"{p['date']}  {s['quality']}/10  gates {s['gates_passed']}/{s['gates_total']}  {p['topic'][:60]}"
        )


def cmd_doctor(args):
    intake = _intake(args)
    print(f"intake ok: {intake.name}, topic={intake.idea.topic[:60]!r}")
    print(f"channels={intake.output.channels} hard_nevers={intake.output.hard_nevers}")


def _load_env() -> None:
    """Best-effort: load .env so the anthropic path sees ANTHROPIC_API_KEY / BF_MODEL."""
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    load_dotenv()


def main(argv=None):
    _load_env()
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--provider", default="terminal", choices=["terminal", "anthropic", "stub"])
    common.add_argument("--run-id", default=_dt.date.today().isoformat())
    common.add_argument("--date", default=_dt.date.today().isoformat())
    common.add_argument(
        "--intake",
        default=None,
        help="path to intake JSON (default: data/intake.json, else sample)",
    )
    common.add_argument(
        "--json", action="store_true", help="emit machine-readable JSON (for the UI)"
    )

    parser = argparse.ArgumentParser(prog="bf", description="Brand Voice Content Engine")
    sub = parser.add_subparsers(dest="cmd", required=True)
    for name, fn in (
        ("post", cmd_post),
        ("gaps", cmd_gaps),
        ("posts", cmd_posts),
        ("onboard", cmd_onboard),
        ("ablate", cmd_ablate),
        ("report", cmd_report),
        ("run", cmd_run),
        ("doctor", cmd_doctor),
    ):
        sub.add_parser(name, parents=[common]).set_defaults(func=fn)

    args = parser.parse_args(argv)
    try:
        args.func(args)
    except NeedsCompletion as nc:
        print(nc, file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
