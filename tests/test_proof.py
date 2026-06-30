"""The deterministic proof check: banned/slop phrases (universal proof.json + personal
voice.banned), grounding (numbers + code/path specifics must trace to the user's material),
and redaction. This is the anti-slop guarantee that doesn't trust the LLM to grade itself.
"""

from engine.blocks.intake import ContentIdea, Intake, Voice
from engine.blocks.proof import check_grounding, check_slop, check_text, load_proof_config


def _intake() -> Intake:
    return Intake(
        name="T",
        idea=ContentIdea(
            topic="shipped an eval harness",
            number="cut confidently-wrong from 14% to 2%",
            proof=["diff +212/-4 in evals/harness.py"],
        ),
        voice=Voice(banned=["unlock", "circle back"]),
    )


def test_proof_json_loads():
    cfg = load_proof_config()
    assert "delve" in cfg.slop_phrases  # the shipped slop list
    assert cfg.grounding_scope in ("numbers", "numbers_and_specifics")


def test_check_slop_catches_universal_and_personal():
    hits = check_slop("we leverage AI to unlock value", ["unlock", "circle back"])
    assert "leverage" in hits  # universal (engine/proof.json)
    assert "unlock" in hits  # personal (voice.banned)
    assert check_slop("a clean, honest sentence", []) == []


def test_grounding_flags_invented_number_but_passes_real_one():
    intake = _intake()
    assert check_grounding("dropped from 14% to 2%", intake) == []  # both real
    assert "40%" in check_grounding("accuracy jumped 40%", intake)  # invented


def test_grounding_flags_invented_code_specific():
    intake = _intake()
    assert check_grounding("see evals/harness.py", intake) == []  # real (in proof)
    assert "fake/module.py" in check_grounding("see fake/module.py", intake)  # invented


def test_grounding_ignores_bare_single_digits():
    intake = _intake()
    assert check_grounding("it took 3 tries that morning", intake) == []  # too noisy to flag


def test_check_text_redacts_and_flags():
    report = check_text("email me at a@b.com — we leverage synergy", _intake())
    assert "email" in report.redactions
    assert "leverage" in report.slop_hits
    assert not report.clean


def test_clean_post_passes():
    report = check_text("we cut confidently-wrong answers from 14% to 2%. here's how.", _intake())
    assert report.clean
    assert report.slop_hits == [] and report.ungrounded == []
