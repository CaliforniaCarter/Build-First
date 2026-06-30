---
description: Draft two on-brand post options to pick from (Timbre)
argument-hint: "[what you want to post about]"
allowed-tools: Bash Read Write Edit
---

Draft a post with Timbre about: **$ARGUMENTS**

Follow the `timbre` skill flow:
1. If `data/intake.json`/`profiles/persona.md` are missing, onboard first (have the short
   conversation, don't dump a form).
2. Write the topic into `data/intake.json` at `idea.topic` if it isn't already there, and run
   `uv run tb gaps --json` — ask the user any gap questions in plain words; never invent answers.
3. Run `uv run tb post --provider anthropic --json` and present **both** options in full.
   Read each `evaluation` privately; surface weak spots as plain guidance, never as scores.
4. Ask which one feels more like them, and why.
5. Run `uv run tb pick --option <0|1> --why "<reason>" --provider anthropic --json`, show the
   final, and offer use-as-is / edit / let-me-help.
6. Run `uv run tb learn --json` to fold the choice into their voice.

Never auto-post. The human is the gate.
