import dataclasses
from pathlib import Path
from typing import Dict, Any, List
import numpy as np


@dataclasses.dataclass(frozen=True)
class DocumentMetadata:
    """Immutable metadata representing a document in the index."""
    id: str
    filepath: Path
    filename: str
    file_hash: str
    last_modified: float


@dataclasses.dataclass(frozen=True)
class Chunk:
    """Immutable chunk of text with its associated embedding and metadata."""
    id: str
    document_id: str
    chunk_index: int
    text_content: str
    embedding: np.ndarray
    metadata: Dict[str, Any]


@dataclasses.dataclass(frozen=True)
class SynthesisOption:
    """Immutable representation of a single judgment perspective."""
    title: str
    reasoning: str
    conclusions: List[str]


@dataclasses.dataclass(frozen=True)
class SynthesisResult:
    """Immutable result containing query, options, and references."""
    query: str
    options: List[SynthesisOption]
    references: List[str]
