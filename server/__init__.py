"""Timbre web intake — a local, no-key browser onboarding.

This package is PURE INTAKE: it serves a small branded page and writes the user's
answers into `data/intake.json` at the exact `writes_to` paths from
`engine/onboarding.json`. It makes **no model calls** and needs **no API key**.

Everything that needs a model (the personalized this-or-that + voice extraction +
the reveal) stays in the terminal, where Claude Code is the model for free. The web
hides the noisy intake step behind a clean UI; the terminal finishes the job.
"""
