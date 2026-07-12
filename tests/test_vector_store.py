import pytest
import numpy as np
from pathlib import Path
from jwrag.models import DocumentMetadata, Chunk
from jwrag.vector_store import SQLiteVectorStore


@pytest.fixture
def db_path(temp_dir: Path) -> Path:
    return temp_dir / "test_jwrag.db"


@pytest.fixture
def store(db_path: Path) -> SQLiteVectorStore:
    s = SQLiteVectorStore(db_path)
    s.initialize()
    return s


def test_initialize_creates_tables(store: SQLiteVectorStore, db_path: Path) -> None:
    assert db_path.exists()


def test_upsert_and_retrieve_document(store: SQLiteVectorStore, temp_dir: Path) -> None:
    doc = DocumentMetadata(
        id="doc-1",
        filepath=temp_dir / "test.txt",
        filename="test.txt",
        file_hash="abc123",
        last_modified=1234567890.0
    )
    chunk = Chunk(
        id="chunk-1",
        document_id="doc-1",
        chunk_index=0,
        text_content="Hello world",
        embedding=np.array([0.1, 0.2, 0.3], dtype=np.float32),
        metadata={"page": 1}
    )
    store.upsert_document(doc, [chunk])
    
    retrieved = store.get_document_by_path(temp_dir / "test.txt")
    assert retrieved is not None
    assert retrieved.id == "doc-1"


def test_search_similar_chunks(store: SQLiteVectorStore) -> None:
    doc = DocumentMetadata(
        id="doc-1",
        filepath=Path("/tmp/test.txt"),
        filename="test.txt",
        file_hash="abc123",
        last_modified=1234567890.0
    )
    vec1 = np.array([1.0, 0.0, 0.0], dtype=np.float32)
    vec2 = np.array([0.0, 1.0, 0.0], dtype=np.float32)
    
    chunk1 = Chunk(id="c1", document_id="doc-1", chunk_index=0, text_content="A", embedding=vec1, metadata={})
    chunk2 = Chunk(id="c2", document_id="doc-1", chunk_index=1, text_content="B", embedding=vec2, metadata={})
    
    store.upsert_document(doc, [chunk1, chunk2])
    
    query_vec = np.array([0.9, 0.1, 0.0], dtype=np.float32)
    results = store.search_similar_chunks(query_vec, top_k=2)
    
    assert len(results) == 2
    assert results[0].text_content == "A"


def test_delete_document(store: SQLiteVectorStore, temp_dir: Path) -> None:
    doc = DocumentMetadata(
        id="doc-1",
        filepath=temp_dir / "test.txt",
        filename="test.txt",
        file_hash="abc123",
        last_modified=1234567890.0
    )
    chunk = Chunk(id="c1", document_id="doc-1", chunk_index=0, text_content="A", embedding=np.array([1.0], dtype=np.float32), metadata={})
    store.upsert_document(doc, [chunk])
    
    store.delete_document(temp_dir / "test.txt")
    
    retrieved = store.get_document_by_path(temp_dir / "test.txt")
    assert retrieved is None
