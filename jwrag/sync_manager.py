import hashlib
from pathlib import Path
from typing import Dict, Optional
from loguru import logger


class IndexSyncManager:
    """Manages file state tracking and determines synchronization actions."""

    def __init__(self) -> None:
        self._file_hashes: Dict[str, str] = {}

    def _compute_hash(self, filepath: Path) -> str:
        """Computes MD5 hash of a file's contents.
        
        Args:
            filepath: The path to the file to hash.
            
        Returns:
            Hexadecimal string representation of the MD5 hash.
        """
        hasher = hashlib.md5()
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hasher.update(chunk)
        return hasher.hexdigest()

    def process_event(self, event_type: str, filepath: Path) -> Optional[str]:
        """Evaluates a filesystem event and returns the appropriate sync action.
        
        Args:
            event_type: One of 'created', 'modified', or 'deleted'.
            filepath: The path to the affected file.
            
        Returns:
            'upsert' if the file should be indexed, 'delete' if it should be removed, 
            or None if no action is needed.
        """
        filepath_str = str(filepath)
        
        if event_type == "created":
            self._file_hashes[filepath_str] = self._compute_hash(filepath)
            return "upsert"
            
        elif event_type == "modified":
            current_hash = self._compute_hash(filepath)
            old_hash = self._file_hashes.get(filepath_str)
            if old_hash != current_hash:
                self._file_hashes[filepath_str] = current_hash
                return "upsert"
            return None
            
        elif event_type == "deleted":
            self._file_hashes.pop(filepath_str, None)
            return "delete"
            
        return None
