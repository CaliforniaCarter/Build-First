# Self-learning loop

## The idea
Two things tell the engine about your voice: which of the two options you **pick** (and why),
and how you **edit** a draft. Both are signals. The loop folds them into your profile so the
next draft is closer — you never hand-tune the profile.

## Token-free capture, batched learning
Every pick and edit is logged to `data/signals.json` with **no AI call** — so most
interactions cost zero tokens. `tb pick` records the opening you chose, the one you rejected,
and your optional `--why`. Learning fires only when you run `tb learn`: it reads the pending
batch and makes **one** call over all of it, then marks them processed. Picks are free;
learning is occasional and runs over a tiny input.

## The hard rule: no bloat
The profile stays tight. The loop updates **in place** (find-and-replace on existing fields)
and only **adds** a line when it's genuinely new information not already covered. Routine
edits refine existing fields; they never grow the file. If an edit reveals nothing about
voice or identity (just a content tweak), the loop does nothing.

## What it updates: the source, not the generated files
`persona.md` and `profile.md` are regenerated from `data/intake.json` on every run, so the
loop updates the **source** (`data/intake.json`) — that's what persists. Only the persistent
fields:
- **Voice** — `look`, `sentence_length`, `emojis`, `notes` (replace); `tone_words`, `banned`,
  `signatures` (add-if-new).
- **Profile** — `typed.identity`, `known_for`, `background`, `beliefs`, `lessons` (replace).
- Per-post fields (the idea) are never touched — they aren't "you."

## How it runs
- `tb pick --option <0|1> [--why "..."]` — saves the post and logs the choice (no AI).
- `tb learn` — folds the pending batch (picks + edits) into `data/intake.json`. Add an edit to
  the batch with `tb learn --edited <your-edited-post>` (original defaults to the last saved post).

When `tb learn` runs:
1. The engine shows the model the batch of signals and your current voice/profile fields.
2. The model proposes conservative updates: prefer **set** (replace), **add** only if genuinely
   new, return nothing if the batch reveals nothing about voice or identity.
3. The engine applies them to `data/intake.json` and prints exactly what changed, so you can
   see it stayed tight.
4. Run `tb onboard` to refresh persona/profile from the updated source (a hand-edited
   `persona.md` otherwise stays put — `tb post` never clobbers it).

A real run: a pick ("open on the admission, not the how-to") taught `voice.notes` *"Opens on
admissions or failures, not how-tos"* and added the tone word *"self-aware"*; an edit that
cut an emoji added it to `voice.banned`.

## Guards against clutter
- A whitelist of learnable fields — the loop can't touch anything else.
- Prefer-replace, add-only-if-new in the prompt; list adds are de-duplicated.
- Every change is shown; nothing is silent.

## Later (full V2)
- Weight signals by outcome — what actually landed once you've posted it.
- A visual, editable profile view — the UI renders the fields and edits write straight back.
