"""Pytest fixtures for Rekall tests."""

import sqlite3
import tempfile
from pathlib import Path

import pytest


def make_config_with_db_path(db_path: Path):
    """Create a Config with custom db_path using ResolvedPaths."""
    from rekall.config import Config
    from rekall.paths import ResolvedPaths, PathSource

    paths = ResolvedPaths(
        config_dir=db_path.parent,
        data_dir=db_path.parent,
        cache_dir=db_path.parent / "cache",
        db_path=db_path,
        source=PathSource.CLI,
    )
    return Config(paths=paths)


@pytest.fixture
def temp_db_path(tmp_path: Path) -> Path:
    """Create a temporary database path."""
    return tmp_path / "test_knowledge.db"


@pytest.fixture
def memory_db(tmp_path: Path):
    """Create a Database instance with temp file for testing."""
    from rekall.db import Database

    db_path = tmp_path / "test.db"
    db = Database(db_path)
    db.init()
    yield db
    db.close()


@pytest.fixture
def temp_rekall_dir(tmp_path: Path) -> Path:
    """Create a temporary ~/.rekall/ directory."""
    rekall_dir = tmp_path / ".rekall"
    rekall_dir.mkdir(parents=True, exist_ok=True)
    return rekall_dir


@pytest.fixture(autouse=True)
def reset_globals():
    """Reset global state between tests."""
    # Reset before test
    import rekall.cli as cli_module
    import rekall.config as config_module

    cli_module._db = None
    config_module._config = None

    yield

    # Cleanup after test
    if cli_module._db is not None:
        cli_module._db.close()
        cli_module._db = None
    config_module._config = None
