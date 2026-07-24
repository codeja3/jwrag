import pytest
import time
from pathlib import Path
from unittest.mock import MagicMock, call
import numpy as np

from jwrag.main import JWRAGApp
from jwrag.models import DocumentMetadata, Chunk, SynthesisResult, SynthesisOption

@pytest.fixture
def mock_app(mocker, tmp_path):
    mocker.patch("jwrag.main.SQLiteVectorStore")
    mocker.patch("jwrag.main.OllamaSynthesisEngine")
    mocker.patch("jwrag.main.DirectoryWatcher")
    mocker.patch("jwrag.main.TUIRenderer")
    
    mock_config = MagicMock()
    mock_config.engine_type = "local"
    mocker.patch("jwrag.main.load_config", return_value=mock_config)
    
    app = JWRAGApp(Path("dummy_db.db"), tmp_path)
    return app

def test_sync_callback_deleted(mock_app, tmp_path):
    callback = mock_app.watcher.start.call_args[0][1]
    filepath = (tmp_path / "test.txt").resolve()
    
    callback("deleted", filepath)
    mock_app.store.delete_document.assert_called_once_with(filepath)

def test_sync_callback_modified(mock_app, mocker, tmp_path):
    mocker.patch("jwrag.main.TextMarkdownParser")
    mocker.patch("jwrag.main.PdfParser")
    mocker.patch("jwrag.main.TextChunker")
    
    mock_parser = MagicMock()
    mock_parser.can_parse.return_value = True
    mock_parser.extract_text_with_metadata.return_value = [{"text": "hello world", "page_number": 1}]
    mock_app.parsers = [mock_parser]
    
    mock_chunker = MagicMock()
    mock_chunker.create_chunks.return_value = [
        Chunk("doc1_0", "doc1", 0, "hello world", np.zeros((1,)), {"page_number": 1})
    ]
    mock_app.chunker = mock_chunker
    
    # Mock hashlib to return a stable hash
    mocker.patch("jwrag.main.hashlib.md5", return_value=MagicMock(hexdigest=lambda: "hash123"))
    mocker.patch("jwrag.main.os.path.getmtime", return_value=123456789.0)
    
    mock_app.engine.generate_embedding.return_value = np.array([0.1, 0.2], dtype=np.float32)
    
    callback = mock_app.watcher.start.call_args[0][1]
    filepath = (tmp_path / "test.txt").resolve()
    
    # Mocking open for compute_hash
    mocker.patch("builtins.open", mocker.mock_open(read_data=b"data"))
    
    callback("modified", filepath)
    
    # Verify parsing
    mock_parser.can_parse.assert_called_with(filepath)
    mock_parser.extract_text_with_metadata.assert_called_once_with(filepath)
    
    # Verify embedding generation
    assert mock_app.engine.generate_embedding.call_count == 1
    
    # Verify store upsert
    assert mock_app.store.upsert_document.call_count == 1
    doc_arg, chunks_arg = mock_app.store.upsert_document.call_args[0]
    assert isinstance(doc_arg, DocumentMetadata)
    assert doc_arg.filepath == filepath
    assert len(chunks_arg) == 1
    assert np.array_equal(chunks_arg[0].embedding, np.array([0.1, 0.2], dtype=np.float32))

def test_process_query(mock_app):
    query = "test query"
    dummy_vector = np.array([0.1, 0.2], dtype=np.float32)
    dummy_chunks = [
        Chunk("id1", "doc1", 0, "content", dummy_vector, {"filename": "test.txt"})
    ]
    from jwrag.models import Reference
    dummy_result = SynthesisResult(
        query=query, 
        options=[SynthesisOption("Title", "Reasoning", ["Concl"])],
        references=[Reference(filename="test.txt")]
    )
    
    mock_app.engine.generate_embedding.return_value = dummy_vector
    mock_app.store.search_similar_chunks.return_value = dummy_chunks
    mock_app.engine.synthesize.return_value = dummy_result
    mock_app.renderer.render_result.return_value = "rendered output"
    
    result = mock_app.process_query(query)
    
    mock_app.engine.generate_embedding.assert_called_once_with(query)
    mock_app.store.search_similar_chunks.assert_called_once_with(dummy_vector, top_k=5)
    mock_app.engine.synthesize.assert_called_once_with(query, dummy_chunks)
    mock_app.renderer.render_result.assert_called_once_with(dummy_result)
    
    assert result == "rendered output"

