"""CLI — onboard, ablate, report, run, doctor.

Default provider is `terminal` (no API key): each reasoning step writes a prompt and
waits for an answer file. `run` does the whole thing: onboard -> ablation -> report.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import sys

from .ablation import load_layers, run_ablation
from .blocks import council
from .blocks import draft as draft_block
from .blocks import receipts as receipts_block
from .blocks.brief import build_brief, load_brief, write_brief
from .blocks.gate import human_gate
from .blocks.intake import load_intake
from .blocks.persona import build_persona
from .blocks.profile import write_profile_docs
from .config import PROFILES_DIR, RUNS_DIR
from .posttypes import get_post_type
from .providers import get_provider
from .providers.base import NeedsCompletion
from .report import RunReport, build_report, compute_places_to_refine, write_report


def _provider(args):
    return get_provider(args.provider, RUNS_DIR / args.run_id)


def _onboard(intake, provider):
    paths = write_profile_docs(intake)
    persona_md = build_persona(intake, provider)
    return paths, persona_md


def cmd_onboard(args):
    intake = load_intake()
    paths, _ = _onboard(intake, _provider(args))
    print(f"wrote {paths['profile']} and {paths['context']} and {PROFILES_DIR / 'persona.md'}")


def cmd_ablate(args):
    intake = load_intake()
    provider = _provider(args)
    persona_md = (PROFILES_DIR / "persona.md").read_text(encoding="utf-8")
    results = run_ablation(intake, persona_md, provider, args.run_id)
    for r in results:
        print(f"{r.level} {r.label:12s} {r.score.headline()}")


def cmd_report(args):
    intake = load_intake()
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
    intake = load_intake()
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


def cmd_generate(args):
    """The shippable path: intake + post type -> editable brief -> the final post.

    Two-step and resumable (same idea as the terminal provider). First run writes the
    brief and stops so you can hand-edit it; re-run drafts from the edited brief.
    """
    intake = load_intake()
    run_dir = RUNS_DIR / args.run_id
    brief_path = run_dir / "brief.json"

    if not brief_path.exists():
        paths = write_brief(build_brief(intake, args.type), run_dir)
        print(
            f"brief  -> {paths['json']}\nreadable -> {paths['md']}\n"
            f"edit {paths['json']}, then re-run `bf generate` to draft."
        )
        return

    provider = _provider(args)
    brief = load_brief(run_dir)
    persona_path = PROFILES_DIR / "persona.md"
    persona_md = persona_path.read_text(encoding="utf-8") if persona_path.exists() else ""
    layers = load_layers(get_post_type(brief.post_type).layer_files)

    prompt = draft_block.build_draft_prompt_from_brief(brief, persona_md or None, layers)
    text = draft_block.draft("draft", prompt, provider)
    text, clog = council.revise(text, persona_md, layers, provider)
    (run_dir / "council_log.json").write_text(json.dumps(clog, indent=2), encoding="utf-8")

    text, proof, redactions = receipts_block.attach_receipts(text, intake)
    if proof or redactions:
        (run_dir / "receipts.json").write_text(
            json.dumps({"proof": proof, "redacted": redactions}, indent=2), encoding="utf-8"
        )
    out = human_gate(text, run_dir)
    print(f"post -> {out}  (copied to clipboard; review before posting)")


def cmd_doctor(args):
    intake = load_intake()
    print(f"intake ok: {intake.name}, topic={intake.idea.topic[:60]!r}")
    print(f"channels={intake.output.channels} hard_nevers={intake.output.hard_nevers}")


def main(argv=None):
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--provider", default="terminal", choices=["terminal", "anthropic"])
    common.add_argument("--run-id", default=_dt.date.today().isoformat())
    common.add_argument("--date", default=_dt.date.today().isoformat())

    parser = argparse.ArgumentParser(prog="bf", description="Brand Voice Content Engine")
    sub = parser.add_subparsers(dest="cmd", required=True)
    for name, fn in (
        ("onboard", cmd_onboard),
        ("ablate", cmd_ablate),
        ("report", cmd_report),
        ("run", cmd_run),
        ("doctor", cmd_doctor),
    ):
        sub.add_parser(name, parents=[common]).set_defaults(func=fn)

    gen = sub.add_parser("generate", parents=[common])
    gen.add_argument("--type", default="linkedin", help="post type (see engine/posttypes.py)")
    gen.set_defaults(func=cmd_generate)

    args = parser.parse_args(argv)
    try:
        args.func(args)
    except NeedsCompletion as nc:
        print(nc, file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
