# Self-learning loop (scope)

## The idea
When you edit a post the engine drafted, that edit is a signal about your voice or who you
are. The loop reads the edit and updates your profile so the next draft is closer — you
never hand-tune the profile.

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
`bf learn --edited <your-edited-post>` (original defaults to the last saved post):
1. The engine shows the model the draft, your edited version, and your current voice/profile
   fields.
2. The model proposes conservative field updates: prefer **set** (replace), **add** only if
   genuinely new, return nothing if the edit is just content.
3. The engine applies them to `data/intake.json` and prints exactly what changed, so you can
   see it stayed tight.
4. The next `bf post` regenerates persona/profile from the richer source.

## Guards against clutter
- A whitelist of learnable fields — the loop can't touch anything else.
- Prefer-replace, add-only-if-new in the prompt; list adds are de-duplicated.
- Every change is shown; nothing is silent.

## Later (full V2)
- Learn from everything you ship, not just edits (what landed, what you saved).
- A visual, editable profile view — the UI renders the fields and edits write straight back.
