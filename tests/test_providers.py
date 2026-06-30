"""The provider seam: the factory resolves names, and the stub (every demo's spine) emits
schema-valid output for every stage the pipeline asks for."""

import tempfile
from pathlib import Path

import pytest

from engine.blocks.council import revise as council_revise
from engine.learn import parse_edits
from engine.providers import get_provider
from engine.providers.anthropic import AnthropicProvider
from engine.providers.stub import StubProvider
from engine.providers.terminal import TerminalProvider
from engine.rubric.shared import parse_score


def test_get_provider_factory():
    d = Path(tempfile.mkdtemp())
    assert isinstance(get_provider("terminal", d), TerminalProvider)
    assert isinstance(get_provider("anthropic", d), AnthropicProvider)
    assert isinstance(get_provider("stub", d), StubProvider)
    with pytest.raises(ValueError):
        get_provider("nope", d)


def test_stub_score_stages_validate():
    stub = StubProvider()
    for stage in ("score_L0", "score_L5", "score_post", "score_revise"):
        score = parse_score(stub.complete(stage, "prompt"))
        assert score.gates_total == 6
        assert len(score.dimensions) == 9


def test_stub_council_revise_stops_in_one_pass():
    final, log = council_revise("a draft", "persona", "layers", StubProvider())
    assert final
    assert len(log) == 1 and log[0]["stop"] is True


def test_stub_learn_and_text_stages():
    stub = StubProvider()
    assert parse_edits(stub.complete("learn", "p")) == []
    assert "Stub draft" in stub.complete("draft_post", "p")
    assert stub.complete("revise", "p")
