import pytest
from unittest.mock import patch, MagicMock
import numpy as np
from jwrag.cloud_client import CloudSynthesisEngine
from jwrag.models import Chunk, SynthesisResult

@pytest.fixture
def engine() -> CloudSynthesisEngine:
    return CloudSynthesisEngine(
        api_key="sk-test",
        base_url="https://api.openai.com/v1",
        embedding_model="text-embedding-3-small",
        synthesis_model="gpt-4o"
    )

def test_cloud_generate_embedding(engine: CloudSynthesisEngine) -> None:
    with patch("jwrag.cloud_client.OpenAI") as MockOpenAI:
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.data = [MagicMock(embedding=[0.1, 0.2, 0.3])]
        mock_client.embeddings.create.return_value = mock_response
        MockOpenAI.return_value = mock_client
        
        # Override the engine client with mock
        engine.client = mock_client
        
        # Mock the sanitizer to return the text and an empty mapping
        with patch.object(engine.sanitizer, "anonymize", return_value=("Anon text", {})):
            vec = engine.generate_embedding("Test text")
            
            assert vec.shape == (3,)
            assert np.allclose(vec, np.array([0.1, 0.2, 0.3]))
            mock_client.embeddings.create.assert_called_once_with(
                input="Anon text",
                model="text-embedding-3-small"
            )

def test_cloud_synthesize(engine: CloudSynthesisEngine) -> None:
    with patch("jwrag.cloud_client.OpenAI") as MockOpenAI:
        mock_client = MagicMock()
        mock_choice = MagicMock()
        
        # The mocked LLM returns anonymized JSON
        mock_choice.message.content = '''
        {
            "options": [
                {
                    "title": "Option for <PERSON_1>",
                    "reasoning": "Because <PERSON_1> is good.",
                    "conclusions": ["Contact <PERSON_1>"]
                }
            ]
        }
        '''
        mock_response = MagicMock(choices=[mock_choice])
        mock_client.chat.completions.create.return_value = mock_response
        
        # Override the engine client with mock
        engine.client = mock_client
        
        chunks = [Chunk(id="1", document_id="d1", chunk_index=0, text_content="John Doe context", embedding=np.zeros(3), metadata={})]
        
        # Mock the sanitizer to simulate anonymization
        mapping = {"<PERSON_1>": "John Doe"}
        def mock_anonymize(text: str) -> tuple[str, dict[str, str]]:
            return text.replace("John Doe", "<PERSON_1>"), mapping
            
        def mock_deanonymize(text: str, m: dict[str, str]) -> str:
            return text.replace("<PERSON_1>", "John Doe")
            
        with patch.object(engine.sanitizer, "anonymize", side_effect=mock_anonymize):
            with patch.object(engine.sanitizer, "deanonymize", side_effect=mock_deanonymize):
                result = engine.synthesize("What about John Doe?", chunks)
                
                assert len(result.options) == 1
                assert result.options[0].title == "Option for John Doe"
                assert result.options[0].reasoning == "Because John Doe is good."
                assert result.options[0].conclusions[0] == "Contact John Doe"
