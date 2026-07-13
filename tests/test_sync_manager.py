import pytest
from pathlib import Path
from jwrag.sync_manager import IndexSyncManager


@pytest.fixture
def sync_manager() -> IndexSyncManager:
    return IndexSyncManager()


def test_process_event_created_returns_upsert(sync_manager: IndexSyncManager, temp_dir: Path) -> None:
    filepath = temp_dir / "test.txt"
    filepath.write_text("Initial content")
    
    action = sync_manager.process_event("created", filepath)
    assert action == "upsert"


def test_process_event_modified_same_hash_returns_none(sync_manager: IndexSyncManager, temp_dir: Path) -> None:
    filepath = temp_dir / "test.txt"
    filepath.write_text("Content")
    
    # First event establishes the hash
    sync_manager.process_event("created", filepath)
    
    # Second event with same content should be skipped
    action = sync_manager.process_event("modified", filepath)
    assert action is None


def test_process_event_modified_diff_hash_returns_upsert(sync_manager: IndexSyncManager, temp_dir: Path) -> None:
    filepath = temp_dir / "test.txt"
    filepath.write_text("Content")
    
    # Establish initial hash
    sync_manager.process_event("created", filepath)
    
    # Modify file
    filepath.write_text("Modified content")
    
    action = sync_manager.process_event("modified", filepath)
    assert action == "upsert"


def test_process_event_deleted_returns_delete(sync_manager: IndexSyncManager, temp_dir: Path) -> None:
    filepath = temp_dir / "test.txt"
    filepath.write_text("Content")
    
    # Establish hash
    sync_manager.process_event("created", filepath)
    
    # Delete file (simulate by removing from cache as watchdog doesn't write it)
    action = sync_manager.process_event("deleted", filepath)
    assert action == "delete"
