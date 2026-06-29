# Build First — Brand Voice Content Engine

Turns the work you actually do into on-brand LinkedIn posts, in your voice, from a cold start.
Drafts only — it never auto-posts.

## Runs with no API key
A deterministic Python spine; each step that needs judgment goes through a **provider seam** to the
model driving the terminal. Every prompt + completion is saved under `runs/`. A dormant
`AnthropicProvider` re-runs the same evals with a key later.

## Quickstart
```bash
uv sync --no-install-project
uv run python -m engine run        # onboard -> ablation -> report
```

## Pipeline
`intake → profile + context → persona → draft (voice/format/audience) → receipts → council → human gate`

## The eval (ablation ladder)
Hold the idea constant, add one input tier at a time — online → +docs → +typed → +persona →
+specifics → +eval pass — drafting and scoring at each step against a shared rubric (hard gates +
0–10 dims). The Writer's Council revises to a 9/10 target with a Reflexion stop rule.

Local-first: `profiles/` and `runs/` are gitignored and never leave the machine.
See `engine/` for the blocks; `tests/` for the checks.
