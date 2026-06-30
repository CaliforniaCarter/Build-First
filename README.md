# Build First — Brand Voice Content Engine (Timbre)

Turns the work you actually do into on-brand LinkedIn posts, in your voice, from a cold start.
Drafts only — it never auto-posts.

## Run the app (web UI + engine)

```bash
# 1. backend — FastAPI over the engine, live Anthropic generation
uv pip install -e '.[api]'
echo 'ANTHROPIC_API_KEY=sk-...' > .env          # your key; powers the reveal + compose
uv run python -m uvicorn api.main:app --port 8000

# 2. frontend — Next.js (new terminal)
cd web && npm install && npm run dev            # http://localhost:3000
```

The web app calls `/api/*`, which Next proxies to the FastAPI backend (no CORS).
Everything is local-first: intake, persona, and posts stay on your machine under `data/`
and `profiles/`. Flow: marketing → onboarding (why → you → voice → reveal → done) → app
(home · write · posts · voice profile).

## Run the engine alone (CLI)

```bash
bf doctor      # validate data/intake.json
bf run         # onboard → ablation ladder → report
```
