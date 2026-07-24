import pytest
from pathlib import Path
import numpy as np
from jwrag.models import DocumentMetadata, Chunk, SynthesisOption, SynthesisResult, Reference


def test_document_metadata_is_frozen() -> None:
    doc = DocumentMetadata(
        id="1", 
        filepath=Path("/tmp/test.txt"), 
        filename="test.txt", 
        file_hash="abc", 
        last_modified=0.0
    )
    with pytest.raises(Exception):  # FrozenInstanceError
        doc.filepath = Path("/tmp/other.txt")


def test_chunk_is_frozen() -> None:
    chunk = Chunk(
        id="1", 
        document_id="doc-1", 
        chunk_index=0, 
        text_content="test", 
        embedding=np.array([0.0], dtype=np.float32), 
        metadata={}
    )
    with pytest.raises(Exception):
        chunk.text_content = "changed"


def test_synthesis_option_is_frozen() -> None:
    opt = SynthesisOption(title="A", reasoning="R", conclusions=["C"])
    with pytest.raises(Exception):
        opt.title = "B"


def test_reference_is_frozen() -> None:
    ref = Reference(filename="doc.pdf", page="1", paragraph="2")
    with pytest.raises(Exception):
        ref.filename = "other.pdf"


def test_synthesis_result_is_frozen() -> None:
    ref = Reference(filename="doc.pdf", page="1", paragraph="2")
    res = SynthesisResult(query="Q", options=[], references=[ref])
    with pytest.raises(Exception):
        res.query = "Q2"
