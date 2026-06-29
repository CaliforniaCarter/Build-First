# Build First — Brand Voice Content Engine

Turns the work you actually do into on-brand LinkedIn posts, in your voice, from a cold start.
Drafts only — it never auto-posts.

## Run it on your laptop (`Content`)

A local web app that onboards you and writes posts in the browser, running on your **Claude
subscription via OAuth — no API key**.

```sh
claude login        # one-time: logs Claude Code into your Pro/Max plan
uv sync
uv run Content       # boots a localhost app and opens your browser
```

It checks you're logged in, starts on `127.0.0.1`, and opens the onboarding page. Save your
profile, then write posts and watch each draft build live. Everything is stored as plain files
on your machine (`data/`, `profiles/`, `runs/`) — set `CONTENT_HOME` to put them elsewhere.

How the model runs: every reasoning step goes through one seam (`Provider.complete`). The web
app uses `ClaudeCodeProvider`, which shells out to your logged-in `claude` CLI in headless mode
(`claude -p`) — your subscription, no key. The original CLI is still here:

```sh
uv run bf run --provider claudecode   # the eval ladder + report, on your subscription
uv run bf doctor --provider claudecode   # check Claude login status
```

## Note

This is built to drive **your own** logged-in Claude Code on **your own** machine. Offering it
for other people to run on *their* subscriptions, or hosting it multi-tenant, needs Anthropic's
approval. The app binds to localhost only and never publishes — you paste the draft yourself.

See `docs/decisions.md` for the architecture decisions.
