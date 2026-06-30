# Talk track — Timbre (Build First, July 2)

A 6–7 minute live demo. The spine: **cold start → your voice in under 10 minutes → it learns.**
Beats and lines below; the bold lines are the ones to actually say.

---

## 0:00 — The problem (45s)
Everyone now sounds like AI. The feed is gray. And the people with the most worth saying —
builders, operators — post the least, because turning what you actually did into something
in *your* voice is slow and feels gross.

> **"I didn't want a tool that writes like AI. I wanted one that writes like me — from the
> work I actually do — and never posts without my say-so."**

That's Timbre.

## 0:45 — Cold start (60s)
Start with nothing. Onboarding isn't a form — it's a short conversation, and the strongest
input is *your own writing* (paste a post or an essay you're proud of). Run `tb onboard`.

Show `profiles/persona.md`. **"This is the voice it pulled from my writing. I didn't tune it —
I just corrected the one thing it got wrong. That edit is the confirmation."**

## 1:45 — Two options (90s)
`tb post`. It returns **two** drafts, in *different shapes* — not the same post twice.

> **"It never gives me one answer to rubber-stamp. It gives me a choice."**

Read both. Point at the weaker one in plain words ("this one's missing a real number"). Note:
you never see a score on screen — the eval is for the engine, not the user.

## 3:15 — The honesty beat (45s)
Earlier, the editor *fabricated* a detail — invented a named interview I never had. I killed
it at the source.

> **"It would rather hand me an honest 7 than a fake 9. If a stronger post needs a specific I
> don't have, it asks me — it doesn't make one up."**

For an AI strategist, that's the whole game: a system you can *trust* in front of customers.

## 4:00 — Pick, and it learns (90s)
Pick one — and say *why*. `tb pick --option 1 --why "I like opening on the admission, not the
how-to."`

It polishes the winner (a Writer's Council revises it to a bar), saves it, copies it to the
clipboard. Then `tb learn`.

> **"Watch this. It just folded my reason into my voice profile —"** show the diff: `voice.notes`
> now says *"opens on admissions, not how-tos."* **"Next draft leads that way. And picking cost
> zero tokens — learning fires once, over the batch."**

That's the loop: every choice makes the next draft more me.

## 5:30 — It runs anywhere (45s)
Two ways, same engine: a standalone CLI with your own key, or a **Claude Code plugin** where the
chat *is* the interface. Model-agnostic. Local-first — your data never
leaves your machine. No "log in with Anthropic" — that's against their terms, so it's
bring-your-own-key by design.

## 6:15 — The builder's bench + close (45s)
Quick flash of `tb labs`: an ablation harness that proves what each input is actually worth —
the kind of eval discipline I'd bring to your team.

> **"Timbre is small on purpose. But it's the thing I'd build at Tenex on day one: a system
> with a real eval, a learning loop, and the judgment to say 'I don't know' instead of making
> it up. I built it in a week. Imagine a quarter."**

---

## If asked: "what's the AI-strategist substance here?"
- **Evals as a product surface** — 6 hard gates + 9 scored dimensions, LLM-as-judge, plus an
  ablation bench (`tb labs`) that isolates the contribution of each input.
- **Prompt design for judgment** — terse prompts that hand the model the call; deterministic
  scaffolding only where it earns its keep (the rubric, the file contract).
- **A learning loop that respects cost** — signals logged token-free, one batched update,
  anti-bloat so the profile stays tight.
- **Knowing the constraints** — OAuth ruled out on ToS grounds; model-agnostic; local-first.

## Numbers to have ready
- Cold start → first saved post: target **under 10 minutes**.
- Draft quality without fabrication: honest **7.4–7.8** polished; the human gate takes it to 9.
- Picks/edits: **0 tokens** to capture; one small call to learn.
