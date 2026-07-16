import sys
import os
import hashlib
from pathlib import Path
from jwrag.vector_store import SQLiteVectorStore
from jwrag.clients import OllamaSynthesisEngine
from jwrag.directory_watcher import DirectoryWatcher
from jwrag.cli import TUIRenderer
from jwrag.parsers import TextMarkdownParser, PdfParser
from jwrag.chunker import TextChunker
from jwrag.models import DocumentMetadata, Chunk, SynthesisResult
from loguru import logger


class JWRAGApp:
    def __init__(self, db_path: Path, doc_dir: Path) -> None:
        self.store = SQLiteVectorStore(db_path)
        self.store.initialize()
        self.engine = OllamaSynthesisEngine()
        self.renderer = TUIRenderer()
        self.watcher = DirectoryWatcher()
        self.parsers = [TextMarkdownParser(), PdfParser()]
        self.chunker = TextChunker()

        def sync_callback(event_type: str, filepath: Path) -> None:
            logger.info(f"Sync event: {event_type} -> {filepath}")
            if event_type == "deleted":
                self.store.delete_document(filepath)
            elif event_type == "modified":
                parser = next((p for p in self.parsers if p.can_parse(filepath)), None)
                if not parser:
                    logger.warning(f"No parser found for {filepath}")
                    return
                
                try:
                    pages = parser.extract_text_with_metadata(filepath)
                    chunks = []
                    
                    with open(filepath, "rb") as f:
                        file_hash = hashlib.md5(f.read()).hexdigest()
                    
                    doc_id = file_hash
                    
                    chunk_idx = 0
                    for page in pages:
                        page_chunks = self.chunker.create_chunks(page["text"], doc_id)
                        for chunk in page_chunks:
                            chunk_meta = chunk.metadata.copy()
                            chunk_meta.update(page)
                            chunk_meta.pop("text", None)
                            chunk_meta["filename"] = filepath.name
                            
                            embedding = self.engine.generate_embedding(chunk.text_content)
                            
                            chunks.append(Chunk(
                                id=f"{doc_id}_{chunk_idx}",
                                document_id=doc_id,
                                chunk_index=chunk_idx,
                                text_content=chunk.text_content,
                                embedding=embedding,
                                metadata=chunk_meta
                            ))
                            chunk_idx += 1
                            
                    doc_meta = DocumentMetadata(
                        id=doc_id,
                        filepath=filepath,
                        filename=filepath.name,
                        file_hash=file_hash,
                        last_modified=os.path.getmtime(filepath)
                    )
                    self.store.upsert_document(doc_meta, chunks)
                    logger.info(f"Successfully upserted {filepath}")
                except Exception as e:
                    logger.error(f"Error processing {filepath}: {e}")

        self.watcher.start(doc_dir, sync_callback)

    def process_query(self, query: str) -> str:
        print("Embedding query...")
        query_vector = self.engine.generate_embedding(query)
        
        print("Searching chunks...")
        chunks = self.store.search_similar_chunks(query_vector, top_k=5)
        
        print("Synthesizing...")
        result = self.engine.synthesize(query, chunks)
        
        unique_refs = list(set([c.metadata.get("filename", "Unknown") for c in chunks]))
        final_result = SynthesisResult(
            query=result.query,
            options=result.options,
            references=unique_refs
        )
        
        return self.renderer.render_result(final_result)

    def stop(self) -> None:
        self.watcher.stop()


def run() -> None:
    db_path = Path("jwrag_index.db")
    doc_dir = Path("./documents")
    
    # Auto-create the documents directory to prevent watchdog crashes
    doc_dir.mkdir(parents=True, exist_ok=True)

    app = JWRAGApp(db_path, doc_dir)
    print("JWRAG Ready. Type 'exit' to quit.")
    try:
        while True:
            query = input("\n> ")
            if not query.strip():
                continue
            if query.strip().lower() in ("exit", "quit"):
                break
            result = app.process_query(query)
            print(result)
    except KeyboardInterrupt:
        pass
    finally:
        app.stop()


if __name__ == "__main__":
    run()
