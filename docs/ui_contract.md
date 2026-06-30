# UI Contract — how a UI drives the engine

The engine is a local CLI (`tb`) over plain files. A UI drives it two ways:
1. **Read/write plain files** in the project (intake, persona, posts).
2. **Shell out** to `tb <command> --json` and parse stdout.

No server, no database, no account — everything is local files (V1 spec: local-first).
Every command accepts `--provider {terminal,anthropic,stub}`, `--intake <path>`, and
`--json`. Default provider `terminal` = Claude Code is the engine (no API key).

## The flow: cold start → first post

| Step | UI does | Engine command | Reads / writes |
| --- | --- | --- | --- |
| 1. Capture | Collect profile + voice + the idea, write `data/intake.json` | — | writes `data/intake.json` |
| 2. Onboard | — | `tb onboard` | writes `profiles/{profile,context,persona}.md` |
| 3. "That's me?" | Show persona, let the user edit + save | `tb persona --json` | reads/writes `profiles/persona.md` |
| 4. Gap probe | Ask each unfilled question, write answers into the idea | `tb gaps --json` | writes `data/intake.json` (`idea.<key>`) |
| 5. Make post | — | `tb post --json` | writes `posts/<slug>/`, clipboard |
| 6. Approve | Show final, let the user edit/approve | — | reads `posts/<slug>/final.md` |
| 7. Library | List past posts | `tb posts --json` | reads `posts/` |

Editing `persona.md` (step 3) **is** the confirmation — the engine never over-trusts its
own extraction. Step 4 never invents an answer; a blank stays blank on purpose.

## The conversation is the LLM's job, not the engine's

The engine returns structured data (the post + the eval). It does **not** print menus or
canned feedback. When the LLM (Claude Code / Cowork, or your UI's model) drives the engine, it:
- presents the post in its own voice;
- reads the structured eval (`evaluation.dimensions` + their reasons) and, if something is
  weak, says so in plain language — never the dimension names or the 0–10 scale;
- always offers an out: **use it as-is**, **edit it yourself**, or **let me help** (tell me
  what to change, or I'll ask a couple of sharpening questions drawn from the weak spots);
- if they want help, asks those questions, writes the answers back, and re-runs.

`tb labs` (Timbre Labs) is the one place the full eval scale is shown — it's for you, the
builder, not the end user.

## JSON shapes

`tb persona --json`
```json
{ "path": "profiles/persona.md", "persona_md": "# persona.md\n..." }
```

`tb gaps --json` — only the unfilled gaps are missing from the idea
```json
[ { "key": "number", "question": "What's one real number...", "filled": false } ]
```
Keys: `number`, `scene`, `lesson`, `only_you`. To answer, write the text into
`data/intake.json` at `idea.<key>`.

`tb post --json` returns TWO options (different shapes) for the user to pick:
```json
{
  "run_id": "2026-06-29",
  "options": [
    { "option": 0, "final": "For years I treated the internet...", "score": 9.1,
      "evaluation": { "dimensions": ["...all nine"], "gates": ["...all six"] }, "receipts": ["..."] },
    { "option": 1, "final": "...same facts, a different shape...", "score": 8.9,
      "evaluation": { "dimensions": ["..."], "gates": ["..."] }, "receipts": ["..."] }
  ]
}
```
The user picks one: `tb pick --run-id <id> --option <0|1>` polishes it (Writer's Council) and saves
it. `tb pick --json` (and `tb revise --json`) return the single saved post:
```json
{ "final": "...", "score": 9.2, "evaluation": { "dimensions": ["..."], "gates": ["..."] },
  "receipts": ["..."], "saved": "posts/my-simple-notion-second-brain", "draft": "runs/<id>/post/draft.md" }
```
`score` is the overall 0–10 meter only. The full `evaluation` is for the LLM and Timbre Labs — the
UI turns weak dimensions into plain guidance and never shows the user the scale.

`tb posts --json` — the saved library
```json
[ { "date": "2026-06-29", "topic": "...", "channels": ["LinkedIn","X"],
    "score": { "quality": 8.2, "gates_passed": 6, "gates_total": 6 },
    "open_gates": [], "receipts": ["..."] } ]
```

## `data/intake.json` (the input contract)

See `data/intake.example.json` for the full blank shape. The fields the engine reads:
- `name` — string.
- `idea` — `topic` (required), plus the gap fields `take`, `scene`, `number`, `lesson`,
  `only_you`, `mechanism`, `proof` (list), `close`.
- `online` — `linkedin`, `x`, `other`, `existing_posts`, `cold_start` (bool).
- `docs` — `resume`, `portfolio`.
- `typed` — `identity`, `known_for`, `background`, `beliefs`, `lessons`.
- `voice` — `answers` (question→raw answer map; the model reads *how* you write),
  `tone_words` (list), `look`, `sentence_length`, `banned` (list), `signatures` (list),
  `emojis`, `notes`.
- `audience` — `writing_for`, `goal`, `play_to`.
- `output` — `channels` (list), `length`, `format`, `hard_nevers` (list), `off_limits`.

A real `data/intake.json` is personal and gitignored; if absent the engine falls back to
the committed synthetic `data/intake.sample.json`.
