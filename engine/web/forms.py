"""The single bridge between the onboarding HTML form and the pydantic `Intake`.

The pydantic models in `blocks/intake.py` stay the source of truth — this only reshapes a flat
form into the nested dict they validate, and back again for edit-mode pre-fill.
"""

from __future__ import annotations

from typing import Mapping

from ..blocks.intake import Intake

# The fixed voice questions. How someone answers these (not what they say) is what
# `build_persona_prompt` reads to extract their voice — so these feed persona.md directly.
VOICE_QUESTIONS = [
    "What did you actually do at work this week? Just tell it like you'd tell a friend.",
    "What's something you believe about your field that others would push back on?",
    "Describe a time something you built broke or flopped. What happened?",
    "What do people get wrong about what you do?",
    "What's a small win recently that you were quietly proud of?",
]


def _csv(value: str) -> list[str]:
    return [s.strip() for s in (value or "").split(",") if s.strip()]


def _lines(value: str) -> list[str]:
    return [s.strip() for s in (value or "").splitlines() if s.strip()]


def intake_from_form(form: Mapping[str, str]) -> Intake:
    g = form.get
    answers = {
        q: g(f"voice_a__{i}", "")
        for i, q in enumerate(VOICE_QUESTIONS)
        if (g(f"voice_a__{i}", "") or "").strip()
    }
    return Intake.model_validate(
        {
            "name": g("name", ""),
            "idea": {
                **{
                    k: g(f"idea__{k}", "")
                    for k in (
                        "topic",
                        "take",
                        "scene",
                        "number",
                        "lesson",
                        "only_you",
                        "mechanism",
                        "close",
                    )
                },
                "proof": _lines(g("idea__proof", "")),
            },
            "online": {
                "linkedin": g("online__linkedin", ""),
                "x": g("online__x", ""),
                "other": g("online__other", ""),
                "existing_posts": g("online__existing_posts", ""),
                "cold_start": g("online__cold_start", "on") == "on",
            },
            "docs": {"resume": g("docs__resume", ""), "portfolio": g("docs__portfolio", "")},
            "typed": {
                k: g(f"typed__{k}", "")
                for k in ("identity", "known_for", "background", "beliefs", "lessons")
            },
            "voice": {
                "answers": answers,
                "tone_words": _csv(g("voice__tone_words", "")),
                "look": g("voice__look", ""),
                "sentence_length": g("voice__sentence_length", ""),
                "banned": _csv(g("voice__banned", "")),
                "signatures": _csv(g("voice__signatures", "")),
                "emojis": g("voice__emojis", ""),
                "notes": g("voice__notes", ""),
            },
            "audience": {k: g(f"audience__{k}", "") for k in ("writing_for", "goal", "play_to")},
            "output": {
                "channels": _csv(g("output__channels", "")) or ["LinkedIn"],
                "length": g("output__length", ""),
                "format": g("output__format", ""),
                "hard_nevers": _lines(g("output__hard_nevers", "")),
                "off_limits": g("output__off_limits", ""),
            },
        }
    )


def form_from_intake(intake: Intake) -> dict:
    """Flat dict for pre-filling the form in edit mode (inverse of intake_from_form)."""
    i, o, d, t, v, a, out = (
        intake.idea,
        intake.online,
        intake.docs,
        intake.typed,
        intake.voice,
        intake.audience,
        intake.output,
    )
    return {
        "name": intake.name,
        "idea__topic": i.topic,
        "idea__take": i.take,
        "idea__scene": i.scene,
        "idea__number": i.number,
        "idea__lesson": i.lesson,
        "idea__only_you": i.only_you,
        "idea__mechanism": i.mechanism,
        "idea__close": i.close,
        "idea__proof": "\n".join(i.proof),
        "online__linkedin": o.linkedin,
        "online__x": o.x,
        "online__other": o.other,
        "online__existing_posts": o.existing_posts,
        "online__cold_start": o.cold_start,
        "docs__resume": d.resume,
        "docs__portfolio": d.portfolio,
        "typed__identity": t.identity,
        "typed__known_for": t.known_for,
        "typed__background": t.background,
        "typed__beliefs": t.beliefs,
        "typed__lessons": t.lessons,
        "voice__answers": {q: v.answers.get(q, "") for q in VOICE_QUESTIONS},
        "voice__tone_words": ", ".join(v.tone_words),
        "voice__look": v.look,
        "voice__sentence_length": v.sentence_length,
        "voice__banned": ", ".join(v.banned),
        "voice__signatures": ", ".join(v.signatures),
        "voice__emojis": v.emojis,
        "voice__notes": v.notes,
        "audience__writing_for": a.writing_for,
        "audience__goal": a.goal,
        "audience__play_to": a.play_to,
        "output__channels": ", ".join(out.channels),
        "output__length": out.length,
        "output__format": out.format,
        "output__hard_nevers": "\n".join(out.hard_nevers),
        "output__off_limits": out.off_limits,
    }
