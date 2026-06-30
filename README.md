# Timbre

Drafts on-brand LinkedIn/X posts **in your voice**, from a cold start. Two options every
time, real receipts attached, and it **never auto-posts** — you're always the gate. Every pick
and edit teaches it your voice.

```bash
uv pip install -e '.[api]'        # or skip [api] and use --provider terminal (no key)
uv run tb onboard                 # capture your voice
uv run tb post --provider anthropic   # → two options, in different shapes
uv run tb pick --option 0 --why "punchier opening"   # polish + save the one you like
uv run tb learn                   # fold your pick into your voice profile
```

## What makes it different

- **Your voice, not a template.** Onboarding extracts a voice profile from your real writing;
  you confirm it by editing it. Drafts vary their shape — no two posts follow the same mold.
- **Two options, then you pick.** Every `tb post` returns two drafts in different shapes. The
  choice you make (and *why*) is itself a signal — it teaches the profile.
- **It won't make things up.** The draft and the editor use only your real material. If a
  stronger post needs a specific you don't have, it asks — it never invents a number, a name,
  or a story. It would rather hand you an honest 7 than a fake 9.
- **It learns, token-free.** Picks and edits are logged with no AI call; `tb learn` folds the
  whole batch into your profile at once, in place, without bloat.
- **Local-first.** Everything lives as plain files on your machine (`data/`, `profiles/`,
  `posts/`). The only thing that leaves is the redacted text each model call needs.

## How it works

`intake → voice profile → draft (×2 shapes) → Writer's Council (revise to a bar) → receipts →
eval (6 gates + 9 dimensions) → you pick → it learns`. The engine returns structured data; the
interface (Claude Code, the web UI, or your own) presents it and owns the conversation.

## Run it three ways

Standalone CLI + your own key · a **Claude Code plugin** (`plugin/`) · or the **web UI**. See
[`docs/deploy.md`](docs/deploy.md).

## Docs

- [`docs/deploy.md`](docs/deploy.md) — the three deploy routes.
- [`docs/ui_contract.md`](docs/ui_contract.md) — how a UI drives the engine (commands ↔ JSON).
- [`docs/self_learning.md`](docs/self_learning.md) — the picks + edits learning loop.
- [`docs/storage.md`](docs/storage.md) — the local file layout.
- [`docs/talk_track.md`](docs/talk_track.md) — the demo narrative.

`tb labs` is the builder's bench — an ablation harness that shows what each input is worth.
Drafts only. You decide what ships.
