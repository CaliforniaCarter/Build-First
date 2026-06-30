---
description: Capture your writing voice from a cold start (Timbre)
argument-hint: "[your LinkedIn/X handle or a post you're proud of]"
allowed-tools: Bash Read Write Edit
---

Onboard the user into Timbre — a warm, one-question-at-a-time conversation that learns their
voice. Context they gave: **$ARGUMENTS**

**The flow is data, not improv.** Read `engine/onboarding.json` first — it holds the welcome
line, the hardcoded audience default, and the exact questions (with their order, type, and
where each answer is stored). Ask those questions; never invent your own.

## How to run it

1. **Read `engine/onboarding.json`.** Print its `welcome` line, as written.

2. **Ask the `questions` STRICTLY one at a time, in `order`** (skip any with `enabled: false`) —
   print one question, wait for the answer, then the next. **Never batch them.** Above each
   question print a progress bar, e.g. `[▰▰▱▱▱▱▱] 2/7 · background`. Substitute `{name}` once you
   have it. **Before the three voice questions (weekend / lunch / teach), say a short
   transition:** *"Now I'll ask you 3 quick questions — just type or talk them out, however
   feels natural; it's the easiest way for me to hear how you actually sound."*
   - **`deterministic`** — ask the `prompt` verbatim.
   - **`adaptive_ab`** — the personalized this-or-that. Print the `prompt` to set it up, then
     follow the question's `generate` instruction: using their **resume + the answers so far**,
     write the TWO short example posts yourself (real facts only — invent nothing), show them as
     **A** and **B**, and ask which sounds more like them. **Never label the difference** (no
     "dry vs warm") — let them feel it. Store the chosen example's **text** at `writes_to`.

3. **Be human between questions.** One short, genuine reaction per answer — and at most one
   grounded micro-observation mid-flow ("you keep it short and dry — noted"). Never invent
   praise; never pad. The *full* voice reveal waits for the end.

4. **Store answers in `data/intake.json`** as you go (start from `data/intake.example.json` for
   the shape). Put each answer at the question's `writes_to` path (e.g. `voice.answers.weekend`).
   For the **`writing_samples`** question: if they paste posts/essays, put each into
   `voice.writing_samples` (weight these heavily) — or run `uv run tb sample --text "…"` per post;
   if they say **skip**, leave it empty — no problem. For **`background`**, pull any handle/URL
   into `online.linkedin` / `online.x` — **don't try to fetch a login-walled profile; pasting is
   the way.** (The audience is already set in `engine/onboarding.json` and feeds drafts
   automatically — you don't ask about it.)

5. **Extract the voice.** Run `uv run tb onboard --json`. This is the only AI step — it reads
   *how* they wrote and writes `profiles/voice.json`. It invents nothing.

6. **The reveal — keep it SHORT (2–3 lines).** Read `profiles/voice.json` and tell them, in
   plain language, how you'll match their energy and keep it authentically them. Don't dump the
   whole profile. Then: *"You can view or tweak your exact voice anytime with `/timbre-voice`
   (or by editing `profiles/voice.json`) — your edit is the confirmation."*

7. **Offer the first post:** "Want me to draft your first post?" → `/timbre-post`.

## Rules

- Don't make them fill a form — it's a conversation.
- Never invent details about them. A blank stays blank.
- The questions come from `engine/onboarding.json`. To change them, edit that file — not this.
