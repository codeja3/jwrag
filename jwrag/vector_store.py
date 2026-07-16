import sqlite3
import threading
from pathlib import Path
from typing import List, Optional
import json
import numpy as np
from loguru import logger
from jwrag.interfaces import IVectorStore
from jwrag.models import DocumentMetadata, Chunk


class SQLiteVectorStore(IVectorStore):
    """SQLite-backed vector store implementation adhering to IVectorStore interface."""

    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self._local = threading.local()

    def _get_connection(self) -> sqlite3.Connection:
        """Retrieves or initializes a database connection for the current thread."""
        if not hasattr(self._local, "conn"):
            self._local.conn = sqlite3.connect(self.db_path)
            self._local.conn.row_factory = sqlite3.Row
        return self._local.conn

    def initialize(self) -> None:
        """Creates the documents and document_chunks tables with required indexes."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id TEXT PRIMARY KEY,
                filepath TEXT UNIQUE NOT NULL,
                filename TEXT NOT NULL,
                file_hash TEXT NOT NULL,
                last_modified REAL NOT NULL,
                indexed_at REAL NOT NULL
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS document_chunks (
                id TEXT PRIMARY KEY,
                document_id TEXT NOT NULL,
                chunk_index INTEGER NOT NULL,
                text_content TEXT NOT NULL,
                embedding BLOB NOT NULL,
                metadata TEXT NOT NULL,
                FOREIGN KEY (document_id) REFERENCES documents (id) ON DELETE CASCADE
            )
        """)
        
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_chunks_document ON document_chunks(document_id)")
        conn.commit()
        logger.info(f"Database initialized at {self.db_path}")

    def upsert_document(self, doc: DocumentMetadata, chunks: List[Chunk]) -> None:
        """Upserts document metadata and its chunks within a single transaction."""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT OR REPLACE INTO documents (id, filepath, filename, file_hash, last_modified, indexed_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (doc.id, str(doc.filepath), doc.filename, doc.file_hash, doc.last_modified, doc.last_modified))
            
            cursor.execute("DELETE FROM document_chunks WHERE document_id = ?", (doc.id,))
            for chunk in chunks:
                embedding_blob = chunk.embedding.tobytes()
                metadata_json = json.dumps(chunk.metadata)
                cursor.execute("""
                    INSERT INTO document_chunks (id, document_id, chunk_index, text_content, embedding, metadata)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (chunk.id, chunk.document_id, chunk.chunk_index, chunk.text_content, embedding_blob, metadata_json))
            conn.commit()
            logger.info(f"Upserted document {doc.id} with {len(chunks)} chunks.")
        except Exception as e:
            conn.rollback()
            raise e

    def delete_document(self, filepath: Path) -> None:
        """Deletes a document and cascades to remove its chunks."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM documents WHERE filepath = ?", (str(filepath),))
        if cursor.rowcount > 0:
            conn.commit()
            logger.info(f"Deleted document at {filepath}")
        else:
            logger.warning(f"Document not found at {filepath}, nothing to delete.")

    def search_similar_chunks(self, query_vector: np.ndarray, top_k: int) -> List[Chunk]:
        """Fetches chunks and computes cosine similarity against the query vector."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, document_id, chunk_index, text_content, embedding, metadata FROM document_chunks")
        rows = cursor.fetchall()
        
        chunks_with_scores = []
        for row in rows:
            embedding_blob = row["embedding"]
            if len(embedding_blob) == 0:
                continue
            vec = np.frombuffer(embedding_blob, dtype=np.float32)
            
            dot_product = np.dot(query_vector, vec)
            norm_q = np.linalg.norm(query_vector)
            norm_v = np.linalg.norm(vec)
            
            if norm_q == 0 or norm_v == 0:
                continue
                
            similarity = dot_product / (norm_q * norm_v)
            chunks_with_scores.append((similarity, row))
            
        chunks_with_scores.sort(key=lambda x: x[0], reverse=True)
        
        result_chunks = []
        for sim, row in chunks_with_scores[:top_k]:
            metadata = json.loads(row["metadata"])
            chunk = Chunk(
                id=row["id"],
                document_id=row["document_id"],
                chunk_index=row["chunk_index"],
                text_content=row["text_content"],
                embedding=np.frombuffer(row["embedding"], dtype=np.float32),
                metadata=metadata
            )
            result_chunks.append(chunk)
        return result_chunks

    def get_document_by_path(self, filepath: Path) -> Optional[DocumentMetadata]:
        """Retrieves document metadata by its file path."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, filepath, filename, file_hash, last_modified FROM documents WHERE filepath = ?", (str(filepath),))
        row = cursor.fetchone()
        if row is None:
            return None
        return DocumentMetadata(
            id=row["id"],
            filepath=Path(row["filepath"]),
            filename=row["filename"],
            file_hash=row["file_hash"],
            last_modified=row["last_modified"]
        )
