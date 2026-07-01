# Timbre — Claude Code plugin

Make Claude Code your writing partner: it learns your voice and drafts on-brand LinkedIn/X
posts you approve. Two options every time, real receipts, never auto-posts, learns from every
pick.

## Install (local, for testing)

From the Timbre repo:

```bash
claude --plugin-dir ./plugin
```

Verify it loaded:

```
/plugin list      # look for "timbre"
```

## Use

Just talk to it — the `timbre` skill auto-invokes when you ask to write a post. Or use the
commands:

- `/timbre-onboard` — capture your voice from a cold start (opens a quick browser onboarding).
- `/timbre-post <what you want to post about>` — draft two options, pick one, learn from it.

## How it works

The plugin doesn't reimplement anything — it teaches Claude to drive the local `tb` engine and
own the conversation:

1. **Onboard** — a short chat (not a form) → `data/intake.json` → `tb onboard`. Your real
   writing (pasted into `voice.writing_samples`) is the best voice sample.
2. **Draft** — `tb post` returns **two** options in different shapes. Claude shows both and
   asks which feels more like you, and why.
3. **Pick** — `tb pick --option N --why "…"` polishes it (Writer's Council), saves it, copies
   it to your clipboard, and logs the choice.
4. **Learn** — `tb learn` folds your recent picks + edits into your voice profile, in place.
   Picks/edits are logged token-free; learning runs once over the small batch.

## Provider

Set `ANTHROPIC_API_KEY` (in `.env`) to draft against the API — that's the route that deploys
to anyone with their own key. With no key, the plugin uses `--provider terminal` and Claude
Code itself becomes the engine.

It **never auto-posts.** You are always the gate.
