import abc
from pathlib import Path
from typing import Callable, List, Dict, Any, Optional
import numpy as np
from jwrag.models import DocumentMetadata, Chunk, SynthesisResult


class IVectorStore(abc.ABC):
    @abc.abstractmethod
    def initialize(self) -> None:
        """Sets up database tables and schemas."""
        pass

    @abc.abstractmethod
    def upsert_document(self, doc: DocumentMetadata, chunks: List[Chunk]) -> None:
        """Saves or updates document metadata and its associated chunks in a single transaction."""
        pass

    @abc.abstractmethod
    def delete_document(self, filepath: Path) -> None:
        """Deletes all records and chunks associated with the file path."""
        pass

    @abc.abstractmethod
    def search_similar_chunks(self, query_vector: np.ndarray, top_k: int) -> List[Chunk]:
        """Performs cosine similarity search against stored embeddings."""
        pass

    @abc.abstractmethod
    def get_document_by_path(self, filepath: Path) -> Optional[DocumentMetadata]:
        """Retrieves document metadata if file is indexed."""
        pass


class IDirectoryWatcher(abc.ABC):
    @abc.abstractmethod
    def start(self, directory_path: Path, callback: Callable[[str, Path], None]) -> None:
        """Starts watching the target directory. Triggers callback on file events.
        
        Args:
            directory_path: The Path of the directory to monitor.
            callback: Function to invoke. Signature: callback(event_type: str, file_path: Path)
                      event_type can be 'created', 'modified', or 'deleted'.
        """
        pass

    @abc.abstractmethod
    def stop(self) -> None:
        """Stops watching the directory."""
        pass


class IDocumentParser(abc.ABC):
    @abc.abstractmethod
    def can_parse(self, filepath: Path) -> bool:
        """Checks if this parser supports the file extension."""
        pass

    @abc.abstractmethod
    def extract_text_with_metadata(self, filepath: Path) -> List[Dict[str, Any]]:
        """Extracts text content and metadata from the document.
        
        Returns:
            A list of dicts, each representing a page or section:
                [{"text": "page/section text", "page_number": 1, ...}]
        """
        pass


class ISynthesisEngine(abc.ABC):
    @abc.abstractmethod
    def generate_embedding(self, text: str) -> np.ndarray:
        """Generates embedding vector for a given text segment using Ollama API."""
        pass

    @abc.abstractmethod
    def synthesize(self, query: str, chunks: List[Chunk]) -> SynthesisResult:
        """Constructs prompt, requests LLM synthesis from Ollama, and parses the multi-perspective result."""
        pass
