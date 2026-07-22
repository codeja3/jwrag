from pathlib import Path
from typing import Callable, Optional
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from loguru import logger
from jwrag.sync_manager import IndexSyncManager


class DirectoryWatcher:
    """Watches a directory for file system events and triggers synchronization callbacks."""

    def __init__(self) -> None:
        self._observer = Observer()
        self._sync_manager = IndexSyncManager()
        self._callback: Optional[Callable[[str, Path], None]] = None
        self._directory_path: Optional[Path] = None

    def start(self, directory_path: Path, callback: Callable[[str, Path], None]) -> None:
        """Starts watching the target directory.
        
        Args:
            directory_path: The Path of the directory to monitor.
            callback: Function to invoke. Signature: callback(event_type: str, file_path: Path)
                      event_type can be 'created', 'modified', or 'deleted'.
        """
        self._directory_path = directory_path
        self._callback = callback
        
        class Handler(FileSystemEventHandler):
            def on_any_event(self, event):
                try:
                    if event.is_directory:
                        return
                        
                    filepath = Path(event.src_path)
                    
                    # Handle race condition where a file is deleted during modification
                    if not filepath.exists() and event.event_type == "modified":
                        self._process("deleted", filepath)
                        return
                        
                    self._process(event.event_type, filepath)
                except Exception as e:
                    logger.error(f"Error handling file event {event.event_type} for {event.src_path}: {e}")

            def _process(self, event_type: str, filepath: Path):
                action = self.sync_manager.process_event(event_type, filepath)
                if action == "upsert":
                    self.callback("modified", filepath)
                elif action == "delete":
                    self.callback("deleted", filepath)
                # else skip (noop)

        handler = Handler()
        handler.sync_manager = self._sync_manager
        handler.callback = callback
        
        self._observer.schedule(handler, str(directory_path), recursive=False)
        self._observer.start()
        logger.info(f"Started watching directory: {directory_path}")

    def stop(self) -> None:
        """Stops watching the directory."""
        if self._observer.is_alive():
            self._observer.stop()
            self._observer.join()
            logger.info("Stopped watching directory.")
