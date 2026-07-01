---
description: Clear all your local Timbre data for a fresh cold start (demo reset)
argument-hint: ""
allowed-tools: Bash
---

Reset Timbre to a cold start so the user can run onboarding fresh — handy for demos.

1. **Confirm first.** Ask: *"This clears your voice, profile, answers, posts, and signals so we
   start from zero — go ahead?"* Only proceed on a yes.
2. **Run `tb reset`.** It deletes `profiles/voice.json` + the profile docs,
   `data/intake.json`, `data/signals.json`, and everything under `posts/` and `runs/`. The
   editable configs (`onboarding.json`, `proof.json`, `rubric.json`, `labs.json`) and the
   synthetic sample are kept.
3. Tell them it's a clean slate and offer to run `/timbre:onboard` to start over.
