"""The human gate writes a reviewable draft; the engine never posts on its own."""

from engine.blocks.gate import human_gate


def test_human_gate_writes_final_draft(tmp_path):
    out = human_gate("the final post", tmp_path)
    assert out == tmp_path / "draft.md"
    assert out.read_text(encoding="utf-8") == "the final post"
