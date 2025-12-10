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
        from rekall.db import Database, compress_context
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
