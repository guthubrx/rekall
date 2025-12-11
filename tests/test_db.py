"""Tests for Rekall database (TDD - written before implementation)."""

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

    def test_schema_version_is_8(self, temp_db_path: Path):
        """Schema version should be 8 after migration."""
        from rekall.db import CURRENT_SCHEMA_VERSION, Database

        db = Database(temp_db_path)
        db.init()

        version = db.get_schema_version()
        assert version == 8
        assert version == CURRENT_SCHEMA_VERSION
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
