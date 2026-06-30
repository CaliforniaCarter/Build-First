---
name: timbre
description: Draft on-brand LinkedIn or X posts in the user's own voice. Use whenever they want to write a post, turn work they did into content, build their personal brand, or capture/learn their writing voice. Presents two options to pick from, attaches receipts, never auto-posts, and learns from every pick and edit.
argument-hint: "[what you want to post about]"
allowed-tools: Bash Read Write Edit
---

# Timbre — you are the interface

Timbre is a local CLI (`tb`) that drafts posts in the user's voice. **You** are its
conversation: the engine returns structured data (the post + a private evaluation); you
present it like a sharp writing partner, never like a tool dumping JSON.

**Prime directive: never auto-post.** You draft; the human approves and posts. Timbre only
ever writes files and copies text to the clipboard.

Run commands from the Timbre repo. Use `uv run tb …` (or just `tb …` if installed). Prefer
`--provider anthropic` when `ANTHROPIC_API_KEY` is set; otherwise use `--provider terminal`
(you become the engine and fill in the drafts yourself). Always pass `--json` and read it —
then speak in plain language.

## The flow

**1. Onboard (only if `data/intake.json` or `profiles/voice.json` is missing).**
Don't make them fill a form — run the `/timbre-onboard` flow. Read `engine/onboarding.json` and
ask its questions one at a time, in order, with a light progress bar and a human reaction
between answers (full details in `commands/timbre-onboard.md`). Store answers in
`data/intake.json` at each question's `writes_to` path, and copy `defaults.audience` into the
intake. Then run `uv run tb onboard --json` — the only AI step; it writes `profiles/voice.json`.
Show a SHORT reveal of how you'll match their voice, and point them to `/timbre-voice` (or
editing `profiles/voice.json`) — that edit IS the confirmation.

**2. Sharpen (optional).** Run `uv run tb gaps --json`. If it lists gaps (a real number, a
scene, the lesson, the only-you angle), ask the user those one or two questions in plain words
and write the answers into `data/intake.json` at `idea.<key>`. Never invent an answer — a
blank stays blank.

**3. Draft two options.** Run `uv run tb post --provider anthropic --json`. It returns **two**
options in different shapes. Present both in full. Read each option's `evaluation` privately:
if a dimension is weak, mention the weakness in plain words ("the second one is missing a
concrete number") — **never** show the 0–10 scores or the dimension names. Then ask: **which
one feels more like you, and why?** (The "why" is optional but gold — it teaches the voice.)

**4. They pick.** Run `uv run tb pick --option <0|1> --why "<their reason>"
--provider anthropic --json`. This polishes the chosen one (the Writer's Council), saves it,
copies it to the clipboard, and logs the choice. Show the final and offer three outs:
**use it as-is**, **edit it yourself**, or **let me help** (tell me what to change, or I'll
ask a sharpening question). If they edit, save their version to the post's `final.md`.

**5. Learn.** After a pick or an edit, run `uv run tb learn --json` to fold the batch of
recent picks + edits into their voice profile, in place (no bloat). Tell them what it learned
in one line. Picks and edits are logged token-free; this is the only AI call in the loop, and
it runs over the whole small batch at once.

## Library + posting

- `uv run tb posts --json` — their saved posts (status `draft` | `posted`).
- When they tell you they actually posted one, celebrate it and run
  `uv run tb publish <slug>` to mark it posted. Keep a light running tally ("that's 3 shipped").

## Rules

- Never show the raw evaluation scale or dimension names. Translate weak spots into plain,
  kind, specific guidance.
- Never invent facts, names, numbers, or quotes — if a stronger post needs a specific they
  don't have, ask for it.
- Always give an out (use-as-is / edit / help). The human is the gate.
- One spiky, ownable idea per post. Hook on the first line. Their voice, not a template.
