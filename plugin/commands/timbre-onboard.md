---
description: Capture your writing voice from a cold start (Timbre)
argument-hint: "[your LinkedIn/X handle or a post you're proud of]"
allowed-tools: Bash Read Write Edit
---

Onboard the user into Timbre. Context they gave: **$ARGUMENTS**

Follow the `timbre` skill's onboarding step:
1. Have a short conversation — who they are, who they write for, and their real writing. If
   they gave a handle, offer to paste in a few of their existing posts (their own writing is
   the strongest voice sample); put that text into `voice.writing_samples` in
   `data/intake.json`. See `data/intake.example.json` for the shape.
2. Run `uv run tb onboard --json`.
3. Run `uv run tb persona --json` and show the extracted voice. Ask "does this sound like
   you?" and let them edit `profiles/persona.md` — that edit is the confirmation.
4. Offer to draft their first post with `/timbre-post`.

Don't make them fill a form. Never invent details about them.
