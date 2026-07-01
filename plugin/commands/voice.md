---
description: View and edit your voice profile in plain words (Timbre)
argument-hint: "[optional: a change to make, e.g. 'shorter sentences']"
allowed-tools: Bash Read Write Edit
---

Show the user their voice profile — the thing every draft obeys — and let them change it in
plain words or by editing the file. Optional change they asked for: **$ARGUMENTS**

## How to run it

1. **Read the voice.** Run `uv run tb voice --json` (it returns the `voice` fields, a `rendered`
   prose version, and the `path`). If it says no profile yet, tell them to run `/timbre:onboard`
   first and stop.

2. **Show it cleanly** — a readable view, not a raw JSON dump. Map the fields to plain labels,
   skipping any that are empty:

   ```
   Here's your voice — what every draft obeys  ·  profiles/voice.json

     SIGNATURE    {signature}
     SOUNDS LIKE  {vocabulary} · {sentence_style}
     LOVES        {favorite_phrases}
     BANNED       {banned}
     HUMOR        {humor}
     STRUCTURE    {structure}
     NEVER        {never_do}
   ```

3. **Offer both ways to change it:**
   - **Plain words** — they say things like "shorter sentences", "never let me say 'circle
     back'", "I don't open with admissions". You map that to the right field in
     `profiles/voice.json` and edit the file (add to `banned`/`never_do`/`signatures`,
     rewrite `sentence_style`/`structure`/`humor`, etc.). Change ONLY what they asked —
     never invent or "improve" other fields.
   - **Direct file** — tell them they can open `profiles/voice.json` and edit it themselves;
     it's a plain file they own.
   - If they say "looks good" (or nothing to change), leave it as is.

4. **Save + confirm.** After an edit, run `uv run tb voice --json` again to confirm it still
   parses, then tell them in one line what changed (e.g. *"Added 'circle back' to your banned
   list."*). Note: **the next draft uses it immediately** — `voice.json` is the source of
   truth, and your edit is never overwritten unless you re-run `/timbre:onboard`.

## Rules

- Never invent traits or change fields they didn't ask about. Their words win.
- Keep the view readable; show the raw JSON only if they ask ("show me the file").
- If `$ARGUMENTS` already names a change, show the voice, apply that change, and confirm.
