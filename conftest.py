import tempfile
from pathlib import Path
import pytest


@pytest.fixture
def temp_dir() -> Path:
    """Provide a temporary directory that is automatically cleaned up after the test."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def test_db_path(temp_dir: Path) -> Path:
    """Provide a path for a test SQLite database inside the temp directory."""
    return temp_dir / "jwrag_index.db"
