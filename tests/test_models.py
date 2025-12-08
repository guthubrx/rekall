"""Tests for Rekall models (TDD - written before implementation)."""

import re
from datetime import datetime


class TestULID:
    """Tests for ULID generation (T007)."""

    def test_ulid_format_26_chars(self):
        """ULID must be exactly 26 characters."""
        from rekall.models import generate_ulid

        ulid = generate_ulid()
        assert len(ulid) == 26

    def test_ulid_valid_characters(self):
        """ULID must only contain Crockford Base32 characters."""
        from rekall.models import generate_ulid

        ulid = generate_ulid()
        # Crockford Base32: 0-9, A-Z excluding I, L, O, U
        valid_pattern = r"^[0-9A-HJKMNP-TV-Z]{26}$"
        assert re.match(valid_pattern, ulid), f"Invalid ULID: {ulid}"

    def test_ulid_uniqueness(self):
        """Multiple ULIDs must be unique."""
        from rekall.models import generate_ulid

        ulids = [generate_ulid() for _ in range(100)]
        assert len(set(ulids)) == 100, "ULIDs are not unique"

    def test_ulid_sortable_chronologically(self):
        """ULIDs generated later should sort after earlier ones."""
        import time

        from rekall.models import generate_ulid

        ulid1 = generate_ulid()
        time.sleep(0.002)  # Small delay to ensure different timestamp
        ulid2 = generate_ulid()
        assert ulid1 < ulid2, "ULIDs should be chronologically sortable"


class TestEntry:
    """Tests for Entry dataclass (T008)."""

    def test_entry_creation_valid(self):
        """Entry should be created with valid type."""
        from rekall.models import Entry, generate_ulid

        entry = Entry(
            id=generate_ulid(),
            title="Test bug",
            type="bug",
        )
        assert entry.title == "Test bug"
        assert entry.type == "bug"
        assert entry.confidence == 2  # default
        assert entry.status == "active"  # default

    def test_entry_all_valid_types(self):
        """All 6 types should be valid."""
        from rekall.models import Entry, generate_ulid

        valid_types = ["bug", "pattern", "decision", "pitfall", "config", "reference"]
        for entry_type in valid_types:
            entry = Entry(id=generate_ulid(), title="Test", type=entry_type)
            assert entry.type == entry_type

    def test_entry_invalid_type_raises(self):
        """Invalid type should raise ValueError."""
        import pytest

        from rekall.models import Entry, generate_ulid

        with pytest.raises(ValueError, match="invalid type"):
            Entry(id=generate_ulid(), title="Test", type="invalid")

    def test_entry_confidence_valid_range(self):
        """Confidence 0-5 should be valid."""
        from rekall.models import Entry, generate_ulid

        for confidence in range(6):
            entry = Entry(
                id=generate_ulid(), title="Test", type="bug", confidence=confidence
            )
            assert entry.confidence == confidence

    def test_entry_confidence_invalid_raises(self):
        """Confidence outside 0-5 should raise ValueError."""
        import pytest

        from rekall.models import Entry, generate_ulid

        with pytest.raises(ValueError, match="confidence must be 0-5"):
            Entry(id=generate_ulid(), title="Test", type="bug", confidence=6)

        with pytest.raises(ValueError, match="confidence must be 0-5"):
            Entry(id=generate_ulid(), title="Test", type="bug", confidence=-1)

    def test_entry_with_tags(self):
        """Entry should accept list of tags."""
        from rekall.models import Entry, generate_ulid

        entry = Entry(
            id=generate_ulid(),
            title="Test",
            type="bug",
            tags=["python", "sqlite"],
        )
        assert entry.tags == ["python", "sqlite"]

    def test_entry_with_project(self):
        """Entry should accept project name."""
        from rekall.models import Entry, generate_ulid

        entry = Entry(
            id=generate_ulid(),
            title="Test",
            type="bug",
            project="my-project",
        )
        assert entry.project == "my-project"

    def test_entry_obsolete_status(self):
        """Entry should support obsolete status."""
        from rekall.models import Entry, generate_ulid

        entry = Entry(
            id=generate_ulid(),
            title="Test",
            type="bug",
            status="obsolete",
            superseded_by="01ARZ3NDEKTSV4RRFFQ69G5FAV",
        )
        assert entry.status == "obsolete"
        assert entry.superseded_by == "01ARZ3NDEKTSV4RRFFQ69G5FAV"

    def test_entry_timestamps_auto(self):
        """Entry should have auto-generated timestamps."""
        from rekall.models import Entry, generate_ulid

        before = datetime.now()
        entry = Entry(id=generate_ulid(), title="Test", type="bug")
        after = datetime.now()

        assert before <= entry.created_at <= after
        assert before <= entry.updated_at <= after


class TestConfig:
    """Tests for Config dataclass (T009)."""

    def test_config_default_db_path(self):
        """Config should have default db_path in XDG location."""
        from pathlib import Path

        from rekall.config import Config

        config = Config()
        # Now uses XDG paths by default
        expected = Path.home() / ".local" / "share" / "rekall" / "knowledge.db"
        assert config.db_path == expected

    def test_config_custom_db_path(self):
        """Config should accept custom paths via ResolvedPaths."""
        from pathlib import Path

        from rekall.config import Config
        from rekall.paths import ResolvedPaths, PathSource

        custom_path = Path("/tmp/test.db")
        paths = ResolvedPaths(
            config_dir=Path("/tmp"),
            data_dir=Path("/tmp"),
            cache_dir=Path("/tmp/cache"),
            db_path=custom_path,
            source=PathSource.CLI,
        )
        config = Config(paths=paths)
        assert config.db_path == custom_path

    def test_config_rekall_dir(self):
        """Config should provide rekall_dir property (now data_dir)."""
        from pathlib import Path

        from rekall.config import Config

        config = Config()
        # Now uses XDG data dir
        expected = Path.home() / ".local" / "share" / "rekall"
        assert config.rekall_dir == expected

    def test_config_editor_default_none(self):
        """Config editor should default to None."""
        from rekall.config import Config

        config = Config()
        assert config.editor is None

    def test_config_embeddings_default_none(self):
        """Config embeddings settings should default to None."""
        from rekall.config import Config

        config = Config()
        assert config.embeddings_provider is None
        assert config.embeddings_model is None
