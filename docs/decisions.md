# Architecture decisions

Short ADRs — the trade-offs behind the build (the part Build First reviewers grade).

## 1. Plain Python orchestration, not LangChain/LangGraph (V1)

**Decision.** The pipeline is a deterministic `for` loop over small block functions
(`engine/ablation.py`), with one bounded Reflexion loop in the council. No graph engine.

**Why.**
- Matches Tenex's "an agent is a while loop" minimalism: debuggable, no framework lock-in,
  nothing to learn to read the repo.
- Error compounds across steps (95%/step over 10 steps ≈ 60%). Short, bounded steps with plain
  control flow are the easiest thing to reason about and verify.
- Our shape is a linear pipeline + one capped revision loop. That doesn't need a graph.
- We already get the main thing people reach to a graph for — **resumability** — for free: the
  terminal provider persists every prompt/completion to disk, so a run resumes by re-running.

**When to revisit (the trigger).** Adopt LangGraph in V2 only when durable, resumable,
*cross-session* state earns it: the continuous watcher (screen/Slack capture), parallel
multi-idea processing, or human-in-the-loop interrupts that span sessions.

**The spike, when triggered.** Wrap the 7 blocks as nodes; a linear graph + a council subgraph
with a conditional edge on the Reflexion stop; a SQLite checkpointer for durable state. Compare
LOC, debuggability, and latency against the plain loop. Keep it on a branch until it clearly wins.

## 2. No API key — a provider seam (V1)

**Decision.** Every reasoning step goes through `Provider.complete(stage, prompt)`. The default
`TerminalProvider` routes to the agent driving the terminal (no key); a dormant `AnthropicProvider`
is the drop-in for a later automated re-eval.

**Why.** Runs with zero setup and zero egress (local-first), keeps every prompt/completion as an
audit trail, and leaves a clean seam so an API re-score is a one-flag change.

## 3. The eval is the moat (V1)

**Decision.** An ablation ladder (one input tier at a time) + a shared rubric (6 hard gates,
9 scored dimensions) + a bounded (up to 3-pass) Reflexion Writer's Council, calibrated to one human.

**Why.** Per Tenex's 5-stage framework, when agents can build anything the eval set is the moat.
The ladder *is* the demo: each input visibly earns its score. Scores are calibration-pending by
design — Carter corrects them and the rubric learns.
