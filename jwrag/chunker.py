from typing import List
import numpy as np
from jwrag.models import Chunk


class TextChunker:
    """Splits text content into overlapping chunks based on hierarchical separators."""

    def __init__(self, chunk_size: int = 1024, overlap: int = 200) -> None:
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.separators = ["\n\n", "\n", ". ", " ", ""]

    def _find_split_point(self, text: str, start: int, end: int) -> int:
        """Finds the best split point within [start, end] using hierarchical separators."""
        for sep in self.separators:
            pos = text.rfind(sep, start, end)
            if pos != -1:
                return pos + len(sep)
        return end

    def chunk(self, text: str) -> List[str]:
        """Splits text into chunks respecting size, overlap, and separators.
        
        Args:
            text: The raw text string to split.
            
        Returns:
            A list of non-empty text segments.
        """
        if not text.strip():
            return []
            
        chunks = []
        start = 0
        while start < len(text):
            end = min(start + self.chunk_size, len(text))
            
            split_pos = self._find_split_point(text, start, end)
            # If split_pos is at the very beginning or beyond end, force cut
            if split_pos <= start:
                split_pos = end
                
            chunks.append(text[start:split_pos])
            
            # Move start forward with overlap
            next_start = split_pos - self.overlap
            if next_start <= start:
                next_start = split_pos
            start = next_start
            
        return [c for c in chunks if c.strip()]

    def create_chunks(self, text: str, doc_id: str) -> List[Chunk]:
        """Splits text into chunks and wraps them in Chunk DTOs.
        
        Args:
            text: The raw text string to split.
            doc_id: The identifier of the source document.
            
        Returns:
            A list of Chunk objects ready for embedding and storage.
        """
        text_segments = self.chunk(text)
        chunks = []
        for i, segment in enumerate(text_segments):
            chunks.append(Chunk(
                id=f"{doc_id}_{i}",
                document_id=doc_id,
                chunk_index=i,
                text_content=segment,
                embedding=np.zeros((1,), dtype=np.float32), # Placeholder, will be replaced by actual embedding
                metadata={}
            ))
        return chunks
