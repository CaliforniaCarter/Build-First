# Deploy — getting Timbre to other people

Timbre is local-first: every install keeps its own `data/` and `profiles/` on the user's
machine. Nothing leaves except the redacted text each LLM call needs. There are three ways to
run it; they share the same engine.

## Route 1 — Standalone CLI + your own API key

The simplest "deployable to anyone" path. Each user brings their own Anthropic key.

```bash
git clone <repo> && cd <repo>
uv pip install -e '.[api]'          # installs the `tb` command + the anthropic SDK
cp .env.example .env                # then put ANTHROPIC_API_KEY=... in it
cp data/intake.example.json data/intake.json   # or let onboarding write it
uv run tb onboard
uv run tb post --provider anthropic            # two options
uv run tb pick --option 0 --why "punchier"     # polish + save the one you like
uv run tb learn                                 # fold your pick into your voice
```

- **Model-agnostic:** set `BF_MODEL` to any Claude model id (defaults to a current one).
- **No key?** Drop `--provider anthropic` to use `terminal` — whatever agent is running the
  command (Claude Code/Cowork) becomes the engine, no key required.

## Route 2 — Claude Code plugin (recommended)

The conversational version: Claude Code becomes the interface and does the onboarding as a
chat, not a form. See `plugin/README.md`.

```bash
claude --plugin-dir ./plugin
/timbre-onboard            # capture your voice
/timbre-post <topic>       # two options → pick → it learns
```

The plugin ships a skill (`timbre`) that auto-invokes when you ask to write a post, plus
`/timbre-post` and `/timbre-onboard` commands. It drives the same `tb` engine — no
duplication. This is the same mechanism a Cowork skill would use.

## Route 3 — Web UI (full onboarding + dashboard)

A Next.js app over a thin FastAPI wrapper of the engine (imported in-process). Onboarding flow,
a content dashboard (past posts, your voice profile, drafts), and the two-option pick.

```bash
# 1. backend — FastAPI over the engine (live generation needs ANTHROPIC_API_KEY in .env)
uv pip install -e '.[api]'
uv run python -m uvicorn api.main:app --port 8000

# 2. frontend — Next.js, in a second terminal
cd web && npm install && npm run dev        # http://localhost:3000
```

The web app calls `/api/*`, which Next proxies to the FastAPI backend (no CORS). Everything is
local-first: intake, persona, and posts stay under `data/` and `profiles/`. The two-option
flow and learning loop are wired through `/api/compose/options`, `/api/compose/pick`, and
`/api/learn`; see `docs/ui_contract.md` for the full command ↔ endpoint mapping.

## Not built on purpose: OAuth

The V1 spec rules out an OAuth "log in with Anthropic" flow — it's against Anthropic's API
terms for this kind of redistribution. The deployable routes are **bring-your-own-key** (Route
1/3) or **run-it-in-your-own-agent** (Route 2's `terminal` provider). That's a deliberate
constraint, not a gap.

## On the table: MCP server

Because the engine is a clean set of functions over local files, the natural next packaging is
an MCP server exposing `onboard / post / pick / learn / posts` as tools — that makes Timbre
usable from any MCP client (Claude Desktop, Cowork) and fully model-agnostic. The plugin can
bundle it via `.mcp.json`. Scoped, not yet built, so it isn't claimed as working.
