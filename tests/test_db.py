"""Tests for Rekall database (TDD - written before implementation)."""

from pathlib import Path

import pytest


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


class TestSchemaV3:
    """Tests for schema v3 migration (embeddings, suggestions, metadata)."""

    def test_migration_creates_embeddings_table(self, temp_db_path: Path):
        """Migration v3 should create embeddings table."""
        from rekall.db import Database

        db = Database(temp_db_path)
        db.init()

        cursor = db.conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='embeddings'"
        )
        assert cursor.fetchone() is not None
        db.close()

    def test_migration_creates_suggestions_table(self, temp_db_path: Path):
        """Migration v3 should create suggestions table."""
        from rekall.db import Database

        db = Database(temp_db_path)
        db.init()

        cursor = db.conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='suggestions'"
        )
        assert cursor.fetchone() is not None
        db.close()

    def test_migration_creates_metadata_table(self, temp_db_path: Path):
        """Migration v3 should create metadata table."""
        from rekall.db import Database

        db = Database(temp_db_path)
        db.init()

        cursor = db.conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='metadata'"
        )
        assert cursor.fetchone() is not None
        db.close()

    def test_schema_version_is_current(self, temp_db_path: Path):
        """Schema version should be current after migration."""
        from rekall.db import CURRENT_SCHEMA_VERSION, Database

        db = Database(temp_db_path)
        db.init()

        version = db.get_schema_version()
        assert version == CURRENT_SCHEMA_VERSION
        db.close()


class TestEmbeddingsCRUD:
    """Tests for embedding CRUD operations (Phase 0)."""

    def test_add_embedding(self, temp_db_path: Path):
        """Should store embedding in database."""
        import numpy as np

        from rekall.db import Database
        from rekall.models import Embedding, Entry, generate_ulid

        db = Database(temp_db_path)
        db.init()

        # Create entry first
        entry = Entry(id=generate_ulid(), title="Test", type="bug")
        db.add(entry)

        # Create and add embedding
        vector = np.random.randn(384).astype(np.float32)
        embedding = Embedding.from_numpy(
            entry_id=entry.id,
            embedding_type="summary",
            array=vector,
            model_name="test-model",
        )
        db.add_embedding(embedding)

        # Verify stored
        cursor = db.conn.execute(
            "SELECT * FROM embeddings WHERE entry_id = ?", (entry.id,)
        )
        row = cursor.fetchone()
        assert row is not None
        assert row["embedding_type"] == "summary"
        assert row["dimensions"] == 384
        db.close()

    def test_get_embedding(self, temp_db_path: Path):
        """Should retrieve embedding by entry_id and type."""
        import numpy as np

        from rekall.db import Database
        from rekall.models import Embedding, Entry, generate_ulid

        db = Database(temp_db_path)
        db.init()

        entry = Entry(id=generate_ulid(), title="Test", type="bug")
        db.add(entry)

        vector = np.random.randn(384).astype(np.float32)
        embedding = Embedding.from_numpy(
            entry_id=entry.id,
            embedding_type="summary",
            array=vector,
            model_name="test-model",
        )
        db.add_embedding(embedding)

        retrieved = db.get_embedding(entry.id, "summary")
        assert retrieved is not None
        assert retrieved.embedding_type == "summary"
        assert retrieved.dimensions == 384

        # Verify vector content
        retrieved_vec = retrieved.to_numpy()
        np.testing.assert_array_almost_equal(retrieved_vec, vector)
        db.close()

    def test_get_embeddings_multiple(self, temp_db_path: Path):
        """Should retrieve all embeddings for an entry."""
        import numpy as np

        from rekall.db import Database
        from rekall.models import Embedding, Entry, generate_ulid

        db = Database(temp_db_path)
        db.init()

        entry = Entry(id=generate_ulid(), title="Test", type="bug")
        db.add(entry)

        # Add summary and context embeddings
        for emb_type in ("summary", "context"):
            vector = np.random.randn(384).astype(np.float32)
            embedding = Embedding.from_numpy(
                entry_id=entry.id,
                embedding_type=emb_type,
                array=vector,
                model_name="test-model",
            )
            db.add_embedding(embedding)

        embeddings = db.get_embeddings(entry.id)
        assert len(embeddings) == 2
        types = {e.embedding_type for e in embeddings}
        assert types == {"summary", "context"}
        db.close()

    def test_delete_embedding(self, temp_db_path: Path):
        """Should delete embedding."""
        import numpy as np

        from rekall.db import Database
        from rekall.models import Embedding, Entry, generate_ulid

        db = Database(temp_db_path)
        db.init()

        entry = Entry(id=generate_ulid(), title="Test", type="bug")
        db.add(entry)

        vector = np.random.randn(384).astype(np.float32)
        embedding = Embedding.from_numpy(
            entry_id=entry.id,
            embedding_type="summary",
            array=vector,
            model_name="test-model",
        )
        db.add_embedding(embedding)

        deleted = db.delete_embedding(entry.id, "summary")
        assert deleted == 1

        retrieved = db.get_embedding(entry.id, "summary")
        assert retrieved is None
        db.close()

    def test_count_embeddings(self, temp_db_path: Path):
        """Should count total embeddings."""
        import numpy as np

        from rekall.db import Database
        from rekall.models import Embedding, Entry, generate_ulid

        db = Database(temp_db_path)
        db.init()

        assert db.count_embeddings() == 0

        # Add entries with embeddings
        for _ in range(3):
            entry = Entry(id=generate_ulid(), title="Test", type="bug")
            db.add(entry)
            vector = np.random.randn(384).astype(np.float32)
            embedding = Embedding.from_numpy(
                entry_id=entry.id,
                embedding_type="summary",
                array=vector,
                model_name="test-model",
            )
            db.add_embedding(embedding)

        assert db.count_embeddings() == 3
        db.close()

    def test_get_entries_without_embeddings(self, temp_db_path: Path):
        """Should find entries missing embeddings."""
        import numpy as np

        from rekall.db import Database
        from rekall.models import Embedding, Entry, generate_ulid

        db = Database(temp_db_path)
        db.init()

        # Create 3 entries
        entries = []
        for i in range(3):
            entry = Entry(id=generate_ulid(), title=f"Test {i}", type="bug")
            db.add(entry)
            entries.append(entry)

        # Add embedding to only the first entry
        vector = np.random.randn(384).astype(np.float32)
        embedding = Embedding.from_numpy(
            entry_id=entries[0].id,
            embedding_type="summary",
            array=vector,
            model_name="test-model",
        )
        db.add_embedding(embedding)

        # Should return 2 entries without embeddings
        missing = db.get_entries_without_embeddings("summary")
        assert len(missing) == 2
        missing_ids = {e.id for e in missing}
        assert entries[1].id in missing_ids
        assert entries[2].id in missing_ids
        db.close()


class TestSuggestionsCRUD:
    """Tests for suggestion CRUD operations (Phase 0)."""

    def test_add_suggestion(self, temp_db_path: Path):
        """Should store suggestion in database."""
        from rekall.db import Database
        from rekall.models import Entry, Suggestion, generate_ulid

        db = Database(temp_db_path)
        db.init()

        # Create entries
        entry1 = Entry(id=generate_ulid(), title="Test 1", type="bug")
        entry2 = Entry(id=generate_ulid(), title="Test 2", type="bug")
        db.add(entry1)
        db.add(entry2)

        suggestion = Suggestion(
            id=generate_ulid(),
            suggestion_type="link",
            entry_ids=[entry1.id, entry2.id],
            score=0.85,
            reason="Similar bugs",
        )
        db.add_suggestion(suggestion)

        cursor = db.conn.execute("SELECT * FROM suggestions WHERE id = ?", (suggestion.id,))
        row = cursor.fetchone()
        assert row is not None
        assert row["suggestion_type"] == "link"
        assert row["score"] == 0.85
        db.close()

    def test_get_suggestion(self, temp_db_path: Path):
        """Should retrieve suggestion by ID."""
        from rekall.db import Database
        from rekall.models import Entry, Suggestion, generate_ulid

        db = Database(temp_db_path)
        db.init()

        entry1 = Entry(id=generate_ulid(), title="Test 1", type="bug")
        entry2 = Entry(id=generate_ulid(), title="Test 2", type="bug")
        db.add(entry1)
        db.add(entry2)

        suggestion = Suggestion(
            id=generate_ulid(),
            suggestion_type="link",
            entry_ids=[entry1.id, entry2.id],
            score=0.85,
            reason="Similar bugs",
        )
        db.add_suggestion(suggestion)

        retrieved = db.get_suggestion(suggestion.id)
        assert retrieved is not None
        assert retrieved.entry_ids == [entry1.id, entry2.id]
        assert retrieved.score == 0.85
        db.close()

    def test_get_suggestions_filtered(self, temp_db_path: Path):
        """Should filter suggestions by status and type."""
        from rekall.db import Database
        from rekall.models import Entry, Suggestion, generate_ulid

        db = Database(temp_db_path)
        db.init()

        # Create entries
        entries = [Entry(id=generate_ulid(), title=f"Test {i}", type="bug") for i in range(5)]
        for e in entries:
            db.add(e)

        # Create link suggestion (pending)
        s1 = Suggestion(
            id=generate_ulid(),
            suggestion_type="link",
            entry_ids=[entries[0].id, entries[1].id],
            score=0.8,
        )
        db.add_suggestion(s1)

        # Create generalize suggestion (pending)
        s2 = Suggestion(
            id=generate_ulid(),
            suggestion_type="generalize",
            entry_ids=[entries[2].id, entries[3].id, entries[4].id],
            score=0.82,
        )
        db.add_suggestion(s2)

        # Filter by type
        links = db.get_suggestions(suggestion_type="link")
        assert len(links) == 1
        assert links[0].suggestion_type == "link"

        # Filter by status
        pending = db.get_suggestions(status="pending")
        assert len(pending) == 2
        db.close()

    def test_update_suggestion_status(self, temp_db_path: Path):
        """Should update suggestion status."""
        from rekall.db import Database
        from rekall.models import Entry, Suggestion, generate_ulid

        db = Database(temp_db_path)
        db.init()

        entry1 = Entry(id=generate_ulid(), title="Test 1", type="bug")
        entry2 = Entry(id=generate_ulid(), title="Test 2", type="bug")
        db.add(entry1)
        db.add(entry2)

        suggestion = Suggestion(
            id=generate_ulid(),
            suggestion_type="link",
            entry_ids=[entry1.id, entry2.id],
            score=0.85,
        )
        db.add_suggestion(suggestion)

        # Accept the suggestion
        result = db.update_suggestion_status(suggestion.id, "accepted")
        assert result is True

        retrieved = db.get_suggestion(suggestion.id)
        assert retrieved.status == "accepted"
        assert retrieved.resolved_at is not None
        db.close()


class TestMetadataCRUD:
    """Tests for metadata CRUD operations (Phase 0)."""

    def test_set_and_get_metadata(self, temp_db_path: Path):
        """Should store and retrieve metadata."""
        from rekall.db import Database

        db = Database(temp_db_path)
        db.init()

        db.set_metadata("last_weekly_check", "2025-12-09")
        value = db.get_metadata("last_weekly_check")
        assert value == "2025-12-09"
        db.close()

    def test_get_metadata_not_found(self, temp_db_path: Path):
        """Should return None for missing key."""
        from rekall.db import Database

        db = Database(temp_db_path)
        db.init()

        value = db.get_metadata("nonexistent")
        assert value is None
        db.close()

    def test_set_metadata_upsert(self, temp_db_path: Path):
        """Should update existing metadata."""
        from rekall.db import Database

        db = Database(temp_db_path)
        db.init()

        db.set_metadata("key", "value1")
        db.set_metadata("key", "value2")

        value = db.get_metadata("key")
        assert value == "value2"
        db.close()

    def test_delete_metadata(self, temp_db_path: Path):
        """Should delete metadata."""
        from rekall.db import Database

        db = Database(temp_db_path)
        db.init()

        db.set_metadata("key", "value")
        result = db.delete_metadata("key")
        assert result is True

        value = db.get_metadata("key")
        assert value is None
        db.close()

    def test_delete_metadata_not_found(self, temp_db_path: Path):
        """Should return False for missing key."""
        from rekall.db import Database

        db = Database(temp_db_path)
        db.init()

        result = db.delete_metadata("nonexistent")
        assert result is False
        db.close()


class TestContextCompression:
    """Tests for context compression (Phase 10)."""

    def test_store_and_get_context(self, temp_db_path: Path):
        """Should compress, store, and decompress context."""
        from rekall.db import Database
        from rekall.models import Entry, generate_ulid

        db = Database(temp_db_path)
        db.init()

        entry = Entry(
            id=generate_ulid(),
            title="Test entry",
            type="bug",
            content="Test content",
        )
        db.add(entry)

        # Store context
        context = "This is a test conversation context about a bug fix."
        db.store_context(entry.id, context)

        # Retrieve context
        retrieved = db.get_context(entry.id)
        assert retrieved == context
        db.close()

    def test_get_context_not_stored(self, temp_db_path: Path):
        """Should return None when no context stored."""
        from rekall.db import Database
        from rekall.models import Entry, generate_ulid

        db = Database(temp_db_path)
        db.init()

        entry = Entry(
            id=generate_ulid(),
            title="Test entry",
            type="bug",
        )
        db.add(entry)

        context = db.get_context(entry.id)
        assert context is None
        db.close()

    def test_get_contexts_for_verification(self, temp_db_path: Path):
        """Should retrieve multiple contexts for verification."""
        from rekall.db import Database
        from rekall.models import Entry, generate_ulid

        db = Database(temp_db_path)
        db.init()

        # Create entries with and without context
        entry1 = Entry(id=generate_ulid(), title="Entry 1", type="bug")
        entry2 = Entry(id=generate_ulid(), title="Entry 2", type="pattern")
        entry3 = Entry(id=generate_ulid(), title="Entry 3", type="decision")
        db.add(entry1)
        db.add(entry2)
        db.add(entry3)

        db.store_context(entry1.id, "Context for entry 1")
        db.store_context(entry3.id, "Context for entry 3")

        # Get contexts
        contexts = db.get_contexts_for_verification([entry1.id, entry2.id, entry3.id])

        assert contexts[entry1.id] == "Context for entry 1"
        assert contexts[entry2.id] is None
        assert contexts[entry3.id] == "Context for entry 3"
        db.close()

    def test_compression_ratio(self, temp_db_path: Path):
        """Compression should significantly reduce size for text."""
        from rekall.db import compress_context, decompress_context

        # Typical conversation context
        context = """
        User asked about implementing a retry mechanism for API calls.
        We discussed exponential backoff with jitter.
        The solution uses a decorator pattern with configurable max retries.
        Code was added to src/utils/retry.py with tests in tests/test_retry.py.
        """ * 10  # ~1500 chars

        compressed = compress_context(context)
        decompressed = decompress_context(compressed)

        # Verify round-trip
        assert decompressed == context

        # Verify compression (should be at least 50% smaller for text)
        original_size = len(context.encode("utf-8"))
        compressed_size = len(compressed)
        compression_ratio = 1 - (compressed_size / original_size)

        assert compression_ratio > 0.5, f"Expected >50% compression, got {compression_ratio:.0%}"


class TestLinksCRUD:
    """Tests for link CRUD operations with reason field."""

    def test_add_link_with_reason(self, temp_db_path: Path):
        """Should store and retrieve link with reason."""
        from rekall.db import Database
        from rekall.models import Entry, generate_ulid

        db = Database(temp_db_path)
        db.init()

        # Create two entries
        entry1 = Entry(id=generate_ulid(), title="Bug fix", type="bug")
        entry2 = Entry(id=generate_ulid(), title="Root cause bug", type="bug")
        db.add(entry1)
        db.add(entry2)

        # Create link with reason
        reason = "This fix addresses the root cause identified in entry2"
        link = db.add_link(
            entry1.id, entry2.id, "derived_from", reason=reason
        )

        assert link.reason == reason
        assert link.relation_type == "derived_from"

        # Verify retrieval
        links = db.get_links(entry1.id, direction="outgoing")
        assert len(links) == 1
        assert links[0].reason == reason
        db.close()

    def test_add_link_without_reason(self, temp_db_path: Path):
        """Should allow link without reason (backwards compatible)."""
        from rekall.db import Database
        from rekall.models import Entry, generate_ulid

        db = Database(temp_db_path)
        db.init()

        # Create two entries
        entry1 = Entry(id=generate_ulid(), title="Entry A", type="pattern")
        entry2 = Entry(id=generate_ulid(), title="Entry B", type="pattern")
        db.add(entry1)
        db.add(entry2)

        # Create link without reason
        link = db.add_link(entry1.id, entry2.id, "related")

        assert link.reason is None

        # Verify retrieval
        links = db.get_links(entry1.id)
        assert len(links) == 1
        assert links[0].reason is None
        db.close()

    def test_get_links_incoming_with_reason(self, temp_db_path: Path):
        """Should retrieve incoming links with reason."""
        from rekall.db import Database
        from rekall.models import Entry, generate_ulid

        db = Database(temp_db_path)
        db.init()

        # Create entries
        source = Entry(id=generate_ulid(), title="Source", type="decision")
        target = Entry(id=generate_ulid(), title="Target", type="pattern")
        db.add(source)
        db.add(target)

        # Create link
        reason = "Decision led to this pattern"
        db.add_link(source.id, target.id, "supersedes", reason=reason)

        # Get incoming links to target
        links = db.get_links(target.id, direction="incoming")
        assert len(links) == 1
        assert links[0].source_id == source.id
        assert links[0].reason == reason
        db.close()


class TestStructuredContextDB:
    """Tests for structured context DB methods (Feature 006)."""

    def test_store_and_get_structured_context(self, temp_db_path: Path):
        """Should store and retrieve structured context."""
        from rekall.db import Database
        from rekall.models import Entry, StructuredContext, generate_ulid

        db = Database(temp_db_path)
        db.init()

        # Create entry
        entry = Entry(id=generate_ulid(), title="Fix 504 timeout", type="bug")
        db.add(entry)

        # Create and store context
        ctx = StructuredContext(
            situation="API timeout sur requêtes > 30s",
            solution="nginx proxy_read_timeout 120s",
            trigger_keywords=["504", "nginx", "timeout"],
            what_failed="Client-side timeout didn't help",
        )
        db.store_structured_context(entry.id, ctx)

        # Retrieve and verify
        retrieved = db.get_structured_context(entry.id)
        assert retrieved is not None
        assert retrieved.situation == ctx.situation
        assert retrieved.solution == ctx.solution
        assert retrieved.trigger_keywords == ctx.trigger_keywords
        assert retrieved.what_failed == ctx.what_failed
        db.close()

    def test_get_structured_context_not_found(self, temp_db_path: Path):
        """Should return None for entry without context."""
        from rekall.db import Database
        from rekall.models import Entry, generate_ulid

        db = Database(temp_db_path)
        db.init()

        # Create entry without context
        entry = Entry(id=generate_ulid(), title="No context", type="pattern")
        db.add(entry)

        # Should return None
        retrieved = db.get_structured_context(entry.id)
        assert retrieved is None
        db.close()

    def test_search_by_keywords_finds_matches(self, temp_db_path: Path):
        """Should find entries by keyword search."""
        from rekall.db import Database
        from rekall.models import Entry, StructuredContext, generate_ulid

        db = Database(temp_db_path)
        db.init()

        # Create entries with different keywords
        entry1 = Entry(id=generate_ulid(), title="Nginx fix", type="bug")
        entry2 = Entry(id=generate_ulid(), title="Redis cache", type="pattern")
        entry3 = Entry(id=generate_ulid(), title="Another nginx", type="config")
        db.add(entry1)
        db.add(entry2)
        db.add(entry3)

        ctx1 = StructuredContext(
            situation="Nginx timeout issue",
            solution="Increase timeout value",
            trigger_keywords=["nginx", "timeout", "504"],
        )
        ctx2 = StructuredContext(
            situation="Redis connection issues",
            solution="Use connection pooling",
            trigger_keywords=["redis", "connection", "pool"],
        )
        ctx3 = StructuredContext(
            situation="Nginx config problem",
            solution="Fix config syntax",
            trigger_keywords=["nginx", "config", "syntax"],
        )
        db.store_structured_context(entry1.id, ctx1)
        db.store_structured_context(entry2.id, ctx2)
        db.store_structured_context(entry3.id, ctx3)

        # Search for nginx - should find 2
        results = db.search_by_keywords(["nginx"])
        assert len(results) == 2
        result_ids = {e.id for e in results}
        assert entry1.id in result_ids
        assert entry3.id in result_ids

        # Search for redis - should find 1
        results = db.search_by_keywords(["redis"])
        assert len(results) == 1
        assert results[0].id == entry2.id

        # Search for timeout or redis - should find 2
        results = db.search_by_keywords(["timeout", "redis"])
        assert len(results) == 2
        db.close()

    def test_search_by_keywords_empty_list(self, temp_db_path: Path):
        """Should return empty for empty keyword list."""
        from rekall.db import Database

        db = Database(temp_db_path)
        db.init()

        results = db.search_by_keywords([])
        assert results == []
        db.close()

    def test_search_by_keywords_case_insensitive(self, temp_db_path: Path):
        """Search should be case-insensitive."""
        from rekall.db import Database
        from rekall.models import Entry, StructuredContext, generate_ulid

        db = Database(temp_db_path)
        db.init()

        entry = Entry(id=generate_ulid(), title="Test entry", type="bug")
        db.add(entry)

        ctx = StructuredContext(
            situation="Test situation here",
            solution="Test solution here",
            trigger_keywords=["nginx", "timeout"],
        )
        db.store_structured_context(entry.id, ctx)

        # Search with different cases
        assert len(db.search_by_keywords(["NGINX"])) == 1
        assert len(db.search_by_keywords(["Nginx"])) == 1
        assert len(db.search_by_keywords(["nginx"])) == 1
        db.close()

    def test_get_entries_with_structured_context(self, temp_db_path: Path):
        """Should get all entries with structured context."""
        from rekall.db import Database
        from rekall.models import Entry, StructuredContext, generate_ulid

        db = Database(temp_db_path)
        db.init()

        # Create entries - some with context, some without
        entry1 = Entry(id=generate_ulid(), title="With context", type="bug")
        entry2 = Entry(id=generate_ulid(), title="No context", type="pattern")
        entry3 = Entry(id=generate_ulid(), title="Also with context", type="config")
        db.add(entry1)
        db.add(entry2)
        db.add(entry3)

        ctx1 = StructuredContext(
            situation="Test situation 1",
            solution="Test solution 1",
            trigger_keywords=["test1"],
        )
        ctx3 = StructuredContext(
            situation="Test situation 3",
            solution="Test solution 3",
            trigger_keywords=["test3"],
        )
        db.store_structured_context(entry1.id, ctx1)
        db.store_structured_context(entry3.id, ctx3)

        # Get entries with context
        results = db.get_entries_with_structured_context()
        assert len(results) == 2

        entry_ids = {e.id for e, _ in results}
        assert entry1.id in entry_ids
        assert entry3.id in entry_ids
        assert entry2.id not in entry_ids

        # Verify context is returned with entries
        for entry, ctx in results:
            assert ctx is not None
            assert ctx.situation.startswith("Test situation")
        db.close()

    def test_migration_v6_adds_column(self, temp_db_path: Path):
        """Migration v6 should add context_structured column."""
        from rekall.db import Database

        db = Database(temp_db_path)
        db.init()

        # Check column exists
        cursor = db.conn.execute("PRAGMA table_info(entries)")
        columns = {row[1] for row in cursor.fetchall()}
        assert "context_structured" in columns
        db.close()


# ============================================================================
# Feature 007: Context Compression Tests (Phase 3)
# ============================================================================


class TestContextCompressedStorage:
    """Tests for compressed context storage (v7)."""

    def test_migration_v7_adds_context_blob(self, temp_db_path: Path):
        """Migration v7 should add context_blob column."""
        from rekall.db import Database

        db = Database(temp_db_path)
        db.init()

        # Check context_blob column exists
        cursor = db.conn.execute("PRAGMA table_info(entries)")
        columns = {row[1] for row in cursor.fetchall()}
        assert "context_blob" in columns
        db.close()

    def test_migration_v7_creates_keywords_table(self, temp_db_path: Path):
        """Migration v7 should create context_keywords table."""
        from rekall.db import Database

        db = Database(temp_db_path)
        db.init()

        # Check table exists
        cursor = db.conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='context_keywords'"
        )
        assert cursor.fetchone() is not None
        db.close()

    def test_store_context_compresses_data(self, temp_db_path: Path):
        """Storing structured context should compress into context_blob."""
        from rekall.db import Database
        from rekall.models import Entry, StructuredContext, generate_ulid

        db = Database(temp_db_path)
        db.init()

        entry = Entry(id=generate_ulid(), title="Test compression", type="bug")
        db.add(entry)

        ctx = StructuredContext(
            situation="This is a test situation with some text",
            solution="This is the solution with some details",
            trigger_keywords=["test", "compression", "zlib"],
        )
        db.store_structured_context(entry.id, ctx)

        # Verify context_blob is set and compressed
        row = db.conn.execute(
            "SELECT context_blob, context_structured FROM entries WHERE id = ?",
            (entry.id,),
        ).fetchone()

        assert row["context_blob"] is not None
        assert len(row["context_blob"]) < len(row["context_structured"])  # Compressed
        db.close()

    def test_store_context_indexes_keywords(self, temp_db_path: Path):
        """Storing structured context should index keywords."""
        from rekall.db import Database
        from rekall.models import Entry, StructuredContext, generate_ulid

        db = Database(temp_db_path)
        db.init()

        entry = Entry(id=generate_ulid(), title="Test indexing", type="bug")
        db.add(entry)

        ctx = StructuredContext(
            situation="Test situation",
            solution="Test solution",
            trigger_keywords=["keyword1", "Keyword2", "KEYWORD3"],
        )
        db.store_structured_context(entry.id, ctx)

        # Verify keywords are indexed (lowercased)
        rows = db.conn.execute(
            "SELECT keyword FROM context_keywords WHERE entry_id = ?",
            (entry.id,),
        ).fetchall()
        keywords = {row[0] for row in rows}

        assert "keyword1" in keywords
        assert "keyword2" in keywords  # Lowercased
        assert "keyword3" in keywords  # Lowercased
        db.close()

    def test_get_context_decompresses(self, temp_db_path: Path):
        """Getting structured context should decompress from blob."""
        from rekall.db import Database
        from rekall.models import Entry, StructuredContext, generate_ulid

        db = Database(temp_db_path)
        db.init()

        entry = Entry(id=generate_ulid(), title="Test decompression", type="bug")
        db.add(entry)

        original_ctx = StructuredContext(
            situation="Original situation text",
            solution="Original solution text",
            trigger_keywords=["original", "test"],
        )
        db.store_structured_context(entry.id, original_ctx)

        # Get it back
        retrieved = db.get_structured_context(entry.id)

        assert retrieved is not None
        assert retrieved.situation == original_ctx.situation
        assert retrieved.solution == original_ctx.solution
        assert retrieved.trigger_keywords == original_ctx.trigger_keywords
        db.close()

    def test_search_by_keywords_uses_index(self, temp_db_path: Path):
        """search_by_keywords should use the keywords index table."""
        from rekall.db import Database
        from rekall.models import Entry, StructuredContext, generate_ulid

        db = Database(temp_db_path)
        db.init()

        # Create entries with different keywords
        entry1 = Entry(id=generate_ulid(), title="Entry 1", type="bug")
        entry2 = Entry(id=generate_ulid(), title="Entry 2", type="pattern")
        db.add(entry1)
        db.add(entry2)

        ctx1 = StructuredContext(
            situation="Test 1",
            solution="Solution 1",
            trigger_keywords=["python", "django"],
        )
        ctx2 = StructuredContext(
            situation="Test 2",
            solution="Solution 2",
            trigger_keywords=["javascript", "react"],
        )
        db.store_structured_context(entry1.id, ctx1)
        db.store_structured_context(entry2.id, ctx2)

        # Search for python
        results = db.search_by_keywords(["python"])
        assert len(results) == 1
        assert results[0].id == entry1.id

        # Search for react
        results = db.search_by_keywords(["react"])
        assert len(results) == 1
        assert results[0].id == entry2.id

        # Search for both
        results = db.search_by_keywords(["python", "react"])
        assert len(results) == 2
        db.close()


class TestContextDataMigration:
    """Tests for context data migration to compressed format."""

    def test_migrate_to_compressed_context(self, temp_db_path: Path):
        """Should migrate context_structured to context_blob."""
        from rekall.db import Database
        from rekall.models import Entry, StructuredContext, generate_ulid

        db = Database(temp_db_path)
        db.init()

        # Create entry with context_structured only (simulating v6 data)
        entry = Entry(id=generate_ulid(), title="Legacy entry", type="bug")
        db.add(entry)

        ctx = StructuredContext(
            situation="Legacy situation",
            solution="Legacy solution",
            trigger_keywords=["legacy", "test"],
        )

        # Manually insert into context_structured only (bypass store_structured_context)
        db.conn.execute(
            "UPDATE entries SET context_structured = ?, context_blob = NULL WHERE id = ?",
            (ctx.to_json(), entry.id),
        )
        db.conn.commit()

        # Verify it needs migration
        assert db.count_entries_without_context_blob() == 1

        # Run migration
        migrated, keywords = db.migrate_to_compressed_context()
        assert migrated == 1
        assert keywords == 2  # "legacy", "test"

        # Verify context_blob is now set
        assert db.count_entries_without_context_blob() == 0

        # Verify we can still read it
        retrieved = db.get_structured_context(entry.id)
        assert retrieved is not None
        assert retrieved.situation == "Legacy situation"
        db.close()

    def test_count_entries_without_context_blob(self, temp_db_path: Path):
        """Should count entries needing migration."""
        from rekall.db import Database
        from rekall.models import Entry, StructuredContext, generate_ulid

        db = Database(temp_db_path)
        db.init()

        # Create 3 entries
        for i in range(3):
            entry = Entry(id=generate_ulid(), title=f"Entry {i}", type="bug")
            db.add(entry)
            ctx = StructuredContext(
                situation=f"Situation {i}",
                solution=f"Solution {i}",
                trigger_keywords=[f"key{i}"],
            )
            # Store normally (will set context_blob)
            db.store_structured_context(entry.id, ctx)

        # All should be migrated (context_blob set)
        assert db.count_entries_without_context_blob() == 0

        # Manually clear context_blob for 2 entries (simulate v6 data)
        # SQLite doesn't support LIMIT in UPDATE, so use subquery
        db.conn.execute(
            """UPDATE entries SET context_blob = NULL WHERE id IN (
                SELECT id FROM entries WHERE context_structured IS NOT NULL LIMIT 2
            )"""
        )
        db.conn.commit()

        # Now 2 should need migration
        assert db.count_entries_without_context_blob() == 2
        db.close()


# ============================================================================
# Feature 009: Sources Integration Tests (Migration v8)
# ============================================================================


class TestMigrationV8Sources:
    """Tests for schema v8 migration (sources, entry_sources tables)."""

    def test_migration_v8_creates_sources_table(self, temp_db_path: Path):
        """Migration v8 should create sources table with correct schema."""
        from rekall.db import Database

        db = Database(temp_db_path)
        db.init()

        # Check table exists
        cursor = db.conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='sources'"
        )
        assert cursor.fetchone() is not None

        # Check columns
        cursor = db.conn.execute("PRAGMA table_info(sources)")
        columns = {row[1]: row[2] for row in cursor.fetchall()}

        assert "id" in columns
        assert "domain" in columns
        assert "url_pattern" in columns
        assert "usage_count" in columns
        assert "last_used" in columns
        assert "personal_score" in columns
        assert "reliability" in columns
        assert "decay_rate" in columns
        assert "last_verified" in columns
        assert "status" in columns
        assert "created_at" in columns
        db.close()

    def test_migration_v8_creates_entry_sources_table(self, temp_db_path: Path):
        """Migration v8 should create entry_sources table with correct schema."""
        from rekall.db import Database

        db = Database(temp_db_path)
        db.init()

        # Check table exists
        cursor = db.conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='entry_sources'"
        )
        assert cursor.fetchone() is not None

        # Check columns
        cursor = db.conn.execute("PRAGMA table_info(entry_sources)")
        columns = {row[1]: row[2] for row in cursor.fetchall()}

        assert "id" in columns
        assert "entry_id" in columns
        assert "source_id" in columns
        assert "source_type" in columns
        assert "source_ref" in columns
        assert "note" in columns
        assert "created_at" in columns
        db.close()

    def test_migration_v8_creates_indexes(self, temp_db_path: Path):
        """Migration v8 should create required indexes."""
        from rekall.db import Database

        db = Database(temp_db_path)
        db.init()

        # Get all indexes
        cursor = db.conn.execute(
            "SELECT name FROM sqlite_master WHERE type='index'"
        )
        indexes = {row[0] for row in cursor.fetchall()}

        # Check sources indexes
        assert "idx_sources_domain" in indexes
        assert "idx_sources_score" in indexes
        assert "idx_sources_status" in indexes

        # Check entry_sources indexes
        assert "idx_entry_sources_entry" in indexes
        assert "idx_entry_sources_source" in indexes
        assert "idx_entry_sources_type" in indexes
        db.close()

    def test_migration_v8_sources_check_constraints(self, temp_db_path: Path):
        """Migration v8 should enforce CHECK constraints on sources."""
        import sqlite3

        from rekall.db import Database

        db = Database(temp_db_path)
        db.init()

        # Try invalid reliability - should fail
        with db.conn:
            try:
                db.conn.execute(
                    """INSERT INTO sources
                       (id, domain, reliability, decay_rate, status, created_at)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    ("test1", "example.com", "X", "medium", "active", "2025-01-01")
                )
                assert False, "Should have raised constraint error"
            except sqlite3.IntegrityError:
                pass  # Expected

        # Try invalid decay_rate - should fail
        with db.conn:
            try:
                db.conn.execute(
                    """INSERT INTO sources
                       (id, domain, reliability, decay_rate, status, created_at)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    ("test2", "example.com", "A", "invalid", "active", "2025-01-01")
                )
                assert False, "Should have raised constraint error"
            except sqlite3.IntegrityError:
                pass  # Expected

        # Try invalid status - should fail
        with db.conn:
            try:
                db.conn.execute(
                    """INSERT INTO sources
                       (id, domain, reliability, decay_rate, status, created_at)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    ("test3", "example.com", "B", "slow", "invalid", "2025-01-01")
                )
                assert False, "Should have raised constraint error"
            except sqlite3.IntegrityError:
                pass  # Expected

        # Valid insert should work
        db.conn.execute(
            """INSERT INTO sources
               (id, domain, reliability, decay_rate, status, created_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            ("test4", "example.com", "A", "fast", "active", "2025-01-01")
        )
        db.conn.commit()

        cursor = db.conn.execute("SELECT id FROM sources WHERE id = ?", ("test4",))
        assert cursor.fetchone() is not None
        db.close()

    def test_migration_v8_entry_sources_check_constraint(self, temp_db_path: Path):
        """Migration v8 should enforce CHECK constraint on entry_sources.source_type."""
        import sqlite3

        from rekall.db import Database
        from rekall.models import Entry, generate_ulid

        db = Database(temp_db_path)
        db.init()

        # Create an entry first
        entry = Entry(id=generate_ulid(), title="Test", type="bug")
        db.add(entry)

        # Try invalid source_type - should fail
        with db.conn:
            try:
                db.conn.execute(
                    """INSERT INTO entry_sources
                       (id, entry_id, source_type, source_ref, created_at)
                       VALUES (?, ?, ?, ?, ?)""",
                    ("test1", entry.id, "invalid", "test", "2025-01-01")
                )
                assert False, "Should have raised constraint error"
            except sqlite3.IntegrityError:
                pass  # Expected

        # Valid insert should work
        db.conn.execute(
            """INSERT INTO entry_sources
               (id, entry_id, source_type, source_ref, created_at)
               VALUES (?, ?, ?, ?, ?)""",
            ("test2", entry.id, "url", "https://example.com", "2025-01-01")
        )
        db.conn.commit()

        cursor = db.conn.execute("SELECT id FROM entry_sources WHERE id = ?", ("test2",))
        assert cursor.fetchone() is not None
        db.close()

    def test_migration_v8_foreign_key_entry_cascade(self, temp_db_path: Path):
        """Deleting entry should cascade delete entry_sources."""
        from rekall.db import Database
        from rekall.models import Entry, generate_ulid

        db = Database(temp_db_path)
        db.init()

        # Create entry and link
        entry = Entry(id=generate_ulid(), title="Test", type="bug")
        db.add(entry)

        db.conn.execute(
            """INSERT INTO entry_sources
               (id, entry_id, source_type, source_ref, created_at)
               VALUES (?, ?, ?, ?, ?)""",
            ("link1", entry.id, "theme", "testing", "2025-01-01")
        )
        db.conn.commit()

        # Verify link exists
        cursor = db.conn.execute("SELECT id FROM entry_sources WHERE entry_id = ?", (entry.id,))
        assert cursor.fetchone() is not None

        # Delete entry
        db.delete(entry.id)

        # Link should be cascade deleted
        cursor = db.conn.execute("SELECT id FROM entry_sources WHERE id = ?", ("link1",))
        assert cursor.fetchone() is None
        db.close()

    def test_migration_v8_foreign_key_source_set_null(self, temp_db_path: Path):
        """Deleting source should set entry_sources.source_id to NULL."""
        from rekall.db import Database
        from rekall.models import Entry, generate_ulid

        db = Database(temp_db_path)
        db.init()

        # Create entry and source
        entry = Entry(id=generate_ulid(), title="Test", type="bug")
        db.add(entry)

        source_id = generate_ulid()
        db.conn.execute(
            """INSERT INTO sources
               (id, domain, reliability, decay_rate, status, created_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (source_id, "example.com", "A", "medium", "active", "2025-01-01")
        )

        # Create link with source_id
        link_id = generate_ulid()
        db.conn.execute(
            """INSERT INTO entry_sources
               (id, entry_id, source_id, source_type, source_ref, created_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (link_id, entry.id, source_id, "url", "https://example.com/page", "2025-01-01")
        )
        db.conn.commit()

        # Verify link has source_id
        cursor = db.conn.execute(
            "SELECT source_id FROM entry_sources WHERE id = ?", (link_id,)
        )
        row = cursor.fetchone()
        assert row[0] == source_id

        # Delete source
        db.conn.execute("DELETE FROM sources WHERE id = ?", (source_id,))
        db.conn.commit()

        # Link should still exist but source_id should be NULL
        cursor = db.conn.execute(
            "SELECT source_id FROM entry_sources WHERE id = ?", (link_id,)
        )
        row = cursor.fetchone()
        assert row is not None  # Link still exists
        assert row[0] is None  # source_id is NULL
        db.close()

    def test_schema_version_is_current(self, temp_db_path: Path):
        """Schema version should match CURRENT_SCHEMA_VERSION after migration."""
        from rekall.db import CURRENT_SCHEMA_VERSION, Database

        db = Database(temp_db_path)
        db.init()

        version = db.get_schema_version()
        assert version == CURRENT_SCHEMA_VERSION  # Currently v9
        db.close()


class TestSourcesCRUD:
    """Tests for Source CRUD operations (Feature 009)."""

    def test_add_source(self, temp_db_path: Path):
        """Should add source to database."""
        from rekall.db import Database
        from rekall.models import Source

        db = Database(temp_db_path)
        db.init()

        source = Source(domain="stackoverflow.com", reliability="A")
        result = db.add_source(source)

        assert result.id != ""
        assert result.domain == "stackoverflow.com"
        assert result.reliability == "A"
        db.close()

    def test_get_source_by_id(self, temp_db_path: Path):
        """Should retrieve source by ID."""
        from rekall.db import Database
        from rekall.models import Source

        db = Database(temp_db_path)
        db.init()

        source = Source(domain="docs.python.org")
        added = db.add_source(source)

        retrieved = db.get_source(added.id)
        assert retrieved is not None
        assert retrieved.domain == "docs.python.org"
        db.close()

    def test_get_source_not_found(self, temp_db_path: Path):
        """Should return None for non-existent ID."""
        from rekall.db import Database

        db = Database(temp_db_path)
        db.init()

        result = db.get_source("nonexistent")
        assert result is None
        db.close()

    def test_get_source_by_domain(self, temp_db_path: Path):
        """Should retrieve source by domain."""
        from rekall.db import Database
        from rekall.models import Source

        db = Database(temp_db_path)
        db.init()

        source = Source(domain="github.com")
        db.add_source(source)

        retrieved = db.get_source_by_domain("github.com")
        assert retrieved is not None
        assert retrieved.domain == "github.com"
        db.close()

    def test_get_source_by_domain_with_pattern(self, temp_db_path: Path):
        """Should distinguish sources by URL pattern."""
        from rekall.db import Database
        from rekall.models import Source

        db = Database(temp_db_path)
        db.init()

        # Add two sources for same domain with different patterns
        source1 = Source(domain="github.com", url_pattern="/anthropics/*")
        source2 = Source(domain="github.com", url_pattern="/openai/*")
        db.add_source(source1)
        db.add_source(source2)

        # Should find specific pattern
        retrieved1 = db.get_source_by_domain("github.com", "/anthropics/*")
        assert retrieved1 is not None
        assert retrieved1.url_pattern == "/anthropics/*"

        retrieved2 = db.get_source_by_domain("github.com", "/openai/*")
        assert retrieved2 is not None
        assert retrieved2.url_pattern == "/openai/*"
        db.close()

    def test_update_source(self, temp_db_path: Path):
        """Should update source fields."""
        from rekall.db import Database
        from rekall.models import Source

        db = Database(temp_db_path)
        db.init()

        source = Source(domain="example.com", reliability="C")
        added = db.add_source(source)

        # Update
        added.reliability = "A"
        added.usage_count = 10
        added.personal_score = 75.5
        result = db.update_source(added)
        assert result is True

        # Verify
        retrieved = db.get_source(added.id)
        assert retrieved.reliability == "A"
        assert retrieved.usage_count == 10
        assert retrieved.personal_score == 75.5
        db.close()

    def test_delete_source(self, temp_db_path: Path):
        """Should delete source."""
        from rekall.db import Database
        from rekall.models import Source

        db = Database(temp_db_path)
        db.init()

        source = Source(domain="to-delete.com")
        added = db.add_source(source)

        result = db.delete_source(added.id)
        assert result is True

        retrieved = db.get_source(added.id)
        assert retrieved is None
        db.close()


class TestEntrySourcesCRUD:
    """Tests for EntrySource linking operations (Feature 009)."""

    def test_link_entry_to_source_theme(self, temp_db_path: Path):
        """Should link entry to a theme source."""
        from rekall.db import Database
        from rekall.models import Entry, generate_ulid

        db = Database(temp_db_path)
        db.init()

        entry = Entry(id=generate_ulid(), title="Python basics", type="reference")
        db.add(entry)

        link = db.link_entry_to_source(
            entry_id=entry.id,
            source_type="theme",
            source_ref="Python/Fundamentals",
            note="Good intro resource",
        )

        assert link.id != ""
        assert link.entry_id == entry.id
        assert link.source_type == "theme"
        assert link.source_ref == "Python/Fundamentals"
        assert link.note == "Good intro resource"
        db.close()

    def test_link_entry_to_source_url(self, temp_db_path: Path):
        """Should link entry to a URL source with curated Source."""
        from rekall.db import Database
        from rekall.models import Entry, Source, generate_ulid

        db = Database(temp_db_path)
        db.init()

        # Create entry and source
        entry = Entry(id=generate_ulid(), title="SO answer", type="reference")
        db.add(entry)

        source = Source(domain="stackoverflow.com", url_pattern="/questions/*")
        added_source = db.add_source(source)

        link = db.link_entry_to_source(
            entry_id=entry.id,
            source_type="url",
            source_ref="https://stackoverflow.com/questions/12345",
            source_id=added_source.id,
        )

        assert link.source_id == added_source.id
        assert link.source_type == "url"
        db.close()

    def test_link_entry_not_found(self, temp_db_path: Path):
        """Should raise ValueError if entry doesn't exist."""
        import pytest

        from rekall.db import Database

        db = Database(temp_db_path)
        db.init()

        with pytest.raises(ValueError, match="Entry not found"):
            db.link_entry_to_source(
                entry_id="nonexistent",
                source_type="theme",
                source_ref="test",
            )
        db.close()

    def test_get_entry_sources(self, temp_db_path: Path):
        """Should retrieve all sources linked to an entry."""
        from rekall.db import Database
        from rekall.models import Entry, Source, generate_ulid

        db = Database(temp_db_path)
        db.init()

        entry = Entry(id=generate_ulid(), title="Multi-source", type="reference")
        db.add(entry)

        source = Source(domain="docs.python.org")
        added_source = db.add_source(source)

        # Add multiple links
        db.link_entry_to_source(entry.id, "theme", "Python/Async")
        db.link_entry_to_source(
            entry.id, "url", "https://docs.python.org/3/library/asyncio.html",
            source_id=added_source.id
        )
        db.link_entry_to_source(entry.id, "file", "/docs/notes.md")

        sources = db.get_entry_sources(entry.id)
        assert len(sources) == 3

        # Check types
        types = {s.source_type for s in sources}
        assert types == {"theme", "url", "file"}

        # Check that URL source has joined Source data
        url_source = next(s for s in sources if s.source_type == "url")
        assert url_source.source is not None
        assert url_source.source.domain == "docs.python.org"
        db.close()

    def test_unlink_entry_from_source(self, temp_db_path: Path):
        """Should remove link between entry and source."""
        from rekall.db import Database
        from rekall.models import Entry, generate_ulid

        db = Database(temp_db_path)
        db.init()

        entry = Entry(id=generate_ulid(), title="Test", type="bug")
        db.add(entry)

        link = db.link_entry_to_source(entry.id, "theme", "Testing")

        # Unlink
        result = db.unlink_entry_from_source(link.id)
        assert result is True

        # Verify gone
        sources = db.get_entry_sources(entry.id)
        assert len(sources) == 0
        db.close()

    def test_unlink_nonexistent(self, temp_db_path: Path):
        """Should return False for non-existent link."""
        from rekall.db import Database

        db = Database(temp_db_path)
        db.init()

        result = db.unlink_entry_from_source("nonexistent")
        assert result is False
        db.close()


class TestUtilsFunctions:
    """Tests for utility functions (Feature 009)."""

    def test_extract_domain_simple(self):
        """Should extract domain from various URL formats."""
        from rekall.utils import extract_domain

        assert extract_domain("https://example.com/path") == "example.com"
        assert extract_domain("http://example.com") == "example.com"
        assert extract_domain("example.com/path") == "example.com"
        assert extract_domain("//example.com/path") == "example.com"

    def test_extract_domain_with_port(self):
        """Should handle URLs with ports."""
        from rekall.utils import extract_domain

        assert extract_domain("https://example.com:8080/path") == "example.com"
        assert extract_domain("example.com:443") == "example.com"

    def test_extract_domain_subdomains(self):
        """Should preserve subdomains."""
        from rekall.utils import extract_domain

        assert extract_domain("https://docs.python.org") == "docs.python.org"
        assert extract_domain("https://api.example.com") == "api.example.com"
        assert extract_domain("https://www.example.com") == "www.example.com"

    def test_normalize_url_scheme(self):
        """Should normalize URL scheme to https."""
        from rekall.utils import normalize_url

        assert normalize_url("http://example.com").startswith("https://")
        assert normalize_url("example.com").startswith("https://")
        assert normalize_url("//example.com").startswith("https://")

    def test_normalize_url_trailing_slash(self):
        """Should remove trailing slashes."""
        from rekall.utils import normalize_url

        assert normalize_url("https://example.com/path/") == "https://example.com/path"
        # Root path should keep single slash
        assert normalize_url("https://example.com/") == "https://example.com/"

    def test_normalize_url_tracking_params(self):
        """Should remove tracking parameters."""
        from rekall.utils import normalize_url

        url = "https://example.com/page?utm_source=twitter&id=123&utm_medium=social"
        normalized = normalize_url(url)
        assert "utm_source" not in normalized
        assert "utm_medium" not in normalized
        assert "id=123" in normalized

    def test_is_valid_url(self):
        """Should validate URL format."""
        from rekall.utils import is_valid_url

        assert is_valid_url("https://example.com") is True
        assert is_valid_url("example.com") is True
        assert is_valid_url("docs.python.org/3/library") is True
        assert is_valid_url("not a url") is False
        assert is_valid_url("justaword") is False

    def test_extract_url_pattern_stackoverflow(self):
        """Should extract Stack Overflow patterns."""
        from rekall.utils import extract_url_pattern

        pattern = extract_url_pattern("https://stackoverflow.com/questions/12345/title-here")
        assert pattern == "/questions/*"

    def test_extract_url_pattern_github(self):
        """Should extract GitHub patterns."""
        from rekall.utils import extract_url_pattern

        pattern = extract_url_pattern("https://github.com/anthropics/claude-code/blob/main/README.md")
        assert pattern == "/anthropics/claude-code/*"

    def test_extract_url_pattern_generic(self):
        """Should extract generic patterns for unknown sites."""
        from rekall.utils import extract_url_pattern

        pattern = extract_url_pattern("https://example.com/docs/api/v2/users")
        assert pattern == "/docs/api/*"

    def test_extract_url_pattern_none(self):
        """Should return None for root paths."""
        from rekall.utils import extract_url_pattern

        assert extract_url_pattern("https://example.com/") is None
        assert extract_url_pattern("https://example.com") is None


class TestSourceScoring:
    """Tests for source scoring operations (Feature 009 - US3)."""

    def test_calculate_source_score_new_source(self, temp_db_path: Path):
        """New source should have base score of 50."""
        from rekall.db import Database
        from rekall.models import Source

        db = Database(temp_db_path)
        db.init()

        source = Source(domain="new-source.com")
        score = db.calculate_source_score(source)

        # Base score with no usage, no recency decay
        assert 49 <= score <= 51  # Approximately 50
        db.close()

    def test_calculate_source_score_with_usage(self, temp_db_path: Path):
        """Score should increase with usage."""
        from datetime import datetime

        from rekall.db import Database
        from rekall.models import Source

        db = Database(temp_db_path)
        db.init()

        # Source with high usage
        source = Source(
            domain="popular.com",
            usage_count=100,
            last_used=datetime.now(),
            reliability="A",
        )
        score = db.calculate_source_score(source)

        # Should be significantly higher than base
        assert score > 70
        db.close()

    def test_calculate_source_score_reliability_factor(self, temp_db_path: Path):
        """Reliability rating should affect score."""
        from datetime import datetime

        from rekall.db import Database
        from rekall.models import Source

        db = Database(temp_db_path)
        db.init()

        base_args = {
            "usage_count": 10,
            "last_used": datetime.now(),
        }

        source_a = Source(domain="reliable-a.com", reliability="A", **base_args)
        source_b = Source(domain="reliable-b.com", reliability="B", **base_args)
        source_c = Source(domain="reliable-c.com", reliability="C", **base_args)

        score_a = db.calculate_source_score(source_a)
        score_b = db.calculate_source_score(source_b)
        score_c = db.calculate_source_score(source_c)

        # A > B > C
        assert score_a > score_b > score_c
        db.close()

    def test_calculate_source_score_decay(self, temp_db_path: Path):
        """Score should decay over time for inactive sources."""
        from datetime import datetime, timedelta

        from rekall.db import Database
        from rekall.models import Source

        db = Database(temp_db_path)
        db.init()

        # Source used today
        recent = Source(
            domain="recent.com",
            usage_count=10,
            last_used=datetime.now(),
            decay_rate="medium",
        )

        # Source used 6 months ago (one half-life for medium)
        old = Source(
            domain="old.com",
            usage_count=10,
            last_used=datetime.now() - timedelta(days=180),
            decay_rate="medium",
        )

        recent_score = db.calculate_source_score(recent)
        old_score = db.calculate_source_score(old)

        # Old source should have lower score due to decay
        assert recent_score > old_score
        # After one half-life, score should be roughly half
        # (but with minimum factor of 0.2)
        assert old_score < recent_score * 0.7
        db.close()

    def test_update_source_usage(self, temp_db_path: Path):
        """Updating usage should increment count and recalculate score."""
        from rekall.db import Database
        from rekall.models import Source

        db = Database(temp_db_path)
        db.init()

        source = Source(domain="update-test.com", usage_count=0)
        added = db.add_source(source)
        initial_score = added.personal_score

        # Update usage
        updated = db.update_source_usage(added.id)

        assert updated is not None
        assert updated.usage_count == 1
        assert updated.last_used is not None
        assert updated.personal_score >= initial_score
        db.close()

    def test_link_updates_source_usage(self, temp_db_path: Path):
        """Linking entry to source should update usage automatically."""
        from rekall.db import Database
        from rekall.models import Entry, Source, generate_ulid

        db = Database(temp_db_path)
        db.init()

        # Create source and entry
        source = Source(domain="auto-update.com", usage_count=0)
        added_source = db.add_source(source)

        entry = Entry(id=generate_ulid(), title="Test", type="reference")
        db.add(entry)

        # Link - should auto-update source usage
        db.link_entry_to_source(
            entry.id, "url", "https://auto-update.com/page",
            source_id=added_source.id
        )

        # Verify usage was updated
        updated_source = db.get_source(added_source.id)
        assert updated_source.usage_count == 1
        assert updated_source.last_used is not None
        db.close()

    def test_get_top_sources(self, temp_db_path: Path):
        """Should return sources sorted by score."""
        from datetime import datetime

        from rekall.db import Database
        from rekall.models import Source

        db = Database(temp_db_path)
        db.init()

        # Create sources with different scores
        for i, (domain, usage, reliability) in enumerate([
            ("low.com", 1, "C"),
            ("medium.com", 10, "B"),
            ("high.com", 50, "A"),
        ]):
            source = Source(
                domain=domain,
                usage_count=usage,
                reliability=reliability,
                last_used=datetime.now(),
            )
            added = db.add_source(source)
            # Recalculate to ensure score is set
            db.recalculate_source_score(added.id)

        top = db.get_top_sources(limit=10)

        assert len(top) == 3
        # Should be sorted by score descending
        assert top[0].domain == "high.com"
        assert top[1].domain == "medium.com"
        assert top[2].domain == "low.com"
        db.close()

    def test_recalculate_all_scores(self, temp_db_path: Path):
        """Should recalculate scores for all active sources."""
        from rekall.db import Database
        from rekall.models import Source

        db = Database(temp_db_path)
        db.init()

        # Create multiple sources
        for i in range(5):
            source = Source(domain=f"source{i}.com", usage_count=i * 10)
            db.add_source(source)

        # Recalculate all
        count = db.recalculate_all_scores()

        assert count == 5
        db.close()

    def test_list_sources_with_filters(self, temp_db_path: Path):
        """Should filter sources by status and score."""
        from datetime import datetime

        from rekall.db import Database
        from rekall.models import Source

        db = Database(temp_db_path)
        db.init()

        # Create sources with different statuses
        active1 = Source(domain="active1.com", status="active", usage_count=50,
                         last_used=datetime.now())
        active2 = Source(domain="active2.com", status="active", usage_count=10,
                         last_used=datetime.now())
        inactive = Source(domain="inactive.com", status="inaccessible")

        for s in [active1, active2, inactive]:
            added = db.add_source(s)
            db.recalculate_source_score(added.id)

        # Filter by status
        active_only = db.list_sources(status="active")
        assert len(active_only) == 2

        # All sources
        all_sources = db.list_sources()
        assert len(all_sources) == 3
        db.close()


class TestBacklinks:
    """Tests for backlink operations (Feature 009 - US2)."""

    def test_get_source_backlinks(self, temp_db_path: Path):
        """Should retrieve entries citing a source."""
        from rekall.db import Database
        from rekall.models import Entry, Source, generate_ulid

        db = Database(temp_db_path)
        db.init()

        # Create source
        source = Source(domain="stackoverflow.com")
        added_source = db.add_source(source)

        # Create entries that cite this source
        entry1 = Entry(id=generate_ulid(), title="SO Answer 1", type="reference")
        entry2 = Entry(id=generate_ulid(), title="SO Answer 2", type="reference")
        entry3 = Entry(id=generate_ulid(), title="No source", type="reference")
        db.add(entry1)
        db.add(entry2)
        db.add(entry3)

        # Link two entries to the source
        db.link_entry_to_source(
            entry1.id, "url", "https://stackoverflow.com/q/123",
            source_id=added_source.id
        )
        db.link_entry_to_source(
            entry2.id, "url", "https://stackoverflow.com/q/456",
            source_id=added_source.id
        )

        # Get backlinks
        backlinks = db.get_source_backlinks(added_source.id)
        assert len(backlinks) == 2

        # Check entries are correct
        entry_titles = {e.title for e, _ in backlinks}
        assert entry_titles == {"SO Answer 1", "SO Answer 2"}
        db.close()

    def test_get_source_backlinks_empty(self, temp_db_path: Path):
        """Should return empty list for source with no backlinks."""
        from rekall.db import Database
        from rekall.models import Source

        db = Database(temp_db_path)
        db.init()

        source = Source(domain="no-backlinks.com")
        added_source = db.add_source(source)

        backlinks = db.get_source_backlinks(added_source.id)
        assert len(backlinks) == 0
        db.close()

    def test_get_source_backlinks_pagination(self, temp_db_path: Path):
        """Should support pagination for backlinks."""
        from rekall.db import Database
        from rekall.models import Entry, Source, generate_ulid

        db = Database(temp_db_path)
        db.init()

        source = Source(domain="many-refs.com")
        added_source = db.add_source(source)

        # Create 5 entries citing this source
        for i in range(5):
            entry = Entry(id=generate_ulid(), title=f"Entry {i}", type="reference")
            db.add(entry)
            db.link_entry_to_source(entry.id, "url", f"https://many-refs.com/{i}",
                                     source_id=added_source.id)

        # Get first page (limit 2)
        page1 = db.get_source_backlinks(added_source.id, limit=2, offset=0)
        assert len(page1) == 2

        # Get second page
        page2 = db.get_source_backlinks(added_source.id, limit=2, offset=2)
        assert len(page2) == 2

        # Get third page (only 1 remaining)
        page3 = db.get_source_backlinks(added_source.id, limit=2, offset=4)
        assert len(page3) == 1

        # Ensure no duplicates
        all_ids = {e.id for e, _ in page1 + page2 + page3}
        assert len(all_ids) == 5
        db.close()

    def test_count_source_backlinks(self, temp_db_path: Path):
        """Should count entries citing a source."""
        from rekall.db import Database
        from rekall.models import Entry, Source, generate_ulid

        db = Database(temp_db_path)
        db.init()

        source = Source(domain="count-test.com")
        added_source = db.add_source(source)

        # Initially 0
        assert db.count_source_backlinks(added_source.id) == 0

        # Add 3 entries
        for i in range(3):
            entry = Entry(id=generate_ulid(), title=f"Entry {i}", type="reference")
            db.add(entry)
            db.link_entry_to_source(entry.id, "url", f"https://count-test.com/{i}",
                                     source_id=added_source.id)

        # Should be 3
        assert db.count_source_backlinks(added_source.id) == 3
        db.close()

    def test_get_backlinks_by_domain(self, temp_db_path: Path):
        """Should get backlinks for all sources from a domain."""
        from rekall.db import Database
        from rekall.models import Entry, Source, generate_ulid

        db = Database(temp_db_path)
        db.init()

        # Create two sources for same domain
        source1 = Source(domain="github.com", url_pattern="/anthropics/*")
        source2 = Source(domain="github.com", url_pattern="/openai/*")
        added1 = db.add_source(source1)
        added2 = db.add_source(source2)

        # Create entries linked to different patterns
        entry1 = Entry(id=generate_ulid(), title="Anthropic code", type="reference")
        entry2 = Entry(id=generate_ulid(), title="OpenAI code", type="reference")
        db.add(entry1)
        db.add(entry2)

        db.link_entry_to_source(entry1.id, "url", "https://github.com/anthropics/claude",
                                 source_id=added1.id)
        db.link_entry_to_source(entry2.id, "url", "https://github.com/openai/gpt",
                                 source_id=added2.id)

        # Get all github.com backlinks
        backlinks = db.get_backlinks_by_domain("github.com")
        assert len(backlinks) == 2

        titles = {e.title for e, _ in backlinks}
        assert titles == {"Anthropic code", "OpenAI code"}
        db.close()


# ============================================================================
# Feature 010: Sources Autonomes - Migration v9 Tests
# ============================================================================


class TestMigrationV9:
    """Tests for migration v9 (Sources Autonomes)."""

    def test_migration_v9_adds_source_columns(self, temp_db_path: Path):
        """Migration v9 should add new columns to sources table."""
        from rekall.db import Database

        db = Database(temp_db_path)
        db.init()

        # Check new columns exist
        cursor = db.conn.execute("PRAGMA table_info(sources)")
        columns = {row[1] for row in cursor.fetchall()}

        assert "is_seed" in columns
        assert "is_promoted" in columns
        assert "promoted_at" in columns
        assert "role" in columns
        assert "seed_origin" in columns
        assert "citation_quality_factor" in columns
        db.close()

    def test_migration_v9_creates_source_themes_table(self, temp_db_path: Path):
        """Migration v9 should create source_themes table."""
        from rekall.db import Database

        db = Database(temp_db_path)
        db.init()

        # Check table exists
        cursor = db.conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='source_themes'"
        )
        assert cursor.fetchone() is not None

        # Check columns
        cursor = db.conn.execute("PRAGMA table_info(source_themes)")
        columns = {row[1] for row in cursor.fetchall()}
        assert "source_id" in columns
        assert "theme" in columns
        db.close()

    def test_migration_v9_creates_known_domains_table(self, temp_db_path: Path):
        """Migration v9 should create known_domains table with initial data."""
        from rekall.db import Database

        db = Database(temp_db_path)
        db.init()

        # Check table exists
        cursor = db.conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='known_domains'"
        )
        assert cursor.fetchone() is not None

        # Check initial data was inserted
        cursor = db.conn.execute("SELECT COUNT(*) FROM known_domains")
        count = cursor.fetchone()[0]
        assert count >= 25, f"Expected at least 25 known domains, got {count}"

        # Check specific domains
        cursor = db.conn.execute(
            "SELECT role FROM known_domains WHERE domain = 'developer.mozilla.org'"
        )
        row = cursor.fetchone()
        assert row is not None
        assert row[0] == "authority"

        cursor = db.conn.execute(
            "SELECT role FROM known_domains WHERE domain = 'stackoverflow.com'"
        )
        row = cursor.fetchone()
        assert row is not None
        assert row[0] == "hub"
        db.close()

    def test_migration_v9_creates_indexes(self, temp_db_path: Path):
        """Migration v9 should create required indexes."""
        from rekall.db import Database

        db = Database(temp_db_path)
        db.init()

        # Get all indexes
        cursor = db.conn.execute(
            "SELECT name FROM sqlite_master WHERE type='index'"
        )
        indexes = {row[0] for row in cursor.fetchall()}

        # Check new source indexes
        assert "idx_sources_is_seed" in indexes
        assert "idx_sources_is_promoted" in indexes
        assert "idx_sources_role" in indexes
        assert "idx_source_themes_theme" in indexes
        db.close()

    def test_migration_v9_source_themes_foreign_key(self, temp_db_path: Path):
        """Deleting source should cascade delete source_themes."""
        from rekall.db import Database
        from rekall.models import Source, generate_ulid

        db = Database(temp_db_path)
        db.init()

        # Create source
        source = Source(domain="test.com", url_pattern="/docs/*")
        added = db.add_source(source)

        # Add theme manually
        db.conn.execute(
            "INSERT INTO source_themes (source_id, theme) VALUES (?, ?)",
            (added.id, "testing")
        )
        db.conn.commit()

        # Verify theme exists
        cursor = db.conn.execute(
            "SELECT theme FROM source_themes WHERE source_id = ?",
            (added.id,)
        )
        assert cursor.fetchone() is not None

        # Delete source
        db.conn.execute("DELETE FROM sources WHERE id = ?", (added.id,))
        db.conn.commit()

        # Theme should be cascade deleted
        cursor = db.conn.execute(
            "SELECT theme FROM source_themes WHERE source_id = ?",
            (added.id,)
        )
        assert cursor.fetchone() is None
        db.close()

    def test_migration_v9_known_domains_check_constraint(self, temp_db_path: Path):
        """known_domains.role should only accept hub or authority."""
        import sqlite3

        from rekall.db import Database

        db = Database(temp_db_path)
        db.init()

        # Try invalid role - should fail
        with db.conn:
            try:
                db.conn.execute(
                    """INSERT INTO known_domains (domain, role, created_at)
                       VALUES (?, ?, datetime('now'))""",
                    ("invalid.com", "invalid_role")
                )
                assert False, "Should have raised constraint error"
            except sqlite3.IntegrityError:
                pass  # Expected

        # Valid insert should work
        db.conn.execute(
            """INSERT INTO known_domains (domain, role, created_at)
               VALUES (?, ?, datetime('now'))""",
            ("valid.com", "authority")
        )
        db.conn.commit()

        cursor = db.conn.execute(
            "SELECT role FROM known_domains WHERE domain = 'valid.com'"
        )
        assert cursor.fetchone()[0] == "authority"
        db.close()

    def test_migration_v9_source_with_new_fields(self, temp_db_path: Path):
        """Should be able to insert source with new v9 fields."""
        from rekall.db import Database
        from rekall.models import generate_ulid

        db = Database(temp_db_path)
        db.init()

        source_id = generate_ulid()
        db.conn.execute(
            """INSERT INTO sources
               (id, domain, is_seed, is_promoted, role, seed_origin,
                citation_quality_factor, reliability, decay_rate, status, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))""",
            (source_id, "test.com", 1, 0, "authority", "/path/to/file.md", 0.75, "A", "slow", "active")
        )
        db.conn.commit()

        cursor = db.conn.execute(
            "SELECT is_seed, is_promoted, role, seed_origin, citation_quality_factor FROM sources WHERE id = ?",
            (source_id,)
        )
        row = cursor.fetchone()
        assert row[0] == 1  # is_seed
        assert row[1] == 0  # is_promoted
        assert row[2] == "authority"
        assert row[3] == "/path/to/file.md"
        assert row[4] == 0.75
        db.close()

    def test_migration_v10_creates_saved_filters_table(self, temp_db_path: Path):
        """Migration v10 should create saved_filters table."""
        from rekall.db import Database

        db = Database(temp_db_path)
        db.init()

        # Check table exists
        cursor = db.conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='saved_filters'"
        )
        assert cursor.fetchone() is not None

        # Check columns
        cursor = db.conn.execute("PRAGMA table_info(saved_filters)")
        columns = {row[1] for row in cursor.fetchall()}
        assert "id" in columns
        assert "name" in columns
        assert "filter_json" in columns
        assert "created_at" in columns
        db.close()

    def test_migration_v10_saved_filters_unique_name(self, temp_db_path: Path):
        """Migration v10 should enforce unique filter names."""
        import sqlite3

        from rekall.db import Database

        db = Database(temp_db_path)
        db.init()

        # Insert first filter
        db.conn.execute(
            "INSERT INTO saved_filters (name, filter_json) VALUES (?, ?)",
            ("test_filter", '{"tags": ["python"]}')
        )
        db.conn.commit()

        # Try to insert duplicate name
        with pytest.raises(sqlite3.IntegrityError):
            db.conn.execute(
                "INSERT INTO saved_filters (name, filter_json) VALUES (?, ?)",
                ("test_filter", '{"tags": ["go"]}')
            )
        db.close()


class TestSourcesOrganisation:
    """Tests for Feature 012 - Sources Organisation (tags/filters)."""

    def test_get_all_tags_with_counts(self, temp_db_path: Path):
        """Should return all tags with their source counts."""
        from rekall.db import Database
        from rekall.models import Source

        db = Database(temp_db_path)
        db.init()

        # Create sources and assign tags
        source1 = db.add_source(Source(domain="site1.com", personal_score=50.0))
        source2 = db.add_source(Source(domain="site2.com", personal_score=60.0))
        source3 = db.add_source(Source(domain="site3.com", personal_score=70.0))

        db.add_source_theme(source1.id, "python")
        db.add_source_theme(source1.id, "testing")
        db.add_source_theme(source2.id, "python")
        db.add_source_theme(source2.id, "go")
        db.add_source_theme(source3.id, "python")

        tags = db.get_all_tags_with_counts()

        # python has 3 sources, go and testing have 1 each
        python_tag = next((t for t in tags if t["theme"] == "python"), None)
        assert python_tag is not None
        assert python_tag["count"] == 3

        go_tag = next((t for t in tags if t["theme"] == "go"), None)
        assert go_tag is not None
        assert go_tag["count"] == 1

        db.close()

    def test_get_sources_by_tags_single(self, temp_db_path: Path):
        """Should return sources matching a single tag."""
        from rekall.db import Database
        from rekall.models import Source

        db = Database(temp_db_path)
        db.init()

        source1 = db.add_source(Source(domain="site1.com", personal_score=50.0))
        source2 = db.add_source(Source(domain="site2.com", personal_score=60.0))
        source3 = db.add_source(Source(domain="site3.com", personal_score=70.0))

        db.add_source_theme(source1.id, "python")
        db.add_source_theme(source2.id, "go")
        db.add_source_theme(source3.id, "python")

        results = db.get_sources_by_tags(["python"])

        assert len(results) == 2
        domains = {s.domain for s in results}
        assert "site1.com" in domains
        assert "site3.com" in domains
        assert "site2.com" not in domains
        db.close()

    def test_get_sources_by_tags_multiple_or_logic(self, temp_db_path: Path):
        """Should return sources matching ANY of the tags (OR logic)."""
        from rekall.db import Database
        from rekall.models import Source

        db = Database(temp_db_path)
        db.init()

        source1 = db.add_source(Source(domain="site1.com", personal_score=50.0))
        source2 = db.add_source(Source(domain="site2.com", personal_score=60.0))
        source3 = db.add_source(Source(domain="site3.com", personal_score=70.0))

        db.add_source_theme(source1.id, "python")
        db.add_source_theme(source2.id, "go")
        db.add_source_theme(source3.id, "rust")

        results = db.get_sources_by_tags(["python", "go"])

        assert len(results) == 2
        domains = {s.domain for s in results}
        assert "site1.com" in domains
        assert "site2.com" in domains
        assert "site3.com" not in domains  # rust only
        db.close()

    def test_get_sources_by_tags_empty_list(self, temp_db_path: Path):
        """Should return empty list for empty tags."""
        from rekall.db import Database

        db = Database(temp_db_path)
        db.init()

        results = db.get_sources_by_tags([])
        assert results == []
        db.close()

    def test_get_tags_suggestions(self, temp_db_path: Path):
        """Should return tag suggestions matching prefix."""
        from rekall.db import Database
        from rekall.models import Source

        db = Database(temp_db_path)
        db.init()

        source1 = db.add_source(Source(domain="site1.com", personal_score=50.0))
        source2 = db.add_source(Source(domain="site2.com", personal_score=60.0))

        db.add_source_theme(source1.id, "python")
        db.add_source_theme(source1.id, "pytest")
        db.add_source_theme(source2.id, "python")
        db.add_source_theme(source2.id, "go")

        # Search for "py" prefix
        suggestions = db.get_tags_suggestions("py")
        assert "python" in suggestions
        assert "pytest" in suggestions
        assert "go" not in suggestions

        # python should come first (2 sources) before pytest (1 source)
        assert suggestions[0] == "python"
        db.close()

    def test_search_sources_advanced_by_tags(self, temp_db_path: Path):
        """Should filter sources by tags with OR logic."""
        from rekall.db import Database
        from rekall.models import Source

        db = Database(temp_db_path)
        db.init()

        source1 = db.add_source(Source(domain="site1.com", personal_score=50.0))
        source2 = db.add_source(Source(domain="site2.com", personal_score=60.0))
        source3 = db.add_source(Source(domain="site3.com", personal_score=70.0))

        db.add_source_theme(source1.id, "python")
        db.add_source_theme(source2.id, "go")
        db.add_source_theme(source3.id, "rust")

        # Filter by single tag
        results = db.search_sources_advanced(tags=["python"])
        assert len(results) == 1
        assert results[0].domain == "site1.com"

        # Filter by multiple tags (OR)
        results = db.search_sources_advanced(tags=["python", "go"])
        assert len(results) == 2
        db.close()

    def test_search_sources_advanced_by_score(self, temp_db_path: Path):
        """Should filter sources by score range."""
        from rekall.db import Database
        from rekall.models import Source

        db = Database(temp_db_path)
        db.init()

        db.add_source(Source(domain="low.com", personal_score=20.0))
        db.add_source(Source(domain="mid.com", personal_score=50.0))
        db.add_source(Source(domain="high.com", personal_score=80.0))

        results = db.search_sources_advanced(score_min=40, score_max=60)
        assert len(results) == 1
        assert results[0].domain == "mid.com"
        db.close()

    def test_search_sources_advanced_combined(self, temp_db_path: Path):
        """Should combine multiple filter criteria with AND logic."""
        from rekall.db import Database
        from rekall.models import Source

        db = Database(temp_db_path)
        db.init()

        source1 = db.add_source(Source(domain="site1.com", personal_score=50.0, status="active"))
        source2 = db.add_source(Source(domain="site2.com", personal_score=60.0, status="archived"))
        source3 = db.add_source(Source(domain="site3.com", personal_score=70.0, status="active"))

        db.add_source_theme(source1.id, "python")
        db.add_source_theme(source2.id, "python")
        db.add_source_theme(source3.id, "python")

        # Filter by tag AND status
        results = db.search_sources_advanced(tags=["python"], statuses=["active"])
        assert len(results) == 2
        domains = {s.domain for s in results}
        assert "site2.com" not in domains  # archived
        db.close()


class TestSourcesAutonomes:
    """Tests for Feature 010 - Sources Autonomes."""

    def test_promotion_criteria_met(self, temp_db_path: Path):
        """Should recognize when source meets promotion criteria."""
        from datetime import datetime, timedelta

        from rekall.db import Database
        from rekall.models import Source

        db = Database(temp_db_path)
        db.init()

        # Create source meeting all criteria
        source = Source(
            domain="qualified.com",
            usage_count=5,  # >= 3
            personal_score=45.0,  # >= 30
            last_used=datetime.now() - timedelta(days=30),  # within 180 days
        )
        added = db.add_source(source)

        result = db.check_promotion_criteria(added)
        assert result is True
        db.close()

    def test_promotion_criteria_not_met(self, temp_db_path: Path):
        """Should recognize when source doesn't meet promotion criteria."""
        from datetime import datetime, timedelta

        from rekall.db import Database
        from rekall.models import Source

        db = Database(temp_db_path)
        db.init()

        # Low usage count
        source1 = Source(
            domain="low-usage.com",
            usage_count=1,  # < 3
            personal_score=50.0,
            last_used=datetime.now(),
        )
        added1 = db.add_source(source1)
        assert db.check_promotion_criteria(added1) is False

        # Low score
        source2 = Source(
            domain="low-score.com",
            usage_count=5,
            personal_score=20.0,  # < 30
            last_used=datetime.now(),
        )
        added2 = db.add_source(source2)
        assert db.check_promotion_criteria(added2) is False

        # Too old
        source3 = Source(
            domain="old.com",
            usage_count=5,
            personal_score=50.0,
            last_used=datetime.now() - timedelta(days=200),  # > 180 days
        )
        added3 = db.add_source(source3)
        assert db.check_promotion_criteria(added3) is False
        db.close()

    def test_promotion_seeds_exemption(self, temp_db_path: Path):
        """Seeds should be exempt from demotion."""
        from datetime import datetime, timedelta

        from rekall.db import Database
        from rekall.models import Source

        db = Database(temp_db_path)
        db.init()

        # Create seed source that doesn't meet criteria
        source = Source(
            domain="seed-source.com",
            is_seed=True,
            seed_origin="/research/test.md",
            usage_count=1,  # doesn't meet criteria
            personal_score=10.0,  # doesn't meet criteria
            last_used=datetime.now() - timedelta(days=200),  # doesn't meet criteria
        )
        added = db.add_source(source)

        # Should not meet promotion criteria
        assert db.check_promotion_criteria(added) is False

        # But demotion should fail (seeds protected)
        result = db.demote_source(added.id)
        assert result is False

        # Verify still not demoted
        refreshed = db.get_source(added.id)
        assert refreshed.is_seed is True
        db.close()

    def test_auto_classification_known_domain(self, temp_db_path: Path):
        """Should auto-classify sources from known domains."""
        from rekall.db import Database
        from rekall.models import Source

        db = Database(temp_db_path)
        db.init()

        # stackoverflow.com should be classified as hub (pre-populated in migration)
        source = Source(domain="stackoverflow.com")
        added = db.add_source(source)

        # Get fresh from DB
        refreshed = db.get_source(added.id)
        assert refreshed.role == "hub"
        db.close()

    def test_auto_classification_unknown_domain(self, temp_db_path: Path):
        """Unknown domains should remain unclassified."""
        from rekall.db import Database
        from rekall.models import Source

        db = Database(temp_db_path)
        db.init()

        source = Source(domain="unknown-random-domain.xyz")
        added = db.add_source(source)

        refreshed = db.get_source(added.id)
        assert refreshed.role == "unclassified"
        db.close()

    def test_citation_quality_calculation(self, temp_db_path: Path):
        """Should calculate citation quality based on co-citations."""
        from rekall.db import Database
        from rekall.models import Entry, Source, generate_ulid

        db = Database(temp_db_path)
        db.init()

        # Create sources
        seed_source = Source(domain="seed.com", is_seed=True)
        seed_added = db.add_source(seed_source)

        authority_source = Source(domain="authority.com", role="authority")
        auth_added = db.add_source(authority_source)

        test_source = Source(domain="test.com")
        test_added = db.add_source(test_source)

        # Create entry citing all sources
        entry = Entry(id=generate_ulid(), title="Test Entry", type="reference")
        db.add(entry)

        # Link sources to entry
        db.link_entry_to_source(
            entry.id, "url", "https://seed.com/doc", source_id=seed_added.id
        )
        db.link_entry_to_source(
            entry.id, "url", "https://authority.com/doc", source_id=auth_added.id
        )
        db.link_entry_to_source(
            entry.id, "url", "https://test.com/doc", source_id=test_added.id
        )

        # Calculate citation quality for test source
        quality = db.calculate_citation_quality(test_added.id)

        # Should be > 0 since co-cited with seed and authority
        assert quality > 0.0
        assert quality <= 1.0
        db.close()

    def test_score_v2_formula(self, temp_db_path: Path):
        """Score v2 should include role bonus, seed bonus, and citation quality."""
        from datetime import datetime

        from rekall.db import Database
        from rekall.models import Source

        db = Database(temp_db_path)
        db.init()

        # Normal source
        normal = Source(
            domain="normal.com",
            usage_count=5,
            last_used=datetime.now(),
            role="unclassified",
            is_seed=False,
            citation_quality_factor=0.0,
        )
        normal_added = db.add_source(normal)
        normal_score = db.calculate_source_score_v2(normal_added)

        # Authority source (1.2x bonus)
        authority = Source(
            domain="authority.com",
            usage_count=5,
            last_used=datetime.now(),
            role="authority",
            is_seed=False,
            citation_quality_factor=0.0,
        )
        auth_added = db.add_source(authority)
        auth_score = db.calculate_source_score_v2(auth_added)

        # Authority should score higher due to 1.2x role bonus
        assert auth_score > normal_score
        assert auth_score == pytest.approx(normal_score * 1.2, rel=0.01)

        # Seed source (1.2x seed bonus)
        seed = Source(
            domain="seed.com",
            usage_count=5,
            last_used=datetime.now(),
            role="unclassified",
            is_seed=True,
            citation_quality_factor=0.0,
        )
        seed_added = db.add_source(seed)
        seed_score = db.calculate_source_score_v2(seed_added)

        # Seed should score higher due to 1.2x seed bonus
        assert seed_score > normal_score
        assert seed_score == pytest.approx(normal_score * 1.2, rel=0.01)

        # High citation quality (up to 20% bonus)
        high_cq = Source(
            domain="highcq.com",
            usage_count=5,
            last_used=datetime.now(),
            role="unclassified",
            is_seed=False,
            citation_quality_factor=1.0,  # Max quality
        )
        hcq_added = db.add_source(high_cq)
        hcq_score = db.calculate_source_score_v2(hcq_added)

        # Should be ~20% higher than normal
        assert hcq_score > normal_score
        assert hcq_score == pytest.approx(normal_score * 1.2, rel=0.01)
        db.close()

    def test_speckit_parser_extract_theme(self):
        """Should extract theme from speckit filename."""
        from rekall.migration.speckit_parser import extract_theme_from_filename

        assert extract_theme_from_filename("01-ai-agents.md") == "ai-agents"
        assert extract_theme_from_filename("06-security.md") == "security"
        assert extract_theme_from_filename("12-web-development.md") == "web-development"
        assert extract_theme_from_filename("no-prefix.md") == "no-prefix"

    def test_speckit_parser_parse_file(self, tmp_path: Path):
        """Should parse URLs from markdown file."""
        from rekall.migration.speckit_parser import parse_research_file

        # Create test file
        test_file = tmp_path / "01-test-theme.md"
        test_file.write_text("""# Test Research

Some text with a [link](https://example.com/docs).

More text with https://another.com/page inline.

- List item: https://third.com/resource
""")

        result = parse_research_file(test_file)

        assert result.theme == "test-theme"
        assert len(result.sources) == 3
        domains = {s.domain for s in result.sources}
        assert domains == {"example.com", "another.com", "third.com"}
        assert len(result.errors) == 0

    def test_source_themes_crud(self, temp_db_path: Path):
        """Should add, get, and remove source themes."""
        from rekall.db import Database
        from rekall.models import Source

        db = Database(temp_db_path)
        db.init()

        source = Source(domain="themed.com")
        added = db.add_source(source)

        # Add themes
        db.add_source_theme(added.id, "security")
        db.add_source_theme(added.id, "ai-agents")

        # Get themes
        themes = db.get_source_themes(added.id)
        assert set(themes) == {"security", "ai-agents"}

        # Remove theme
        db.remove_source_theme(added.id, "security")
        themes = db.get_source_themes(added.id)
        assert themes == ["ai-agents"]
        db.close()

    def test_get_sources_by_theme(self, temp_db_path: Path):
        """Should retrieve sources filtered by theme."""
        from rekall.db import Database
        from rekall.models import Source

        db = Database(temp_db_path)
        db.init()

        # Create sources with themes
        s1 = db.add_source(Source(domain="sec1.com", personal_score=80))
        db.add_source_theme(s1.id, "security")

        s2 = db.add_source(Source(domain="sec2.com", personal_score=60))
        db.add_source_theme(s2.id, "security")

        s3 = db.add_source(Source(domain="ai.com", personal_score=90))
        db.add_source_theme(s3.id, "ai-agents")

        # Get security sources
        security_sources = db.get_sources_by_theme("security")
        assert len(security_sources) == 2
        # Should be sorted by score desc
        assert security_sources[0].domain == "sec1.com"
        assert security_sources[1].domain == "sec2.com"

        # Get ai sources
        ai_sources = db.get_sources_by_theme("ai-agents")
        assert len(ai_sources) == 1
        assert ai_sources[0].domain == "ai.com"
        db.close()


# =============================================================================
# Migration v11 - Sources Medallion (Feature 013)
# =============================================================================


class TestMigrationV11:
    """Tests for migration v11 - Sources Medallion tables."""

    def test_migration_v11_creates_sources_inbox_table(self, temp_db_path: Path):
        """Migration v11 should create sources_inbox table."""
        from rekall.db import Database

        db = Database(temp_db_path)
        db.init()

        cursor = db.conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='sources_inbox'"
        )
        assert cursor.fetchone() is not None
        db.close()

    def test_migration_v11_sources_inbox_columns(self, temp_db_path: Path):
        """Sources_inbox table should have correct columns."""
        from rekall.db import Database

        db = Database(temp_db_path)
        db.init()

        cursor = db.conn.execute("PRAGMA table_info(sources_inbox)")
        columns = {row[1]: row[2] for row in cursor.fetchall()}

        # Required columns
        assert "id" in columns
        assert "url" in columns
        assert "domain" in columns
        assert "cli_source" in columns
        assert "project" in columns
        assert "conversation_id" in columns
        assert "user_query" in columns
        assert "assistant_snippet" in columns
        assert "surrounding_text" in columns
        assert "captured_at" in columns
        assert "import_source" in columns
        assert "raw_json" in columns
        assert "is_valid" in columns
        assert "validation_error" in columns
        assert "enriched_at" in columns
        db.close()

    def test_migration_v11_creates_sources_staging_table(self, temp_db_path: Path):
        """Migration v11 should create sources_staging table."""
        from rekall.db import Database

        db = Database(temp_db_path)
        db.init()

        cursor = db.conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='sources_staging'"
        )
        assert cursor.fetchone() is not None
        db.close()

    def test_migration_v11_sources_staging_columns(self, temp_db_path: Path):
        """Sources_staging table should have correct columns."""
        from rekall.db import Database

        db = Database(temp_db_path)
        db.init()

        cursor = db.conn.execute("PRAGMA table_info(sources_staging)")
        columns = {row[1]: row[2] for row in cursor.fetchall()}

        # Required columns
        assert "id" in columns
        assert "url" in columns
        assert "domain" in columns
        assert "title" in columns
        assert "description" in columns
        assert "content_type" in columns
        assert "language" in columns
        assert "last_verified" in columns
        assert "is_accessible" in columns
        assert "http_status" in columns
        assert "citation_count" in columns
        assert "project_count" in columns
        assert "projects_list" in columns
        assert "first_seen" in columns
        assert "last_seen" in columns
        assert "promotion_score" in columns
        assert "inbox_ids" in columns
        assert "enriched_at" in columns
        assert "promoted_at" in columns
        assert "promoted_to" in columns
        db.close()

    def test_migration_v11_creates_connector_imports_table(self, temp_db_path: Path):
        """Migration v11 should create connector_imports table."""
        from rekall.db import Database

        db = Database(temp_db_path)
        db.init()

        cursor = db.conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='connector_imports'"
        )
        assert cursor.fetchone() is not None
        db.close()

    def test_migration_v11_connector_imports_columns(self, temp_db_path: Path):
        """Connector_imports table should have correct columns."""
        from rekall.db import Database

        db = Database(temp_db_path)
        db.init()

        cursor = db.conn.execute("PRAGMA table_info(connector_imports)")
        columns = {row[1]: row[2] for row in cursor.fetchall()}

        assert "connector" in columns
        assert "last_import" in columns
        assert "last_file_marker" in columns
        assert "entries_imported" in columns
        assert "errors_count" in columns
        db.close()

    def test_migration_v11_creates_indexes(self, temp_db_path: Path):
        """Migration v11 should create appropriate indexes."""
        from rekall.db import Database

        db = Database(temp_db_path)
        db.init()

        cursor = db.conn.execute(
            "SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_inbox_%'"
        )
        inbox_indexes = [row[0] for row in cursor.fetchall()]
        assert len(inbox_indexes) >= 4  # url, domain, cli_source, captured_at, etc.

        cursor = db.conn.execute(
            "SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_staging_%'"
        )
        staging_indexes = [row[0] for row in cursor.fetchall()]
        assert len(staging_indexes) >= 3  # domain, score, promoted_at
        db.close()


class TestInboxCRUD:
    """Tests for inbox CRUD operations (T024)."""

    def test_add_inbox_entry(self, temp_db_path: Path):
        """Should add inbox entry to database."""
        from rekall.db import Database
        from rekall.models import InboxEntry, generate_ulid

        db = Database(temp_db_path)
        db.init()

        entry = InboxEntry(
            id=generate_ulid(),
            url="https://docs.python.org/3/library/",
            domain="docs.python.org",
            cli_source="claude",
            project="rekall",
        )
        db.add_inbox_entry(entry)

        # Verify entry exists
        cursor = db.conn.execute(
            "SELECT * FROM sources_inbox WHERE id = ?", (entry.id,)
        )
        row = cursor.fetchone()
        assert row is not None
        assert row["url"] == "https://docs.python.org/3/library/"
        assert row["cli_source"] == "claude"
        db.close()

    def test_get_inbox_entries(self, temp_db_path: Path):
        """Should retrieve inbox entries."""
        from rekall.db import Database
        from rekall.models import InboxEntry, generate_ulid

        db = Database(temp_db_path)
        db.init()

        # Add multiple entries
        for i in range(3):
            entry = InboxEntry(
                id=generate_ulid(),
                url=f"https://example{i}.com/",
                domain=f"example{i}.com",
                cli_source="claude",
            )
            db.add_inbox_entry(entry)

        entries = db.get_inbox_entries()
        assert len(entries) == 3
        db.close()

    def test_get_inbox_entries_with_limit(self, temp_db_path: Path):
        """Should limit inbox entries returned."""
        from rekall.db import Database
        from rekall.models import InboxEntry, generate_ulid

        db = Database(temp_db_path)
        db.init()

        for i in range(5):
            entry = InboxEntry(
                id=generate_ulid(),
                url=f"https://example{i}.com/",
                domain=f"example{i}.com",
                cli_source="claude",
            )
            db.add_inbox_entry(entry)

        entries = db.get_inbox_entries(limit=2)
        assert len(entries) == 2
        db.close()

    def test_get_inbox_not_enriched(self, temp_db_path: Path):
        """Should get only non-enriched inbox entries."""
        from datetime import datetime

        from rekall.db import Database
        from rekall.models import InboxEntry, generate_ulid

        db = Database(temp_db_path)
        db.init()

        # Add enriched entry
        enriched = InboxEntry(
            id=generate_ulid(),
            url="https://enriched.com/",
            domain="enriched.com",
            cli_source="claude",
            enriched_at=datetime.now(),
        )
        db.add_inbox_entry(enriched)

        # Add non-enriched entry
        pending = InboxEntry(
            id=generate_ulid(),
            url="https://pending.com/",
            domain="pending.com",
            cli_source="claude",
            enriched_at=None,
        )
        db.add_inbox_entry(pending)

        not_enriched = db.get_inbox_not_enriched()
        assert len(not_enriched) == 1
        assert not_enriched[0].url == "https://pending.com/"
        db.close()

    def test_mark_inbox_enriched(self, temp_db_path: Path):
        """Should mark inbox entry as enriched."""
        from rekall.db import Database
        from rekall.models import InboxEntry, generate_ulid

        db = Database(temp_db_path)
        db.init()

        entry = InboxEntry(
            id=generate_ulid(),
            url="https://example.com/",
            domain="example.com",
            cli_source="claude",
        )
        db.add_inbox_entry(entry)

        db.mark_inbox_enriched(entry.id)

        # Verify enriched_at is set
        cursor = db.conn.execute(
            "SELECT enriched_at FROM sources_inbox WHERE id = ?", (entry.id,)
        )
        row = cursor.fetchone()
        assert row["enriched_at"] is not None
        db.close()

    def test_get_inbox_entries_quarantine(self, temp_db_path: Path):
        """Should filter inbox entries by is_valid."""
        from rekall.db import Database
        from rekall.models import InboxEntry, generate_ulid

        db = Database(temp_db_path)
        db.init()

        # Valid entry
        valid = InboxEntry(
            id=generate_ulid(),
            url="https://valid.com/",
            domain="valid.com",
            cli_source="claude",
            is_valid=True,
        )
        db.add_inbox_entry(valid)

        # Invalid entry (quarantine)
        invalid = InboxEntry(
            id=generate_ulid(),
            url="file:///local/path",
            domain="",
            cli_source="claude",
            is_valid=False,
            validation_error="file:// URLs not allowed",
        )
        db.add_inbox_entry(invalid)

        # Get valid only
        valid_entries = db.get_inbox_entries(valid_only=True)
        assert len(valid_entries) == 1
        assert valid_entries[0].is_valid is True

        # Get quarantine only
        quarantine = db.get_inbox_entries(quarantine_only=True)
        assert len(quarantine) == 1
        assert quarantine[0].is_valid is False
        db.close()


class TestStagingCRUD:
    """Tests for staging CRUD operations (T025)."""

    def test_add_staging_entry(self, temp_db_path: Path):
        """Should add staging entry to database."""
        from rekall.db import Database
        from rekall.models import StagingEntry, generate_ulid

        db = Database(temp_db_path)
        db.init()

        entry = StagingEntry(
            id=generate_ulid(),
            url="https://docs.python.org/3/library/",
            domain="docs.python.org",
            title="Python Standard Library",
            content_type="documentation",
        )
        db.add_staging_entry(entry)

        # Verify entry exists
        cursor = db.conn.execute(
            "SELECT * FROM sources_staging WHERE id = ?", (entry.id,)
        )
        row = cursor.fetchone()
        assert row is not None
        assert row["title"] == "Python Standard Library"
        assert row["content_type"] == "documentation"
        db.close()

    def test_get_staging_by_url(self, temp_db_path: Path):
        """Should retrieve staging entry by URL."""
        from rekall.db import Database
        from rekall.models import StagingEntry, generate_ulid

        db = Database(temp_db_path)
        db.init()

        entry = StagingEntry(
            id=generate_ulid(),
            url="https://example.com/unique",
            domain="example.com",
            title="Unique Page",
        )
        db.add_staging_entry(entry)

        retrieved = db.get_staging_by_url("https://example.com/unique")
        assert retrieved is not None
        assert retrieved.title == "Unique Page"

        # Non-existent URL
        not_found = db.get_staging_by_url("https://notfound.com/")
        assert not_found is None
        db.close()

    def test_get_staging_entries(self, temp_db_path: Path):
        """Should retrieve staging entries."""
        from rekall.db import Database
        from rekall.models import StagingEntry, generate_ulid

        db = Database(temp_db_path)
        db.init()

        for i in range(3):
            entry = StagingEntry(
                id=generate_ulid(),
                url=f"https://example{i}.com/",
                domain=f"example{i}.com",
                promotion_score=float(i * 10),
            )
            db.add_staging_entry(entry)

        entries = db.get_staging_entries()
        assert len(entries) == 3
        # Should be sorted by score descending
        assert entries[0].promotion_score >= entries[1].promotion_score
        db.close()

    def test_get_staging_eligible_for_promotion(self, temp_db_path: Path):
        """Should get only staging entries eligible for promotion."""
        from datetime import datetime

        from rekall.db import Database
        from rekall.models import Source, StagingEntry, generate_ulid

        db = Database(temp_db_path)
        db.init()

        # Below threshold
        low = StagingEntry(
            id=generate_ulid(),
            url="https://low.com/",
            domain="low.com",
            promotion_score=50.0,
        )
        db.add_staging_entry(low)

        # Above threshold
        high = StagingEntry(
            id=generate_ulid(),
            url="https://high.com/",
            domain="high.com",
            promotion_score=90.0,
        )
        db.add_staging_entry(high)

        # Create a real source to reference
        source = Source(domain="promoted.com")
        added_source = db.add_source(source)

        # Already promoted (with valid source reference)
        promoted = StagingEntry(
            id=generate_ulid(),
            url="https://promoted.com/",
            domain="promoted.com",
            promotion_score=95.0,
            promoted_to=added_source.id,
            promoted_at=datetime.now(),
        )
        db.add_staging_entry(promoted)

        eligible = db.get_staging_eligible_for_promotion(threshold=75.0)
        assert len(eligible) == 1
        assert eligible[0].url == "https://high.com/"
        db.close()

    def test_update_staging(self, temp_db_path: Path):
        """Should update staging entry."""
        from rekall.db import Database
        from rekall.models import StagingEntry, generate_ulid

        db = Database(temp_db_path)
        db.init()

        entry = StagingEntry(
            id=generate_ulid(),
            url="https://example.com/",
            domain="example.com",
            title="Original Title",
            citation_count=1,
        )
        db.add_staging_entry(entry)

        # Update entry
        entry.title = "Updated Title"
        entry.citation_count = 5
        db.update_staging(entry)

        # Verify update
        retrieved = db.get_staging_by_url("https://example.com/")
        assert retrieved.title == "Updated Title"
        assert retrieved.citation_count == 5
        db.close()


class TestConnectorImportsCRUD:
    """Tests for connector_imports CRUD operations."""

    def test_upsert_connector_import_insert(self, temp_db_path: Path):
        """Should insert new connector import record."""
        from datetime import datetime

        from rekall.db import Database
        from rekall.models import ConnectorImport

        db = Database(temp_db_path)
        db.init()

        import_record = ConnectorImport(
            connector="claude",
            last_import=datetime.now(),
            last_file_marker="file1.jsonl",
            entries_imported=10,
            errors_count=0,
        )
        db.upsert_connector_import(import_record)

        # Verify inserted
        cursor = db.conn.execute(
            "SELECT * FROM connector_imports WHERE connector = ?", ("claude",)
        )
        row = cursor.fetchone()
        assert row is not None
        assert row["entries_imported"] == 10
        db.close()

    def test_upsert_connector_import_update(self, temp_db_path: Path):
        """Should update existing connector import record."""
        from datetime import datetime

        from rekall.db import Database
        from rekall.models import ConnectorImport

        db = Database(temp_db_path)
        db.init()

        # Initial insert
        import_record = ConnectorImport(
            connector="claude",
            last_import=datetime.now(),
            entries_imported=10,
        )
        db.upsert_connector_import(import_record)

        # Update
        import_record.entries_imported = 25
        import_record.last_file_marker = "file2.jsonl"
        db.upsert_connector_import(import_record)

        # Verify updated (not duplicated)
        cursor = db.conn.execute(
            "SELECT COUNT(*) FROM connector_imports WHERE connector = ?", ("claude",)
        )
        assert cursor.fetchone()[0] == 1

        cursor = db.conn.execute(
            "SELECT entries_imported, last_file_marker FROM connector_imports WHERE connector = ?",
            ("claude",),
        )
        row = cursor.fetchone()
        assert row["entries_imported"] == 25
        assert row["last_file_marker"] == "file2.jsonl"
        db.close()

    def test_get_connector_import(self, temp_db_path: Path):
        """Should retrieve connector import record."""
        from datetime import datetime

        from rekall.db import Database
        from rekall.models import ConnectorImport

        db = Database(temp_db_path)
        db.init()

        # Insert record
        import_record = ConnectorImport(
            connector="cursor",
            last_import=datetime.now(),
            entries_imported=5,
        )
        db.upsert_connector_import(import_record)

        # Retrieve
        retrieved = db.get_connector_import("cursor")
        assert retrieved is not None
        assert retrieved.connector == "cursor"
        assert retrieved.entries_imported == 5

        # Non-existent
        not_found = db.get_connector_import("nonexistent")
        assert not_found is None
        db.close()
