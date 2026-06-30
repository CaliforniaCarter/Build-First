"""Gap-driven probe — ask only for what a strong post is missing.

A strong post needs a real number, a concrete scene, a non-obvious lesson, and an
only-you take (the same four the rubric's hard gates check). This finds which are
missing from the idea and returns one fixed question per gap. The engine never
invents the answer — you provide it, or you leave it blank on purpose.

Thin by design: fixed questions, not an adaptive interview. The UI asks them and
writes the answers back into the idea (intake.idea.<key>).
"""

from __future__ import annotations

from .intake import Intake

# The four gap dimensions, in ask-order, each with one fixed question.
GAP_QUESTIONS = {
    "number": "What's one real number in this story? How long, how many, how much — "
    "anything true. Leave it blank if there honestly isn't one.",
    "scene": "What's one concrete moment? Where you were, what happened. Show it, don't summarize.",
    "lesson": "What's the non-obvious takeaway here — something most people would miss?",
    "only_you": "What's the only-you angle — something only you could say about this?",
}


def find_gaps(intake: Intake) -> list[dict]:
    """Every gap dimension with its question and whether the idea already fills it."""
    idea = intake.idea
    values = {
        "number": idea.number,
        "scene": idea.scene,
        "lesson": idea.lesson,
        "only_you": idea.only_you,
    }
    return [
        {"key": k, "question": GAP_QUESTIONS[k], "filled": bool(values[k].strip())}
        for k in GAP_QUESTIONS
    ]


def unfilled_gaps(intake: Intake) -> list[dict]:
    """Just the gaps still missing — the questions to actually ask, one at a time."""
    return [g for g in find_gaps(intake) if not g["filled"]]
