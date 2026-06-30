# UI Contract — how a UI drives the engine

The engine is a local CLI (`bf`) over plain files. A UI drives it two ways:
1. **Read/write plain files** in the project (intake, persona, posts).
2. **Shell out** to `bf <command> --json` and parse stdout.

No server, no database, no account — everything is local files (V1 spec: local-first).
Every command accepts `--provider {terminal,anthropic,stub}`, `--intake <path>`, and
`--json`. Default provider `terminal` = Claude Code is the engine (no API key).

## The flow: cold start → first post

| Step | UI does | Engine command | Reads / writes |
| --- | --- | --- | --- |
| 1. Capture | Collect profile + voice + the idea, write `data/intake.json` | — | writes `data/intake.json` |
| 2. Onboard | — | `bf onboard` | writes `profiles/{profile,context,persona}.md` |
| 3. "That's me?" | Show persona, let the user edit + save | `bf persona --json` | reads/writes `profiles/persona.md` |
| 4. Gap probe | Ask each unfilled question, write answers into the idea | `bf gaps --json` | writes `data/intake.json` (`idea.<key>`) |
| 5. Make post | — | `bf post --json` | writes `posts/<date>-<slug>/`, clipboard |
| 6. Approve | Show final, let the user edit/approve | — | reads `posts/<date>-<slug>/final.md` |
| 7. Library | List past posts | `bf posts --json` | reads `posts/` |

Editing `persona.md` (step 3) **is** the confirmation — the engine never over-trusts its
own extraction. Step 4 never invents an answer; a blank stays blank on purpose.

## JSON shapes

`bf persona --json`
```json
{ "path": "profiles/persona.md", "persona_md": "# persona.md\n..." }
```

`bf gaps --json` — only the unfilled gaps are missing from the idea
```json
[ { "key": "number", "question": "What's one real number...", "filled": false } ]
```
Keys: `number`, `scene`, `lesson`, `only_you`. To answer, write the text into
`data/intake.json` at `idea.<key>`.

`bf post --json`
```json
{
  "final": "I've quit every second brain...",
  "score": { "quality": 8.2, "gates_passed": 6, "gates_total": 6 },
  "open_gates": [],
  "receipts": ["about 80 entries logged in two weeks", "..."],
  "saved": "posts/2026-06-29-my-simple-notion-second-brain",
  "draft": "runs/<id>/post/draft.md"
}
```

`bf posts --json` — the saved library
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
