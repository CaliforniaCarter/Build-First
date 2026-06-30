# Storage (local-first)

Everything Timbre knows lives as plain files on your machine. No database, no cloud, no
account. The only thing that leaves the machine is the redacted text each LLM call needs.

## Layout

```
data/intake.json            your raw inputs (private, gitignored)
profiles/
  profile.md                who you are
  context.md                today's work
  persona.md                your voice (hand-confirmable; never silently overwritten)
posts/
  <date>-<slug>/            one folder per post, updated in place
    final.md                the post text
    post.json               metadata (below)
runs/<id>/                  disposable working files (prompts, drafts, completions)
```

## `post.json`

```json
{
  "slug": "2026-06-29-my-simple-notion-second-brain",
  "topic": "...",
  "channels": ["LinkedIn", "X"],
  "status": "draft",
  "score": { "quality": 9.2, "gates_passed": 6, "gates_total": 6 },
  "open_gates": [],
  "receipts": ["..."],
  "created": "2026-06-29",
  "updated": "2026-06-29"
}
```
`status` is `draft | posted`. One entry per post: re-running or editing updates the same
folder; `created` stays, `updated` moves, and `status` is preserved.

## How the UI reads/writes

- **List the library:** `tb posts --json` (or read `posts/*/post.json`).
- **A post's text:** `posts/<slug>/final.md`.
- **Mark posted / back to draft:** `tb publish <slug>` (`--draft` to revert), or set `status` in `post.json`.
- **Save the user's edited text:** write it to `final.md`, then trigger learning (below).

## Edits → profile, token-efficiently (design — building next)

When you edit a post, the profile learns from it, without burning tokens on every keystroke:
- Edits are stored as plain text (no AI), capped to the last few.
- The profile-update AI call runs **on demand over that small batch of diffs** (not per edit) and
  updates the profile **in place** (anti-bloat, via `engine/learn.py`). Most edits cost zero
  tokens; learning fires occasionally on a tiny input.

## Warm start (handles → existing posts)

`online.linkedin` / `online.x` set cold vs warm start. If the user has existing posts, those are
the best voice corpus — they go into `voice.writing_samples`, which the persona extraction weights
above the easy-question answers. Fetching them from a live profile is an agent/Cowork browser task
(it writes into `writing_samples`), not engine code — see the note in chat.
