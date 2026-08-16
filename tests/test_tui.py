import pytest
from jwrag.cli import TUIRenderer
from jwrag.models import SynthesisResult, SynthesisOption, Reference


def test_render_query() -> None:
    renderer = TUIRenderer()
    output = renderer.render_query("Test query?")
    assert "Test query?" in output


def test_render_options() -> None:
    renderer = TUIRenderer()
    opt = SynthesisOption(title="A", reasoning="R", conclusions=["C"])
    result = SynthesisResult(query="Q", options=[opt], references=[])
    output = renderer.render_result(result)
    assert "A" in output
    assert "R" in output


def test_render_references() -> None:
    renderer = TUIRenderer()
    ref1 = Reference(filename="doc1.txt")
    ref2 = Reference(filename="doc2.pdf", markers={"chapter": "5", "section": "2", "page": "14", "paragraph": "3"})
    result = SynthesisResult(query="Q", options=[], references=[ref1, ref2])
    output = renderer.render_result(result)
    assert "- doc1.txt" in output
    assert "- doc2.pdf (Ch. 5, § 2, p. 14, ¶ 3)" in output


def test_render_references_diacritics_variations() -> None:
    renderer = TUIRenderer()
    ref = Reference(filename="policy.pdf", markers={"page": "iv", "paragraph": "2", "clause": "7"})
    result = SynthesisResult(query="Q", options=[], references=[ref])
    output = renderer.render_result(result)
    assert "- policy.pdf (§ 7, p. iv, ¶ 2)" in output
