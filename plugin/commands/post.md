---
description: Turn real work into two post options, pick one, polish it (Timbre)
argument-hint: "[what you did — or a commit/file/notes to read]"
allowed-tools: Bash Read Write Edit
---

Draft a post from the user's real work: **$ARGUMENTS**

Follow the `timbre` skill flow. Never invent facts; never auto-post — the human is the gate.

1. **Onboard first if needed.** If `data/intake.json` or `profiles/voice.json` is missing, run
   the `/timbre:onboard` conversation first.

2. **Capture the work — two ways.** Either is fine:
   - **They describe it** in plain words, or
   - **They point you at a real artifact** — a commit (`git show <sha>`), a file, a PR, notes.
     Read it and pull out what actually happened.

   Write `idea.topic` into `data/intake.json`, and put the **real receipts** you found into
   `idea.proof` — concrete, verifiable things only (a commit SHA + diff stat, a file path, a
   real metric, a dated event). If you didn't see a receipt, don't write one.

3. **Probe the gaps (never invent).** Run `uv run tb gaps --json`. For each gap (a real number,
   the scene, the lesson, the only-you angle), ask the user in plain words and write the answer
   into `idea.<key>`. A blank stays blank — the post is honestly weaker, not faked.

4. **Draft two options.** Run `uv run tb post --provider anthropic --json` (drop `--provider
   anthropic` if there's no key — you become the engine). Present them as **two stacked, labeled
   blocks**, each with its receipts and its proof check:

   ```
   ▌ POST 1
   <the full draft, in their voice>
   receipts: <the proof items for this option>
   proof check: ✓ clean — no slop, every number traces to their material

   ▌ POST 2   (same facts, a different shape)
   <the full draft>
   receipts: <the proof items>
   proof check: ✓ clean
   ```

   The `proof_check` field is a **deterministic code check** (against `engine/proof.json` + the
   user's `voice.json` banned list), not the model's opinion. If it reports `slop_hits` or
   `ungrounded` for an option, **surface it plainly under that block** and ask the user to give
   the real number, cut it, or override — never ship a fabricated figure or a banned phrase:

   ```
   proof check: ⚠ "40%" isn't in anything you gave me — real number, or cut it?
   ```

   Read each option's `evaluation` **privately**. If one is weak, say so in plain words ("the
   second's missing a concrete number") — never show the 0–10 scores or the dimension names.

5. **They pick.** Ask: **"which feels more like you — 1 or 2? (and why — optional)"** Then run
   `uv run tb pick --option <0|1> --why "<their reason>" --provider anthropic --json`. This
   polishes the chosen one (Writer's Council), saves it, copies it to the clipboard, and
   **logs the choice as a token-free signal** — so every pick teaches the voice, with no AI
   call. Show the final **with its receipts and `proof_check`** (✓ clean, or the same
   flag-and-ask if something slipped in), then offer three outs: **use it as-is**, **edit it
   yourself**, or **let me help**. If they edit, save their version to the post's `final.md`.

6. **Don't fold the voice yet.** Picks and edits accumulate as free signals; the fold into the
   voice profile is **batched to the end of the session** and only on the user's yes (see the
   learning loop) — so the voice never gets over-updated. Do **not** run `tb learn` here.
