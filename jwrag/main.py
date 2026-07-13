import sys
from pathlib import Path
from jwrag.vector_store import SQLiteVectorStore
from jwrag.clients import OllamaSynthesisEngine
from jwrag.directory_watcher import DirectoryWatcher
from jwrag.cli import TUIRenderer
from loguru import logger


class JWRAGApp:
    def __init__(self, db_path: Path, doc_dir: Path) -> None:
        self.store = SQLiteVectorStore(db_path)
        self.store.initialize()
        self.engine = OllamaSynthesisEngine()
        self.renderer = TUIRenderer()
        self.watcher = DirectoryWatcher()

        def sync_callback(event_type: str, filepath: Path) -> None:
            logger.info(f"Sync event: {event_type} -> {filepath}")
            # TODO: Wire up actual upsert/delete logic based on event_type

        self.watcher.start(doc_dir, sync_callback)

    def process_query(self, query: str) -> str:
        print("Embedding query...")
        print("Searching chunks...")
        print("Synthesizing...")
        # TODO: Implement full pipeline: embed -> search -> synthesize -> render
        return "Query processed."

    def stop(self) -> None:
        self.watcher.stop()


def run() -> None:
    db_path = Path("jwrag_index.db")
    doc_dir = Path("./documents")

    app = JWRAGApp(db_path, doc_dir)
    print("JWRAG Ready. Type 'exit' to quit.")
    try:
        while True:
            query = input("\n> ")
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
