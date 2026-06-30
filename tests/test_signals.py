"""Learning signals are logged token-free, then folded in one batch — picks and edits alike."""

from engine import signals
from engine.blocks.persona import VoiceProfile
from engine.learn import build_learn_prompt, learn
from engine.providers.stub import StubProvider


def _voice() -> VoiceProfile:
    return VoiceProfile(signature="dry", punctuation="emojis sparingly")


def test_record_pending_and_mark_processed(tmp_path):
    path = tmp_path / "signals.json"
    assert signals.pending_signals(path) == []
    signals.record_signal("pick", {"chosen_opening": "A", "why": "punchier"}, path)
    signals.record_signal("edit", {"original": "o", "edited": "e"}, path)
    pend = signals.pending_signals(path)
    assert [s["kind"] for s in pend] == ["pick", "edit"]
    signals.mark_processed(path)
    assert signals.pending_signals(path) == []  # nothing re-processed next time


def test_cap_keeps_only_recent(tmp_path):
    path = tmp_path / "signals.json"
    for i in range(signals.CAP + 5):
        signals.record_signal("pick", {"chosen_opening": str(i)}, path)
    import json

    assert len(json.loads(path.read_text())) == signals.CAP


def test_batch_prompt_includes_picks_and_edits():
    prompt = build_learn_prompt(
        [{"kind": "pick", "chosen_opening": "A", "why": "punchier"}], _voice()
    )
    assert "punchier" in prompt and "SIGNALS" in prompt


def test_empty_batch_is_a_noop():
    applied, skipped = learn([], _voice(), StubProvider())
    assert applied == [] and skipped == []
