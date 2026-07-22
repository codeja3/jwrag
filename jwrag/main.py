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
from jwrag.config import load_config
from jwrag.cloud_client import CloudSynthesisEngine
from loguru import logger


class JWRAGApp:
    def __init__(self, db_path: Path, doc_dir: Path) -> None:
        self.store = SQLiteVectorStore(db_path)
        self.store.initialize()
        
        config = load_config()
        if config.engine_type == "cloud":
            self.engine = CloudSynthesisEngine(
                api_key=config.cloud_api_key,
                base_url=config.base_url,
                embedding_model=config.embedding_model,
                synthesis_model=config.synthesis_model
            )
        else:
            self.engine = OllamaSynthesisEngine(
                base_url=config.base_url,
                embedding_model=config.embedding_model,
                synthesis_model=config.synthesis_model
            )
            
        self.renderer = TUIRenderer()
        self.watcher = DirectoryWatcher()
        self.parsers = [TextMarkdownParser(), PdfParser()]
        self.chunker = TextChunker()

        def sync_callback(event_type: str, filepath: Path) -> None:
            filepath = filepath.resolve()
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
                    
                    import tqdm
                    
                    doc_id = file_hash
                    
                    # Pre-calculate chunks to show progress
                    all_chunks = []
                    for page in pages:
                        page_chunks = self.chunker.create_chunks(page["text"], doc_id)
                        for chunk in page_chunks:
                            chunk.metadata.update(page)
                            chunk.metadata.pop("text", None)
                            chunk.metadata["filename"] = filepath.name
                            all_chunks.append(chunk)
                    
                    chunks = []
                    logger.info(f"Generating embeddings for {len(all_chunks)} chunks...")
                    
                    for chunk_idx, chunk in enumerate(tqdm.tqdm(all_chunks, desc=f"Embedding {filepath.name}")):
                        embedding = self.engine.generate_embedding(chunk.text_content)
                        chunks.append(Chunk(
                            id=f"{doc_id}_{chunk_idx}",
                            document_id=doc_id,
                            chunk_index=chunk_idx,
                            text_content=chunk.text_content,
                            embedding=embedding,
                            metadata=chunk.metadata
                        ))
                            
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
        
        # Migration: Normalize all database paths to absolute resolved paths
        try:
            conn = self.store._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id, filepath FROM documents")
            for row in cursor.fetchall():
                p = Path(row["filepath"])
                if not p.is_absolute():
                    resolved_p = p.resolve()
                    cursor.execute("UPDATE documents SET filepath = ? WHERE id = ?", (str(resolved_p), row["id"]))
            conn.commit()
        except Exception as e:
            logger.error(f"Error migrating database paths: {e}")
        
        # Initial sweep: Delete DB records for files that no longer exist
        try:
            conn = self.store._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT filepath FROM documents")
            db_filepaths = [Path(row["filepath"]) for row in cursor.fetchall()]
            for db_filepath in db_filepaths:
                if not db_filepath.exists():
                    logger.info(f"File deleted while app was closed: {db_filepath.name}")
                    sync_callback("deleted", db_filepath)
        except Exception as e:
            logger.error(f"Error during initial DB cleanup: {e}")

        # Initial sweep: Index new/modified files
        logger.info("Scanning for new or modified documents...")
        for filepath in doc_dir.iterdir():
            if not filepath.is_file():
                continue
            
            # Resolve to absolute path so it matches watchdog and the DB
            filepath = filepath.resolve()
            
            parser = next((p for p in self.parsers if p.can_parse(filepath)), None)
            if not parser:
                continue
                
            try:
                with open(filepath, "rb") as f:
                    current_hash = hashlib.md5(f.read()).hexdigest()
            except (FileNotFoundError, PermissionError):
                continue
                
            # Seed the watcher's sync manager state
            self.watcher._sync_manager._file_hashes[str(filepath)] = current_hash
            
            existing_doc = self.store.get_document_by_path(filepath)
            if not existing_doc or existing_doc.file_hash != current_hash:
                logger.info(f"Discovered unindexed or changed file: {filepath.name}")
                sync_callback("modified", filepath)

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
