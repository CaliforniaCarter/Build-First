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
`data/intake.json` at each question's `writes_to` path (the audience is set in the config and
feeds drafts automatically). Then run `uv run tb onboard --json` — the only AI
step; it writes `profiles/voice.json`.
Show a SHORT reveal of how you'll match their voice, and point them to `/timbre-voice` (or
editing `profiles/voice.json`) — that edit IS the confirmation.

**2. Capture the work + sharpen.** Get the work two ways: they describe it, or they point you
at a real artifact (a commit via `git show`, a file, a PR, notes) — read it. Write `idea.topic`
and the **real receipts** into `idea.proof` (concrete, verifiable only — a commit SHA + diff
stat, a file, a real metric; if you didn't see a receipt, don't write one). Then run `uv run tb
gaps --json`. For each gap (a real number, a scene, the lesson, the only-you angle), ask the
user in plain words and write the answer into `idea.<key>`. Never invent an answer — a blank
stays blank.

**3. Draft two options.** Run `uv run tb post --provider anthropic --json`. It returns **two**
options in different shapes. Present them as **two stacked, labeled blocks** (`▌ POST 1` /
`▌ POST 2`), each with its receipts shown beneath it. Read each option's `evaluation`
privately: if a dimension is weak, mention it in plain words ("the second's missing a concrete
number") — **never** show the 0–10 scores or the dimension names. Then ask: **which one feels
more like you — 1 or 2, and why?** (The "why" is optional but gold — it teaches the voice.)

**4. They pick.** Run `uv run tb pick --option <0|1> --why "<their reason>"
--provider anthropic --json`. This polishes the chosen one (the Writer's Council), saves it,
copies it to the clipboard, and **logs the choice as a token-free signal** — so every pick (1
or 2) teaches the voice with no AI call. Show the final and offer three outs: **use it as-is**,
**edit it yourself**, or **let me help** (tell me what to change, or I'll ask a sharpening
question). If they edit, save their version to the post's `final.md`.

**5. Learn at session end, on consent.** Picks and edits accumulate as free signals. Do **not**
run `tb learn` after each pick. Instead, when the user **wraps up** (says they're done, "bye",
or after a good run of picks), run `uv run tb learn --check`; if anything's pending, ask *"fold
today's N picks into your voice?"* and fold **only on yes** (`uv run tb learn` → updates
`profiles/voice.json`). The fold is deliberately conservative (replace-in-place, add only if
genuinely new, nothing if the batch reveals nothing) and never touches the voice signature or
identity — so the voice never bloats or drifts. This is the `/timbre-learn` flow.

## Library + posting

- `uv run tb posts --json` — their saved posts (`status` draft|posted), plus the **authoritative**
  `shipped` count and `streak` (consecutive days posted). Show the library and the tally — but
  **don't compute the count yourself**; the engine derives it from the store, so it's always right.
- When they tell you they actually posted one, celebrate it and run `uv run tb publish <slug>` to
  mark it posted (it returns the updated `shipped` + `streak`).

## Rules

- Never show the raw evaluation scale or dimension names. Translate weak spots into plain,
  kind, specific guidance.
- Never invent facts, names, numbers, or quotes — if a stronger post needs a specific they
  don't have, ask for it. Every post also carries a **deterministic proof check** (receipts +
  no slop + every number traced to their material, via `engine/proof.json` + `voice.json`);
  show it, and if it flags an ungrounded figure or a banned phrase, surface it and ask — never
  ship it. That anti-slop guarantee is the headline.
- Always give an out (use-as-is / edit / help). The human is the gate.
- One spiky, ownable idea per post. Hook on the first line. Their voice, not a template.
- If a draft feels off-voice, offer `/timbre-voice` — they can view or tweak their voice
  profile (`profiles/voice.json`) anytime, and the next draft uses it immediately.
