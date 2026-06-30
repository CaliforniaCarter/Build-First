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

from .ablation import (
    context_for,
    load_ladder,
    load_layers,
    run_ablation,
    run_field_ablation,
    run_persona_ablation,
)
from .blocks.draft import build_draft_prompt
from .blocks.gate import human_gate
from .blocks.intake import load_intake
from .blocks.persona import VOICE_PATH, build_voice, load_voice, render_voice
from .blocks.proof import check_text, load_proof_config
from .blocks.probe import unfilled_gaps
from .config import DATA_DIR, POSTS_DIR, PROFILES_DIR, RUNS_DIR
from .learn import learn
from .onboarding import load_onboarding, onboarding_summary
from .post import ALL_INPUTS, PostResult, evaluate, make_options, make_post, polish
from .providers import get_provider
from .providers.base import NeedsCompletion
from .report import RunReport, build_report, compute_places_to_refine, write_report
from .revise import revise
from .rubric.schemas import DIM_NAMES, GATE_NAMES
from .signals import mark_processed, pending_signals, record_signal
from .store import (
    clear_local_data,
    latest_final,
    list_posts,
    posting_streak,
    recent_post_openings,
    save_post,
    set_status,
    shipped_count,
)
from .takes import form_takes


def _provider(args):
    return get_provider(args.provider, RUNS_DIR / args.run_id)


def _intake(args):
    return load_intake(Path(args.intake) if args.intake else None)


def _onboard(intake, provider, force_persona=False):
    return build_voice(intake, provider, force=force_persona)


def cmd_onboard(args):
    intake = _intake(args)
    _onboard(intake, _provider(args), force_persona=True)
    print(f"wrote your voice profile to {VOICE_PATH}")


def cmd_ablate(args):
    """Timbre Labs: see what each input is worth. Default = add context one tier at a time;
    --fields = leave-one-out over every individual field (does each field earn its place?)."""
    intake = _intake(args)
    provider = _provider(args)
    persona_md = _onboard(intake, provider)
    if args.persona:
        baseline, results = run_persona_ablation(intake, provider, args.run_id)
        if args.json:
            print(json.dumps({"baseline": baseline, "voice_fields": results}, indent=2))
            return
        print(f"Baseline — full voice in: {baseline}/10\n")
        print("Drop one voice input, RE-EXTRACT the persona, re-score — what does the post lose?")
        for r in results:
            print(
                f"  {r['contribution']:>+5} ← {r['field']:22s} (without it: {r['score_without']}/10)"
            )
        print("\nA positive number = that voice input earns its place.")
        return
    if args.fields:
        baseline, results = run_field_ablation(intake, persona_md, provider, args.run_id)
        if args.json:
            print(json.dumps({"baseline": baseline, "fields": results}, indent=2))
            return
        print(f"Baseline — every field in: {baseline}/10\n")
        print("Drop one field, re-score — what does the post lose?")
        for r in results:
            print(
                f"  {r['contribution']:>+5} ← {r['field']:22s} (without it: {r['score_without']}/10)"
            )
        print("\nA positive number = that field earns its place (dropping it hurt the score).")
        return
    results = run_ablation(intake, persona_md, provider, args.run_id)
    for r in results:
        print(f"{r.level} {r.label:12s} {r.score.headline()}")


def cmd_report(args):
    """Timbre Labs: full ablation report — each level's post, score, and diff."""
    intake = _intake(args)
    provider = _provider(args)
    persona_md = _onboard(intake, provider)
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
    persona_md = _onboard(intake, provider)
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
    persona_md = _onboard(intake, provider)
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


def _proof_json(report):
    """The deterministic proof check, for the UI. None if not computed."""
    if report is None:
        return None
    return {
        "clean": report.clean,
        "slop_hits": report.slop_hits,
        "ungrounded": report.ungrounded,
        "redactions": report.redactions,
    }


def _print_proof(report):
    """A plain-language proof-check line for non-JSON output."""
    if report is None:
        return
    if report.clean:
        print("Proof check: ✓ clean — no slop, every number traces to your material")
        return
    if report.slop_hits:
        print(f"Proof check ⚠ slop/banned phrase(s): {', '.join(report.slop_hits)}")
    if report.ungrounded:
        print(f"Proof check ⚠ not in your material (fix or cut): {', '.join(report.ungrounded)}")


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
                    "proof_check": _proof_json(result.proof_report),
                    "saved": str(saved),
                    "draft": str(out),
                },
                indent=2,
            )
        )
        return
    print(result.final_draft)
    print(f"\nScore: {result.score.quality_avg}/10 · saved to {saved}")
    _print_proof(result.proof_report)


def cmd_post(args):
    """The product: draft TWO options in different shapes, score both, hand them to you to pick."""
    intake = _intake(args)
    provider = _provider(args)
    persona_md = _onboard(intake, provider)
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
                            "proof_check": _proof_json(r.proof_report),
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
        if r.proof:
            print("\nreceipts: " + " · ".join(r.proof))
        _print_proof(r.proof_report)
        print()
    print(f"Pick one: tb pick --run-id {args.run_id} --option <0/1>  (polishes it and saves)")


def cmd_pick(args):
    """Pick one of the two options, polish it (Writer's Council), save it, and log the choice."""
    intake = _intake(args)
    provider = _provider(args)
    vp = load_voice()
    persona_md = render_voice(vp) if vp else ""
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
    persona_md = _onboard(intake, provider)
    layers = load_layers()
    if args.post and not Path(args.post).exists():
        print(f"no such file: {args.post}", file=sys.stderr)
        return
    current = Path(args.post).read_text(encoding="utf-8") if args.post else latest_final()
    if not current:
        print("no post to revise — run `tb post` first or pass --post <file>", file=sys.stderr)
        return
    revised = revise(current, args.command, persona_md, layers, intake.output.hard_nevers, provider)
    final, proof, redactions, score, report = evaluate(
        revised, intake, persona_md, layers, provider, "score_revise", current
    )
    result = PostResult(
        first_draft=revised,
        final_draft=final,
        score=score,
        proof=proof,
        redactions=redactions,
        proof_report=report,
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


def cmd_voice(args):
    """Show the editable voice profile (the 'that's me?' artifact). Edit profiles/voice.json to confirm."""
    vp = load_voice()
    if vp is None:
        msg = "no voice profile yet — run `tb onboard` first"
        print(json.dumps({"error": msg}) if args.json else msg)
        return
    if args.json:
        print(
            json.dumps(
                {"path": str(VOICE_PATH), "voice": vp.model_dump(), "rendered": render_voice(vp)},
                indent=2,
            )
        )
    else:
        print(render_voice(vp))


def cmd_proof(args):
    """Run the deterministic proof check on a post (latest saved, or --post <file>): receipts,
    banned/slop phrases, and any number/specific that doesn't trace to your material."""
    intake = _intake(args)
    if args.post:
        if not Path(args.post).exists():
            print(f"no such file: {args.post}", file=sys.stderr)
            return
        text = Path(args.post).read_text(encoding="utf-8")
    else:
        text = latest_final()
        if not text:
            print("no post to check — run `tb post` first or pass --post <file>", file=sys.stderr)
            return
    report = check_text(text, intake)
    if args.json:
        print(json.dumps({"receipts": report.receipts, **_proof_json(report)}, indent=2))
        return
    if report.receipts:
        print("RECEIPTS")
        for r in report.receipts:
            print(f"  • {r}")
        print()
    print("PROOF CHECK")
    if report.clean:
        print("  ✓ no slop / banned phrases")
        print("  ✓ every number traces to your material")
    else:
        if report.slop_hits:
            print(f"  ⚠ slop/banned: {', '.join(report.slop_hits)}")
        if report.ungrounded:
            print(f"  ⚠ not in your material (fix or cut): {', '.join(report.ungrounded)}")
    if report.redactions:
        print(f"  ✓ redacted: {', '.join(report.redactions)}")


def cmd_sample(args):
    """Add a writing sample (an existing post/essay) to your voice corpus — the strongest signal."""
    path = Path(args.intake) if args.intake else (DATA_DIR / "intake.json")
    intake = _intake(args)
    text = args.text
    if args.file:
        if not Path(args.file).exists():
            print(f"no such file: {args.file}", file=sys.stderr)
            return
        text = Path(args.file).read_text(encoding="utf-8")
    text = (text or "").strip()
    if not text:
        print('nothing to add — pass --text "..." or --file <path>', file=sys.stderr)
        return
    if text in intake.voice.writing_samples:
        print("already have that sample.")
        return
    intake.voice.writing_samples.append(text)
    path.write_text(intake.model_dump_json(indent=2) + "\n", encoding="utf-8")
    n = len(intake.voice.writing_samples)
    msg = f"Added a writing sample ({n} now). Run `tb onboard` to refold your voice."
    print(json.dumps({"samples": n, "intake": str(path)}) if args.json else msg)


def cmd_takes(args):
    """Surface a few spiky takes you could post, grounded in your material (content playground)."""
    intake = _intake(args)
    provider = _provider(args)
    vp = load_voice()
    persona_md = render_voice(vp) if vp else ""
    takes = form_takes(intake, persona_md, provider)
    if args.json:
        print(json.dumps({"takes": takes}, indent=2))
        return
    if not takes:
        print("No takes yet — add more about what you believe (onboarding or `tb sample`).")
        return
    print("Takes you could post (grounded in your material):")
    for t in takes:
        print(f"  • {t['take']}")
        if t.get("based_on"):
            print(f"      ↳ from: {t['based_on']}")


def cmd_inspect(args):
    """Show exactly what Timbre knows + what it sends to the LLM. Nothing hidden."""
    intake = _intake(args)
    vp = load_voice()
    persona_md = render_voice(vp) if vp else "(run `tb onboard` first)"
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
                    "context": ctx,  # what Timbre knows, built from data/intake.json
                    "voice": persona_md,
                    "draft_prompt": prompt,  # the exact text sent to the LLM
                },
                indent=2,
            )
        )
        return
    print("=== WHAT TIMBRE KNOWS (from data/intake.json) ===")
    print(ctx)
    print("\n=== YOUR VOICE (voice.json, rendered) ===")
    print(persona_md)
    print("\n=== THE EXACT PROMPT SENT TO THE LLM ===")
    print(prompt)


def cmd_posts(args):
    """List the saved-post library + the always-right tally (shipped + streak). UI reads --json."""
    posts = list_posts()
    shipped, streak = shipped_count(posts), posting_streak(posts)
    if args.json:
        print(json.dumps({"posts": posts, "shipped": shipped, "streak": streak}, indent=2))
        return
    if not posts:
        print("No saved posts yet. Run `tb post` to make one.")
        return
    plural = "s" if len(posts) != 1 else ""
    streak_txt = f" · 🔥 {streak}-day streak" if streak > 1 else ""
    print(f"📚 {len(posts)} post{plural} · {shipped} shipped{streak_txt}\n")
    for p in posts:
        when = p.get("updated") or p.get("created") or p.get("date", "")
        mark = "✅" if p.get("status") == "posted" else "📝"
        print(f"{mark} {when}  {p['score']['quality']}/10  {p['slug']}")


def cmd_publish(args):
    """Mark a saved post as posted (or back to draft with --draft). Slug is from `tb posts`."""
    status = "draft" if args.draft else "posted"
    if not set_status(args.slug, status):
        print(f"no such post: {args.slug}", file=sys.stderr)
        return
    posts = list_posts()
    shipped, streak = shipped_count(posts), posting_streak(posts)
    if args.json:
        print(
            json.dumps({"slug": args.slug, "status": status, "shipped": shipped, "streak": streak})
        )
        return
    if status == "posted":
        plural = "s" if shipped != 1 else ""
        streak_txt = f" 🔥 {streak}-day streak —" if streak > 1 else ""
        print(
            f"🎉 Shipped: {args.slug}. That's {shipped} post{plural} live —{streak_txt} keep going."
        )
    else:
        print(f"{args.slug} → back to draft. ({shipped} still live.)")


def cmd_learn(args):
    """End-of-session learning: fold your recent picks + edits into voice.json, in place and
    conservatively. Picks are always logged for free (`tb pick`); this is the only AI call, batched."""
    if args.check:  # report pending count without folding — for the end-of-session consent prompt
        n = len(pending_signals())
        print(json.dumps({"pending": n}) if args.json else f"{n} pending signal(s) to fold")
        return
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

    vp = load_voice()
    if vp is None:
        msg = "no voice profile yet — run `tb onboard` first"
        print(json.dumps({"error": msg}) if args.json else msg)
        return
    batch = pending_signals()
    if not batch:
        msg = "Nothing pending — pick a post or pass --edited <file>, then run `tb learn`."
        print(json.dumps({"applied": [], "skipped": [], "folded": 0}) if args.json else msg)
        return
    applied, skipped = learn(batch, vp, _provider(args))
    if applied:
        VOICE_PATH.write_text(vp.model_dump_json(indent=2) + "\n", encoding="utf-8")
    mark_processed()
    if args.json:
        print(
            json.dumps(
                {
                    "applied": applied,
                    "skipped": skipped,
                    "folded": len(batch),
                    "voice": str(VOICE_PATH),
                },
                indent=2,
            )
        )
        return
    print(f"Folded {len(batch)} signal(s) — picks + edits — into your voice.")
    if applied:
        print("Learned (voice.json updated in place, no bloat):")
        for a in applied:
            print(f"  - {a}")
        print(f"\nWrote {VOICE_PATH}. The next `tb post` will use it.")
    else:
        print("No new voice signal in this batch. Voice unchanged.")
    if skipped:
        print(f"(skipped: {'; '.join(skipped)})")


def cmd_reset(args):
    """Clear your local data (voice, profile, answers, posts, signals, runs) for a fresh cold
    start. Configs (onboarding/proof/rubric/labs) and the synthetic sample are kept."""
    removed = clear_local_data(PROFILES_DIR, DATA_DIR, POSTS_DIR, RUNS_DIR)
    if args.json:
        print(json.dumps({"reset": True, "removed": removed}, indent=2))
        return
    if not removed:
        print("Already a cold start — nothing to clear.")
        return
    print(f"Reset to a cold start — cleared {len(removed)} item(s):")
    for r in removed:
        print(f"  - {r}")
    print("\nRun `tb onboard` (or /timbre-onboard) to start fresh.")


def cmd_doctor(args):
    intake = _intake(args)
    print(f"intake ok: {intake.name}, topic={intake.idea.topic[:60]!r}")
    print(f"channels={intake.output.channels} hard_nevers={intake.output.hard_nevers}")
    try:
        print(onboarding_summary(load_onboarding()))
    except (FileNotFoundError, ValueError) as e:
        print(f"onboarding config ERROR: {e}")
    try:
        pc = load_proof_config()
        print(
            f"proof config ok: {len(pc.slop_phrases)} slop phrase(s), "
            f"grounding={pc.grounding_scope}, on_flag={pc.on_flag}"
        )
    except ValueError as e:
        print(f"proof config ERROR: {e}")
    print(f"rubric ok: {len(GATE_NAMES)} gates, {len(DIM_NAMES)} dimensions (engine/rubric.json)")
    try:
        print(f"labs ladder ok: {len(load_ladder())} tiers (engine/labs.json)")
    except (FileNotFoundError, ValueError, KeyError) as e:
        print(f"labs ladder ERROR: {e}")
    print(f"voice profile: {'present' if load_voice() else 'not built yet (run `tb onboard`)'}")


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
        ("voice", cmd_voice),
        ("proof", cmd_proof),
        ("sample", cmd_sample),
        ("takes", cmd_takes),
        ("inspect", cmd_inspect),
        ("posts", cmd_posts),
        ("publish", cmd_publish),
        ("learn", cmd_learn),
        ("onboard", cmd_onboard),
        ("reset", cmd_reset),
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
    parsers["learn"].add_argument(
        "--check",
        action="store_true",
        help="report pending signals without folding (consent prompt)",
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
    parsers["sample"].add_argument("--text", default=None, help="a post/essay you wrote, inline")
    parsers["sample"].add_argument("--file", default=None, help="a file with your writing")
    parsers["proof"].add_argument(
        "--post", default=None, help="the post to check (default: last saved)"
    )
    parsers["ablate"].add_argument(
        "--fields", action="store_true", help="leave-one-out per field (does each field help?)"
    )
    parsers["ablate"].add_argument(
        "--persona",
        action="store_true",
        help="leave-one-out per voice input (re-extracts the persona each time)",
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
