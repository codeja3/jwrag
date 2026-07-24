import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from jwrag.directory_watcher import DirectoryWatcher


@pytest.fixture
def watcher() -> DirectoryWatcher:
    return DirectoryWatcher()


def test_start_initializes_and_starts_observer(watcher: DirectoryWatcher) -> None:
    mock_instance = MagicMock()
    watcher._observer = mock_instance
    
    callback = MagicMock()
    watcher.start(Path("/tmp/test_dir"), callback)
    
    mock_instance.schedule.assert_called_once()
    mock_instance.start.assert_called_once()


def test_stop_stops_and_joins_observer(watcher: DirectoryWatcher) -> None:
    mock_instance = MagicMock()
    mock_instance.is_alive.return_value = True
    watcher._observer = mock_instance
    
    watcher.start(Path("/tmp/test_dir"), lambda e, p: None)
    
    watcher.stop()
    
    mock_instance.stop.assert_called_once()
    mock_instance.join.assert_called_once()


def test_handler_processes_created_event(watcher: DirectoryWatcher, temp_dir: Path) -> None:
    mock_instance = MagicMock()
    watcher._observer = mock_instance
    watcher._sync_manager.process_event = MagicMock(return_value="upsert")
    
    callback = MagicMock()
    watcher.start(temp_dir, callback)
    
    # Simulate event directly on handler
    handler = mock_instance.schedule.call_args[0][0]
    mock_event = MagicMock()
    mock_event.is_directory = False
    mock_event.src_path = str(temp_dir / "new.txt")
    (temp_dir / "new.txt").write_text("test")
    
    handler.on_any_event(mock_event)
    
    # Callback should be invoked for upsert
    callback.assert_called_once()
    assert callback.call_args[0][0] == "modified"


def test_handler_processes_deleted_event(watcher: DirectoryWatcher, temp_dir: Path) -> None:
    mock_instance = MagicMock()
    watcher._observer = mock_instance
    watcher._sync_manager.process_event = MagicMock(return_value="delete")
    
    callback = MagicMock()
    watcher.start(temp_dir, callback)
    
    handler = mock_instance.schedule.call_args[0][0]
    mock_event = MagicMock()
    mock_event.is_directory = False
    mock_event.src_path = str(temp_dir / "deleted.txt")
    (temp_dir / "deleted.txt").write_text("test") # Pre-exist for hash tracking
    
    handler.on_any_event(mock_event)
    
    callback.assert_called_once()
    assert callback.call_args[0][0] == "deleted"
