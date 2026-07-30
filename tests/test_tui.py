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
    ref2 = Reference(filename="doc2.pdf", markers={"chapter": "5", "clause": "2"})
    result = SynthesisResult(query="Q", options=[], references=[ref1, ref2])
    output = renderer.render_result(result)
    assert "- doc1.txt" in output
    assert "- doc2.pdf (Chapter: 5, Clause: 2)" in output
