import abc
from pathlib import Path
from typing import List, Optional
import numpy as np
from jwrag.models import DocumentMetadata, Chunk


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
