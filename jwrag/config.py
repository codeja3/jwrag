import os
from pathlib import Path
from dataclasses import dataclass
from dotenv import load_dotenv

@dataclass
class Config:
    engine_type: str
    embedding_model: str
    synthesis_model: str
    cloud_api_key: str | None
    base_url: str

def load_config() -> Config:
    # Look for a .env file in the current working directory
    load_dotenv(Path(".env"))
    
    engine_type = os.getenv("JWRAG_ENGINE", "local").lower()
    
    if engine_type == "local":
        embedding_model = os.getenv("JWRAG_EMBEDDING_MODEL", "qwen3-embedding:4b")
        synthesis_model = os.getenv("JWRAG_SYNTHESIS_MODEL", "gemma4:26b-mlx")
        base_url = os.getenv("JWRAG_BASE_URL", "http://localhost:11434")
        cloud_api_key = None
    elif engine_type == "cloud":
        embedding_model = os.getenv("JWRAG_EMBEDDING_MODEL", "text-embedding-3-small")
        synthesis_model = os.getenv("JWRAG_SYNTHESIS_MODEL", "gpt-4o")
        base_url = os.getenv("JWRAG_BASE_URL", "https://api.openai.com/v1")
        cloud_api_key = os.getenv("JWRAG_CLOUD_API_KEY")
        if not cloud_api_key:
            raise ValueError("JWRAG_CLOUD_API_KEY must be set when using cloud engine")
    else:
        raise ValueError(f"Unknown engine type: {engine_type}. Must be 'local' or 'cloud'.")
        
    return Config(
        engine_type=engine_type,
        embedding_model=embedding_model,
        synthesis_model=synthesis_model,
        cloud_api_key=cloud_api_key,
        base_url=base_url
    )
