import pytest
from jwrag.chunker import TextChunker


@pytest.fixture
def chunker() -> TextChunker:
    return TextChunker(chunk_size=1024, overlap=200)


def test_chunker_handles_short_text(chunker: TextChunker) -> None:
    text = "Short text."
    chunks = chunker.chunk(text)
    assert len(chunks) == 1
    assert chunks[0] == text


def test_chunker_respects_separator_hierarchy(chunker: TextChunker) -> None:
    # Create a long text with paragraphs
    text = "\n\n".join(["Paragraph " + str(i) * 100 for i in range(20)])
    chunks = chunker.chunk(text)
    
    # Verify chunks are not empty and respect boundaries roughly
    assert len(chunks) > 1
    for chunk in chunks:
        assert len(chunk) <= chunker.chunk_size


def test_chunker_applies_overlap(chunker: TextChunker) -> None:
    long_text = "A" * 2000
    chunks = chunker.chunk(long_text)
    
    # Check that we have multiple chunks and they are not completely disjoint
    assert len(chunks) > 1
    for i in range(1, len(chunks)):
        prev_chunk = chunks[i-1]
        curr_chunk = chunks[i]
        # Overlap ensures some characters are shared or boundaries are close
        assert len(prev_chunk) + len(curr_chunk) > chunker.chunk_size


def test_chunker_creates_chunks_with_metadata(chunker: TextChunker) -> None:
    text = "Test content for chunking."
    test_meta = {"page_number": 1, "paragraph": 2, "filename": "test.txt"}
    chunks = chunker.create_chunks(text, "doc-1", test_meta)
    
    assert len(chunks) == 1
    assert chunks[0].document_id == "doc-1"
    assert chunks[0].chunk_index == 0
    assert chunks[0].metadata == test_meta
