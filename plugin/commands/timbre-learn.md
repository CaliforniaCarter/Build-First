---
description: Fold this session's picks + edits into your voice (Timbre)
argument-hint: ""
allowed-tools: Bash Read Write Edit
---

Offer to fold the session's accumulated picks and edits into the user's voice — the
end-of-session learning consent. Picks and edits were logged for free as you went; this is the
one batched AI pass.

1. **Check for pending signals.** Run `uv run tb learn --check --json`. If `pending` is 0, say
   there's nothing to fold and stop.

2. **Ask first — consent.** If there are pending signals, ask plainly: *"Want me to fold your N
   picks/edits from this session into your voice? (one quick pass — updates
   `profiles/voice.json`)"* Only proceed on a **yes**. On no, leave them — they stay pending for
   next time.

3. **Fold on yes.** Run `uv run tb learn --provider anthropic --json` (drop `--provider
   anthropic` if there's no key). It updates `profiles/voice.json` **in place, conservatively**
   (replace a value, add only if genuinely new) — the voice never bloats or drifts, and your
   hand-edits, the voice signature, and your identity are all safe. Tell them what changed in one
   line (from `applied`), or that nothing voice-relevant came up. The next draft uses it.

Never fold without the user's yes.
