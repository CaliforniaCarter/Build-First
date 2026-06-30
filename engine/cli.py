"""CLI — the product (`post`, `gaps`, `posts`) and Timbre Labs (`ablate`, `report`, `labs`).

`post` makes one in-voice post you approve; `gaps` is the gap-driven probe; `posts` lists the
saved library. Timbre Labs (`ablate`/`report`/`labs`) is the builder's eval-testing bench.
Default provider is `terminal` (Claude is the engine, no API key); `--json` emits UI output.
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
from .post import ALL_INPUTS, PostResult, evaluate, make_options, make_post, polish
from .providers import get_provider
from .providers.base import NeedsCompletion
from .report import RunReport, build_report, compute_places_to_refine, write_report
from .revise import revise
from .signals import mark_processed, pending_signals, record_signal
from .store import latest_final, list_posts, recent_post_openings, save_post, set_status


def _provider(args):
    return get_provider(args.provider, RUNS_DIR / args.run_id)


def _intake(args):
    return load_intake(Path(args.intake) if args.intake else None)


def _onboard(intake, provider, force_persona=False):
    paths = write_profile_docs(intake)
    persona_md = build_persona(intake, provider, force=force_persona)
    return paths, persona_md


def cmd_onboard(args):
    intake = _intake(args)
    paths, _ = _onboard(intake, _provider(args), force_persona=True)
    print(f"wrote {paths['profile']} and {paths['context']} and {PROFILES_DIR / 'persona.md'}")


def cmd_ablate(args):
    """Timbre Labs: add context one tier at a time and watch the score move."""
    intake = _intake(args)
    provider = _provider(args)
    _, persona_md = _onboard(intake, provider)
    results = run_ablation(intake, persona_md, provider, args.run_id)
    for r in results:
        print(f"{r.level} {r.label:12s} {r.score.headline()}")


def cmd_report(args):
    """Timbre Labs: full ablation report — each level's post, score, and diff."""
    intake = _intake(args)
    provider = _provider(args)
    _, persona_md = _onboard(intake, provider)
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


def cmd_labs(args):
    """Timbre Labs: the full eval scale + how your change moved it. Not user-facing."""
    intake = _intake(args)
    provider = _provider(args)
    _, persona_md = _onboard(intake, provider)
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
    print(f"Timbre Labs — quality {s.quality_avg}/10, gates {s.gates_passed}/{s.gates_total}")
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
    _, persona_md = _onboard(intake, provider)
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
    print(f"\nScore: {result.score.quality_avg}/10 · saved to {saved}")


def cmd_post(args):
    """The product: draft TWO options in different shapes, score both, hand them to you to pick."""
    intake = _intake(args)
    provider = _provider(args)
    _, persona_md = _onboard(intake, provider)
    options = make_options(
        intake, persona_md, provider, args.run_id, recent_openings=recent_post_openings()
    )
    if args.json:
        print(
            json.dumps(
                {
                    "run_id": args.run_id,
                    "options": [
                        {
                            "option": i,
                            "final": r.final_draft,
                            "score": r.score.quality_avg,
                            "evaluation": {
                                "dimensions": [
                                    {"name": d.name, "score": d.score, "reason": d.reason}
                                    for d in r.score.dimensions
                                ],
                                "gates": [
                                    {"name": g.name, "passed": g.passed, "reason": g.reason}
                                    for g in r.score.gates
                                ],
                            },
                            "receipts": r.proof,
                        }
                        for i, r in enumerate(options)
                    ],
                },
                indent=2,
            )
        )
        return
    for i, r in enumerate(options):
        print(f"=== OPTION {i} · {r.score.quality_avg}/10 ===")
        print(r.final_draft)
        print()
    print(f"Pick one: tb pick --run-id {args.run_id} --option <0/1>  (polishes it and saves)")


def cmd_pick(args):
    """Pick one of the two options, polish it (Writer's Council), save it, and log the choice."""
    intake = _intake(args)
    provider = _provider(args)
    persona_md = (PROFILES_DIR / "persona.md").read_text(encoding="utf-8")
    post_dir = RUNS_DIR / args.run_id / "post"
    opt = post_dir / f"option_{args.option}.md"
    if not opt.exists():
        print(f"no such option: {opt} (run `tb post` first)", file=sys.stderr)
        return
    chosen = opt.read_text(encoding="utf-8").strip()
    result = polish(chosen, intake, persona_md, provider)
    out = human_gate(result.final_draft, post_dir)
    saved = save_post(result, intake, args.date)
    # Log the A-vs-B choice as a token-free signal; `tb learn` folds it in later.
    other = post_dir / f"option_{0 if str(args.option) == '1' else 1}.md"
    rejected = other.read_text(encoding="utf-8").strip() if other.exists() else ""
    first = lambda t: t.splitlines()[0] if t else ""  # noqa: E731 — opening line only
    record_signal(
        "pick",
        {
            "chosen_opening": first(chosen),
            "rejected_opening": first(rejected),
            "why": args.why or "",
        },
    )
    _emit_post(result, saved, out, args)


def cmd_revise(args):
    """Revise the current post by your command, re-score, and save. The LLM does the rewrite."""
    intake = _intake(args)
    provider = _provider(args)
    _, persona_md = _onboard(intake, provider)
    layers = load_layers()
    if args.post and not Path(args.post).exists():
        print(f"no such file: {args.post}", file=sys.stderr)
        return
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
    """Show exactly what Timbre knows about you + what it sends to the LLM. Nothing hidden."""
    intake = _intake(args)

    def _read(name):
        p = PROFILES_DIR / name
        return p.read_text(encoding="utf-8") if p.exists() else "(run `tb onboard` first)"

    profile_md = _read("profile.md")
    context_md = _read("context.md")
    persona_md = _read("persona.md")
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
                    "profile_md": profile_md,
                    "context_md": context_md,
                    "persona_md": persona_md,
                    "draft_prompt": prompt,  # the exact text sent to the LLM
                },
                indent=2,
            )
        )
        return
    print("=== WHO YOU ARE (profile.md) ===")
    print(profile_md)
    print("\n=== TODAY'S CONTEXT (context.md) ===")
    print(context_md)
    print("\n=== YOUR VOICE (persona.md) ===")
    print(persona_md)
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
        when = p.get("updated") or p.get("created") or p.get("date", "")
        print(f"{when}  [{p.get('status', 'draft')}]  {p['score']['quality']}/10  {p['slug']}")


def cmd_publish(args):
    """Mark a saved post as posted (or back to draft with --draft). Slug is from `tb posts`."""
    status = "draft" if args.draft else "posted"
    if set_status(args.slug, status):
        print(f"{args.slug} -> {status}")
    else:
        print(f"no such post: {args.slug}", file=sys.stderr)


def cmd_learn(args):
    """Self-learning loop: fold your recent picks + edits into a tighter profile, in place."""
    path = Path(args.intake) if args.intake else (DATA_DIR / "intake.json")
    intake = _intake(args)
    # An explicit --edited records an edit signal first, so it joins the pending batch.
    if args.edited:
        if not Path(args.edited).exists():
            print(f"no such file: {args.edited}", file=sys.stderr)
            return
        if args.original and not Path(args.original).exists():
            print(f"no such file: {args.original}", file=sys.stderr)
            return
        original = (
            Path(args.original).read_text(encoding="utf-8") if args.original else latest_final()
        )
        if not original:
            print("no draft to compare — pass --original or run `tb post` first", file=sys.stderr)
            return
        record_signal(
            "edit",
            {"original": original, "edited": Path(args.edited).read_text(encoding="utf-8")},
        )

    batch = pending_signals()
    if not batch:
        msg = "Nothing pending — pick a post or pass --edited <file>, then run `tb learn`."
        print(json.dumps({"applied": [], "skipped": [], "folded": 0}) if args.json else msg)
        return
    applied, skipped = learn(batch, intake, _provider(args))
    if applied:
        path.write_text(intake.model_dump_json(indent=2) + "\n", encoding="utf-8")
    mark_processed()
    if args.json:
        print(
            json.dumps(
                {"applied": applied, "skipped": skipped, "folded": len(batch), "intake": str(path)},
                indent=2,
            )
        )
        return
    print(f"Folded {len(batch)} signal(s) — picks + edits — into your profile.")
    if applied:
        print("Learned (profile updated in place, no bloat):")
        for a in applied:
            print(f"  - {a}")
        print(f"\nWrote {path}. The next `tb post` will use it.")
    else:
        print("No new voice/identity signal in this batch. Profile unchanged.")
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

    parser = argparse.ArgumentParser(
        prog="tb", description="Timbre — capture your voice, draft posts you approve."
    )
    sub = parser.add_subparsers(dest="cmd", required=True)
    parsers = {}
    for name, fn in (
        ("post", cmd_post),
        ("pick", cmd_pick),
        ("revise", cmd_revise),
        ("gaps", cmd_gaps),
        ("persona", cmd_persona),
        ("inspect", cmd_inspect),
        ("posts", cmd_posts),
        ("publish", cmd_publish),
        ("learn", cmd_learn),
        ("onboard", cmd_onboard),
        ("ablate", cmd_ablate),
        ("report", cmd_report),
        ("labs", cmd_labs),
        ("run", cmd_run),
        ("doctor", cmd_doctor),
    ):
        p = sub.add_parser(name, parents=[common])
        p.set_defaults(func=fn)
        parsers[name] = p
    parsers["learn"].add_argument(
        "--edited", default=None, help="path to your edited post (also folds pending picks)"
    )
    parsers["learn"].add_argument(
        "--original", default=None, help="the engine's draft (default: last saved post)"
    )
    parsers["revise"].add_argument(
        "--command", required=True, help="what to change, in plain words"
    )
    parsers["revise"].add_argument(
        "--post", default=None, help="the post to revise (default: last saved)"
    )
    parsers["publish"].add_argument("slug", help="the post's folder name (see `tb posts`)")
    parsers["publish"].add_argument("--draft", action="store_true", help="move it back to draft")
    parsers["pick"].add_argument("--option", required=True, help="which option to keep (0 or 1)")
    parsers["pick"].add_argument(
        "--why", default=None, help="why you picked it (optional; feeds learning)"
    )

    args = parser.parse_args(argv)
    try:
        args.func(args)
    except NeedsCompletion as nc:
        print(nc, file=sys.stderr)
        return 2
    except ValueError as e:
        # malformed model output (bad JSON / failed validation) — fail cleanly, not a traceback
        print(f"couldn't parse the model's output: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
