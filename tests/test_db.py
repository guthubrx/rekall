"""Tests for Rekall database (TDD - written before implementation)."""

import sqlite3
from pathlib import Path


class TestDatabaseCreation:
    """Tests for database creation (T010)."""

    def test_database_creates_file(self, temp_db_path: Path):
        """Database should create file at specified path."""
        from rekall.db import Database

        db = Database(temp_db_path)
        db.init()
        assert temp_db_path.exists()
        db.close()

    def test_database_creates_entries_table(self, temp_db_path: Path):
        """Database should create entries table with correct schema."""
        from rekall.db import Database

        db = Database(temp_db_path)
        db.init()

        # Check table exists
        cursor = db.conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='entries'"
        )
        assert cursor.fetchone() is not None

        # Check columns
        cursor = db.conn.execute("PRAGMA table_info(entries)")
        columns = {row[1]: row[2] for row in cursor.fetchall()}
        assert "id" in columns
        assert "title" in columns
        assert "content" in columns
        assert "type" in columns
        assert "project" in columns
        assert "confidence" in columns
        assert "status" in columns
        assert "superseded_by" in columns
        assert "created_at" in columns
        assert "updated_at" in columns

        db.close()

    def test_database_creates_tags_table(self, temp_db_path: Path):
        """Database should create tags table."""
        from rekall.db import Database

        db = Database(temp_db_path)
        db.init()

        cursor = db.conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='tags'"
        )
        assert cursor.fetchone() is not None
        db.close()

    def test_database_creates_fts5_table(self, temp_db_path: Path):
        """Database should create FTS5 virtual table."""
        from rekall.db import Database

        db = Database(temp_db_path)
        db.init()

        cursor = db.conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='entries_fts'"
        )
        assert cursor.fetchone() is not None
        db.close()

    def test_database_wal_mode_enabled(self, temp_db_path: Path):
        """Database should use WAL mode."""
        from rekall.db import Database

        db = Database(temp_db_path)
        db.init()

        cursor = db.conn.execute("PRAGMA journal_mode")
        mode = cursor.fetchone()[0]
        assert mode.lower() == "wal"
        db.close()


class TestCRUD:
    """Tests for CRUD operations (T011)."""

    def test_add_entry(self, temp_db_path: Path):
        """Should add entry to database."""
        from rekall.db import Database
        from rekall.models import Entry, generate_ulid

        db = Database(temp_db_path)
        db.init()

        entry = Entry(
            id=generate_ulid(),
            title="Test bug",
            type="bug",
            content="Some content",
            tags=["python", "test"],
        )
        db.add(entry)

        # Verify entry exists
        cursor = db.conn.execute("SELECT * FROM entries WHERE id = ?", (entry.id,))
        row = cursor.fetchone()
        assert row is not None
        assert row["title"] == "Test bug"
        db.close()

    def test_get_entry_by_id(self, temp_db_path: Path):
        """Should retrieve entry by ID."""
        from rekall.db import Database
        from rekall.models import Entry, generate_ulid

        db = Database(temp_db_path)
        db.init()

        entry_id = generate_ulid()
        entry = Entry(id=entry_id, title="Test", type="pattern")
        db.add(entry)

        retrieved = db.get(entry_id)
        assert retrieved is not None
        assert retrieved.id == entry_id
        assert retrieved.title == "Test"
        db.close()

    def test_get_entry_not_found(self, temp_db_path: Path):
        """Should return None for non-existent ID."""
        from rekall.db import Database

        db = Database(temp_db_path)
        db.init()

        result = db.get("nonexistent")
        assert result is None
        db.close()

    def test_update_entry(self, temp_db_path: Path):
        """Should update existing entry."""
        from rekall.db import Database
        from rekall.models import Entry, generate_ulid

        db = Database(temp_db_path)
        db.init()

        entry = Entry(id=generate_ulid(), title="Original", type="bug")
        db.add(entry)

        entry.title = "Updated"
        entry.content = "New content"
        db.update(entry)

        retrieved = db.get(entry.id)
        assert retrieved.title == "Updated"
        assert retrieved.content == "New content"
        db.close()

    def test_delete_entry(self, temp_db_path: Path):
        """Should delete entry."""
        from rekall.db import Database
        from rekall.models import Entry, generate_ulid

        db = Database(temp_db_path)
        db.init()

        entry = Entry(id=generate_ulid(), title="To delete", type="bug")
        db.add(entry)

        db.delete(entry.id)

        result = db.get(entry.id)
        assert result is None
        db.close()

    def test_add_entry_with_tags(self, temp_db_path: Path):
        """Should store tags in separate table."""
        from rekall.db import Database
        from rekall.models import Entry, generate_ulid

        db = Database(temp_db_path)
        db.init()

        entry = Entry(
            id=generate_ulid(), title="Tagged", type="pattern", tags=["python", "best-practice"]
        )
        db.add(entry)

        cursor = db.conn.execute(
            "SELECT tag FROM tags WHERE entry_id = ? ORDER BY tag", (entry.id,)
        )
        tags = [row[0] for row in cursor.fetchall()]
        assert tags == ["best-practice", "python"]
        db.close()


class TestFTS5:
    """Tests for FTS5 full-text search (T012)."""

    def test_fts5_index_on_insert(self, temp_db_path: Path):
        """FTS5 index should be updated on insert."""
        from rekall.db import Database
        from rekall.models import Entry, generate_ulid

        db = Database(temp_db_path)
        db.init()

        entry = Entry(
            id=generate_ulid(),
            title="Circular import fix",
            type="bug",
            content="Fixed React circular import issue",
        )
        db.add(entry)

        # Check FTS5 table has the entry
        cursor = db.conn.execute(
            "SELECT id FROM entries_fts WHERE entries_fts MATCH 'circular'"
        )
        results = cursor.fetchall()
        assert len(results) == 1
        assert results[0][0] == entry.id
        db.close()

    def test_search_match_title(self, temp_db_path: Path):
        """Search should match terms in title."""
        from rekall.db import Database
        from rekall.models import Entry, generate_ulid

        db = Database(temp_db_path)
        db.init()

        entry = Entry(id=generate_ulid(), title="React hooks tutorial", type="reference")
        db.add(entry)

        results = db.search("hooks")
        assert len(results) == 1
        assert results[0].entry.id == entry.id
        db.close()

    def test_search_match_content(self, temp_db_path: Path):
        """Search should match terms in content."""
        from rekall.db import Database
        from rekall.models import Entry, generate_ulid

        db = Database(temp_db_path)
        db.init()

        entry = Entry(
            id=generate_ulid(),
            title="Bug fix",
            type="bug",
            content="The useState hook was causing infinite loop",
        )
        db.add(entry)

        results = db.search("infinite loop")
        assert len(results) == 1
        db.close()

    def test_search_returns_ranked(self, temp_db_path: Path):
        """Search should return results ranked by relevance."""
        from rekall.db import Database
        from rekall.models import Entry, generate_ulid

        db = Database(temp_db_path)
        db.init()

        # Entry with "cache" in title (more relevant)
        entry1 = Entry(id=generate_ulid(), title="Cache optimization", type="pattern")
        db.add(entry1)

        # Entry with "cache" in content (less relevant)
        entry2 = Entry(
            id=generate_ulid(),
            title="Performance tip",
            type="pattern",
            content="Use cache for better performance",
        )
        db.add(entry2)

        results = db.search("cache")
        assert len(results) == 2
        # First result should be more relevant (title match)
        assert results[0].rank <= results[1].rank
        db.close()

    def test_search_no_results(self, temp_db_path: Path):
        """Search should return empty list when no match."""
        from rekall.db import Database
        from rekall.models import Entry, generate_ulid

        db = Database(temp_db_path)
        db.init()

        entry = Entry(id=generate_ulid(), title="Python tutorial", type="reference")
        db.add(entry)

        results = db.search("javascript")
        assert len(results) == 0
        db.close()

    def test_search_stemming(self, temp_db_path: Path):
        """Search should use Porter stemming (running -> run)."""
        from rekall.db import Database
        from rekall.models import Entry, generate_ulid

        db = Database(temp_db_path)
        db.init()

        entry = Entry(id=generate_ulid(), title="Running tests", type="config")
        db.add(entry)

        # Should match "run" due to Porter stemming
        results = db.search("run")
        assert len(results) == 1
        db.close()

    def test_search_excludes_obsolete(self, temp_db_path: Path):
        """Search should exclude obsolete entries by default."""
        from rekall.db import Database
        from rekall.models import Entry, generate_ulid

        db = Database(temp_db_path)
        db.init()

        entry = Entry(
            id=generate_ulid(), title="Old pattern", type="pattern", status="obsolete"
        )
        db.add(entry)

        results = db.search("pattern")
        assert len(results) == 0
        db.close()
