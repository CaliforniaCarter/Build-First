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

from .ablation import context_for, load_layers, run_ablation
from .blocks.draft import build_draft_prompt
from .blocks.gate import human_gate
from .blocks.intake import load_intake
from .blocks.persona import build_persona
from .blocks.probe import unfilled_gaps
from .blocks.profile import write_profile_docs
from .config import DATA_DIR, PROFILES_DIR, RUNS_DIR
from .learn import learn
from .post import ALL_INPUTS, PostResult, evaluate, make_post
from .providers import get_provider
from .providers.base import NeedsCompletion
from .report import RunReport, build_report, compute_places_to_refine, write_report
from .revise import revise
from .store import latest_final, list_posts, save_post


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
    """Admin / lab: add context one tier at a time and watch the score move."""
    intake = _intake(args)
    provider = _provider(args)
    persona_md = (PROFILES_DIR / "persona.md").read_text(encoding="utf-8")
    results = run_ablation(intake, persona_md, provider, args.run_id)
    for r in results:
        print(f"{r.level} {r.label:12s} {r.score.headline()}")


def cmd_report(args):
    """Admin / lab: full ablation report — each level's post, score, and diff."""
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


def cmd_admin(args):
    """Admin: the full eval scale + how your change moved it. Not user-facing."""
    intake = _intake(args)
    provider = _provider(args)
    _onboard(intake, provider)
    persona_md = (PROFILES_DIR / "persona.md").read_text(encoding="utf-8")
    s = make_post(intake, persona_md, provider, args.run_id).score
    posts = list_posts()
    baseline = posts[-1]["score"]["quality"] if posts else None
    if args.json:
        print(
            json.dumps(
                {
                    "quality": s.quality_avg,
                    "gates_passed": s.gates_passed,
                    "gates_total": s.gates_total,
                    "baseline_quality": baseline,
                    "delta": round(s.quality_avg - baseline, 1) if baseline is not None else None,
                    "dimensions": [
                        {"name": d.name, "score": d.score, "reason": d.reason} for d in s.dimensions
                    ],
                    "gates": [
                        {"name": g.name, "passed": g.passed, "reason": g.reason} for g in s.gates
                    ],
                },
                indent=2,
            )
        )
        return
    print(f"EVAL (admin) — quality {s.quality_avg}/10, gates {s.gates_passed}/{s.gates_total}")
    if baseline is not None:
        print(f"vs last saved: {baseline} -> {s.quality_avg} ({s.quality_avg - baseline:+.1f})")
    print("\nDimensions:")
    for d in s.dimensions:
        print(f"  {d.score:>2}/10  {d.name:22s} {d.reason}")
    print("\nGates:")
    for g in s.gates:
        print(f"  {'PASS' if g.passed else 'FAIL'}  {g.name:24s} {g.reason}")


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


def _emit_post(result, saved, out, args):
    """Return the post + structured eval. The LLM presents/suggests/probes from this."""
    if args.json:
        print(
            json.dumps(
                {
                    "final": result.final_draft,
                    "score": result.score.quality_avg,
                    "evaluation": {
                        "dimensions": [
                            {"name": d.name, "score": d.score, "reason": d.reason}
                            for d in result.score.dimensions
                        ],
                        "gates": [
                            {"name": g.name, "passed": g.passed, "reason": g.reason}
                            for g in result.score.gates
                        ],
                    },
                    "receipts": result.proof,
                    "saved": str(saved),
                    "draft": str(out),
                },
                indent=2,
            )
        )
        return
    print(result.final_draft)
    print(f"\nScore: {result.score.quality_avg}/10 · saved to {saved} · copied to clipboard")


def cmd_post(args):
    """The product: draft ONE post from every input, polish, save, return structured output."""
    intake = _intake(args)
    provider = _provider(args)
    _onboard(intake, provider)
    persona_md = (PROFILES_DIR / "persona.md").read_text(encoding="utf-8")
    result = make_post(intake, persona_md, provider, args.run_id)
    out = human_gate(result.final_draft, RUNS_DIR / args.run_id / "post")
    saved = save_post(result, intake, args.date)
    _emit_post(result, saved, out, args)


def cmd_revise(args):
    """Revise the current post by your command, re-score, and save. The LLM does the rewrite."""
    intake = _intake(args)
    provider = _provider(args)
    persona_md = (PROFILES_DIR / "persona.md").read_text(encoding="utf-8")
    layers = load_layers()
    current = Path(args.post).read_text(encoding="utf-8") if args.post else latest_final()
    if not current:
        print("no post to revise — run `tb post` first or pass --post <file>", file=sys.stderr)
        return
    revised = revise(current, args.command, persona_md, layers, intake.output.hard_nevers, provider)
    final, proof, redactions, score = evaluate(
        revised, intake, persona_md, layers, provider, "score_revise", current
    )
    result = PostResult(
        first_draft=revised, final_draft=final, score=score, proof=proof, redactions=redactions
    )
    out = human_gate(final, RUNS_DIR / args.run_id / "post")
    saved = save_post(result, intake, args.date)
    _emit_post(result, saved, out, args)


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


def cmd_persona(args):
    """Show the extracted voice profile (the 'that's me?' artifact). Edit the file to confirm."""
    path = PROFILES_DIR / "persona.md"
    if not path.exists():
        msg = "no persona yet — run `tb onboard` first"
        print(json.dumps({"error": msg}) if args.json else msg)
        return
    text = path.read_text(encoding="utf-8")
    if args.json:
        print(json.dumps({"path": str(path), "persona_md": text}, indent=2))
    else:
        print(text)


def cmd_inspect(args):
    """Show exactly what the LLM sees: your voice profile + the assembled prompt. Nothing hidden."""
    intake = _intake(args)
    persona_path = PROFILES_DIR / "persona.md"
    persona_md = (
        persona_path.read_text(encoding="utf-8")
        if persona_path.exists()
        else "(run `tb onboard` first)"
    )
    layers = load_layers()
    ctx = context_for(ALL_INPUTS, intake)
    prompt = build_draft_prompt(
        intake.idea.topic,
        ctx,
        persona_md,
        layers,
        intake.output.hard_nevers,
        intake.output.channels,
    )
    if args.json:
        print(
            json.dumps(
                {
                    "persona_md": persona_md,
                    "context_block": ctx,
                    "layers": layers,
                    "draft_prompt": prompt,
                },
                indent=2,
            )
        )
        return
    print("=== PERSONA (your voice — what the LLM is told to match) ===")
    print(persona_md)
    print("\n=== CONTEXT (assembled from your intake) ===")
    print(ctx)
    print("\n=== THE EXACT PROMPT SENT TO THE LLM ===")
    print(prompt)


def cmd_posts(args):
    """List the saved-post library. The UI reads --json."""
    posts = list_posts()
    if args.json:
        print(json.dumps(posts, indent=2))
        return
    if not posts:
        print("No saved posts yet. Run `tb post` to make one.")
        return
    for p in posts:
        s = p["score"]
        print(
            f"{p['date']}  {s['quality']}/10  gates {s['gates_passed']}/{s['gates_total']}  {p['topic'][:60]}"
        )


def cmd_learn(args):
    """Self-learning loop: turn your edit into tighter profile fields, never bloat."""
    path = Path(args.intake) if args.intake else (DATA_DIR / "intake.json")
    intake = _intake(args)
    edited = Path(args.edited).read_text(encoding="utf-8")
    original = Path(args.original).read_text(encoding="utf-8") if args.original else latest_final()
    if not original:
        print("no original draft — pass --original <file> or run `tb post` first", file=sys.stderr)
        return
    applied, skipped = learn(original, edited, intake, _provider(args))
    if applied:
        path.write_text(intake.model_dump_json(indent=2) + "\n", encoding="utf-8")
    if args.json:
        print(json.dumps({"applied": applied, "skipped": skipped, "intake": str(path)}, indent=2))
        return
    if applied:
        print("Learned (profile updated in place, no bloat):")
        for a in applied:
            print(f"  - {a}")
        print(f"\nWrote {path}. The next `tb post` will use it.")
    else:
        print("Nothing to learn from this edit — no new voice/identity signal. Profile unchanged.")
    if skipped:
        print(f"(skipped: {'; '.join(skipped)})")


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

    parser = argparse.ArgumentParser(prog="tb", description="Brand Voice Content Engine")
    sub = parser.add_subparsers(dest="cmd", required=True)
    parsers = {}
    for name, fn in (
        ("post", cmd_post),
        ("revise", cmd_revise),
        ("gaps", cmd_gaps),
        ("persona", cmd_persona),
        ("inspect", cmd_inspect),
        ("posts", cmd_posts),
        ("learn", cmd_learn),
        ("onboard", cmd_onboard),
        ("ablate", cmd_ablate),
        ("report", cmd_report),
        ("admin", cmd_admin),
        ("run", cmd_run),
        ("doctor", cmd_doctor),
    ):
        p = sub.add_parser(name, parents=[common])
        p.set_defaults(func=fn)
        parsers[name] = p
    parsers["learn"].add_argument("--edited", required=True, help="path to your edited post")
    parsers["learn"].add_argument(
        "--original", default=None, help="the engine's draft (default: last saved post)"
    )
    parsers["revise"].add_argument(
        "--command", required=True, help="what to change, in plain words"
    )
    parsers["revise"].add_argument(
        "--post", default=None, help="the post to revise (default: last saved)"
    )

    args = parser.parse_args(argv)
    try:
        args.func(args)
    except NeedsCompletion as nc:
        print(nc, file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
