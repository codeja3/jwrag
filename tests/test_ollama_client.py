import pytest
from unittest.mock import patch, MagicMock
import numpy as np
from jwrag.models import Chunk
from jwrag.clients import OllamaSynthesisEngine


@pytest.fixture
def engine() -> OllamaSynthesisEngine:
    return OllamaSynthesisEngine(base_url="http://localhost:11434")


def test_generate_embedding_success(engine: OllamaSynthesisEngine) -> None:
    mock_response = MagicMock()
    mock_response.json.return_value = {"embedding": [0.1, 0.2, 0.3]}
    mock_response.raise_for_status = MagicMock()
    
    with patch.object(engine.client, 'post', return_value=mock_response) as mock_post:
        result = engine.generate_embedding("Test text")
        
        assert isinstance(result, np.ndarray)
        assert np.allclose(result, [0.1, 0.2, 0.3])
        mock_post.assert_called_once()


def test_generate_embedding_failure(engine: OllamaSynthesisEngine) -> None:
    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = Exception("Network Error")
    
    with patch.object(engine.client, 'post', return_value=mock_response):
        with pytest.raises(Exception):
            engine.generate_embedding("Test text")


def test_synthesize_success(engine: OllamaSynthesisEngine) -> None:
    mock_response = MagicMock()
    mock_response.json.return_value = {"response": '{"options": [{"title": "A", "reasoning": "R", "conclusions": ["C1"]}], "references": [{"filename": "doc1.pdf", "page": "1", "paragraph": "2"}]}'}
    mock_response.raise_for_status = MagicMock()
    
    with patch.object(engine.client, 'post', return_value=mock_response) as mock_post:
        chunks = [Chunk(id="1", document_id="d1", chunk_index=0, text_content="Context A", embedding=np.zeros(3), metadata={"filename": "doc1.pdf", "page_number": 1, "paragraph": 2})]
        result = engine.synthesize("Query?", chunks)
        
        assert len(result.options) == 1
        assert result.options[0].title == "A"
        assert len(result.references) == 1
        assert result.references[0].filename == "doc1.pdf"
        assert result.references[0].page == "1"
        assert result.references[0].paragraph == "2"
        
        # Verify prompt prefixing
        call_args = mock_post.call_args[1]["json"]
        assert "[Document: doc1.pdf, Page: 1, Paragraph: 2]" in call_args["prompt"]


def test_synthesize_json_parsing_fallbacks(engine: OllamaSynthesisEngine) -> None:
    # Test markdown fence stripping
    mock_response = MagicMock()
    mock_response.json.return_value = {"response": '```json\n{"options": [{"title": "B", "reasoning": "R", "conclusions": []}], "references": []}\n```'}
    mock_response.raise_for_status = MagicMock()
    
    with patch.object(engine.client, 'post', return_value=mock_response):
        chunks = [Chunk(id="1", document_id="d1", chunk_index=0, text_content="Context B", embedding=np.zeros(3), metadata={})]
        result = engine.synthesize("Query?", chunks)
        assert len(result.options) == 1
        assert result.options[0].title == "B"

    # Test regex extraction
    mock_response2 = MagicMock()
    mock_response2.json.return_value = {"response": "Some text before {\"options\": [{\"title\": \"C\", \"reasoning\": \"R\", \"conclusions\": []}], \"references\": []} after text"}
    mock_response2.raise_for_status = MagicMock()
    
    with patch.object(engine.client, 'post', return_value=mock_response2):
        chunks = [Chunk(id="1", document_id="d1", chunk_index=0, text_content="Context C", embedding=np.zeros(3), metadata={})]
        result = engine.synthesize("Query?", chunks)
        assert len(result.options) == 1
        assert result.options[0].title == "C"


def test_synthesize_hard_fallback_on_max_retries(engine: OllamaSynthesisEngine) -> None:
    mock_response = MagicMock()
    mock_response.json.return_value = {"response": "Invalid JSON {{{"}
    mock_response.raise_for_status = MagicMock()
    
    call_count = 0
    def side_effect(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        return mock_response
        
    with patch.object(engine.client, 'post', side_effect=side_effect):
        chunks = [Chunk(id="1", document_id="d1", chunk_index=0, text_content="Context D", embedding=np.zeros(3), metadata={})]
        result = engine.synthesize("Query?", chunks)
        
        assert call_count == 3 # 1 initial + 2 retries
        assert len(result.options) == 1
        assert result.options[0].title == "Parsing Failure"
