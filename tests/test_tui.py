import pytest
from jwrag.cli import TUIRenderer
from jwrag.models import SynthesisResult, SynthesisOption


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
    result = SynthesisResult(query="Q", options=[], references=["doc1.txt"])
    output = renderer.render_result(result)
    assert "doc1.txt" in output
