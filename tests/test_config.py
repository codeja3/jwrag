import os
from unittest.mock import patch
import pytest
from jwrag.config import load_config

def test_load_config_local_default() -> None:
    with patch.dict(os.environ, {}, clear=True), patch('jwrag.config.load_dotenv'):
        config = load_config()
        assert config.engine_type == "local"
        assert config.embedding_model == "qwen3-embedding:4b"
        assert config.synthesis_model == "gemma4:26b-mlx"
        assert config.base_url == "http://localhost:11434"
        assert config.cloud_api_key is None

def test_load_config_cloud_success() -> None:
    with patch.dict(os.environ, {"JWRAG_ENGINE": "cloud", "JWRAG_CLOUD_API_KEY": "sk-test"}, clear=True), patch('jwrag.config.load_dotenv'):
        config = load_config()
        assert config.engine_type == "cloud"
        assert config.embedding_model == "text-embedding-3-small"
        assert config.synthesis_model == "gpt-4o"
        assert config.base_url == "https://api.openai.com/v1"
        assert config.cloud_api_key == "sk-test"

def test_load_config_cloud_missing_key() -> None:
    with patch.dict(os.environ, {"JWRAG_ENGINE": "cloud"}, clear=True), patch('jwrag.config.load_dotenv'):
        with pytest.raises(ValueError, match="JWRAG_CLOUD_API_KEY must be set"):
            load_config()

def test_load_config_unknown_engine() -> None:
    with patch.dict(os.environ, {"JWRAG_ENGINE": "magic"}, clear=True), patch('jwrag.config.load_dotenv'):
        with pytest.raises(ValueError, match="Unknown engine type"):
            load_config()
