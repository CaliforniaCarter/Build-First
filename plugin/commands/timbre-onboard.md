---
description: Capture your writing voice from a cold start (Timbre)
argument-hint: "[optional: anything about you, or a post you're proud of]"
allowed-tools: Bash Read Write Edit
---

Onboard the user into Timbre. The noisy part — collecting their answers — happens in a clean
**web page** (no API key, no terminal mechanics). You finish the job in the terminal: one
personalized this-or-that, then the voice extraction and a short reveal. Context they gave: **$ARGUMENTS**

## How to run it

1. **Open the web intake and wait.** Run `uv run tb welcome` **in the background** (it opens a
   browser page and returns the moment the user clicks **Done** — that can take a few minutes, so
   the background runner is what keeps it from being cut off). Say **one** short line and nothing
   else: *"I opened a quick setup page in your browser — fill it out and hit Done, and I'll take it
   from there."* Then wait for the command to return. (The page writes the deterministic answers
   straight into `data/intake.json` — name, background, resume, writing samples, and the
   weekend/lunch/teach answers. You do **not** re-ask any of these.)

2. **The personalized this-or-that** (`style_pick`, the only question NOT in the web). Read
   `engine/onboarding.json` for the `style_pick` question and `data/intake.json` for what they
   gave. Follow that question's `generate` instruction: from **their own resume + answers**, write
   TWO short example posts (2–4 lines each) about ONE real thing from their material — same facts,
   only the *feel* differs. **Invent nothing**, and **never name the difference** (no "dry vs
   warm"). Show them as **A** and **B**, ask which is more them, and store the chosen example's
   **text** at `voice.style_pick` in `data/intake.json` (use Edit/Write on that one field only).

3. **Extract the voice.** Run `uv run tb onboard`. This is the only AI step — it reads *how* they
   wrote (from `data/intake.json`) and writes `profiles/voice.json`. It invents nothing.

4. **The reveal — SHORT and warm.** Open with a genuine thanks. Read `profiles/voice.json` and
   tell them, in 2–3 plain lines, how you'll keep it sounding like them. Don't dump the profile.
   Then: *"It's always editable — tweak it anytime with `/timbre-voice` (or edit
   `profiles/voice.json`), and your edit is the confirmation."*

5. **Offer the first post:** *"Want to make your first post? Just say the word."* → `/timbre-post`.

## Fallback — no browser (terminal-only)

If `tb welcome` can't run (no `web` extra) or the user would rather stay in the terminal, ask the
**deterministic** questions from `engine/onboarding.json` **strictly one at a time, in order**
(skip any `enabled: false`), with a short progress note and a brief human acknowledgement between
answers. Substitute `{name}` once you have it. Store each answer at its `writes_to` path in
`data/intake.json` (start from `data/intake.example.json` for the shape); for `writing_samples`,
"skip" leaves it empty. Then do the `style_pick` (step 2), the extraction (step 3), and the
reveal (steps 4–5).

## Rules

- The web is **intake only** — it never calls a model. The AI steps (`style_pick`, `tb onboard`)
  are yours, in the terminal, key-free via the default provider.
- Never invent details about them. A blank stays blank.
- The questions come from `engine/onboarding.json`. To change them, edit that file — not this.
