"""Rekall database operations with SQLite + FTS5."""

from __future__ import annotations

import sqlite3
import zlib
from datetime import date, datetime
from pathlib import Path
from typing import Optional

from rekall.models import (
    Embedding,
    Entry,
    EntrySource,
    Link,
    ReviewItem,
    SearchResult,
    Source,
    StructuredContext,
    Suggestion,
    calculate_consolidation_score,
    generate_ulid,
)

# =============================================================================
# Schema Versioning (PRAGMA user_version)
# =============================================================================
# Version history:
#   0 = Initial schema (entries, tags, FTS5)
#   1 = Cognitive memory fields (memory_type, access tracking, spaced repetition)
#   2 = Links table for knowledge graph
#   3 = Smart embeddings (embeddings, suggestions, metadata tables)
#   4 = Context compression (context_compressed column for verification)
#   5 = Link reason (reason column for justification)
#   6 = Structured context (context_structured JSON column for disambiguation)
#   7 = Unified context (context_blob compressed + keywords index table)
#   8 = Sources integration (sources, entry_sources tables for bidirectional linking)

CURRENT_SCHEMA_VERSION = 8

# Migrations dict: version -> list of SQL statements
# Each migration upgrades from version N-1 to version N
MIGRATIONS: dict[int, list[str]] = {
    1: [
        # Add cognitive memory columns to entries
        "ALTER TABLE entries ADD COLUMN memory_type TEXT DEFAULT 'episodic'",
        "ALTER TABLE entries ADD COLUMN last_accessed TEXT",
        "ALTER TABLE entries ADD COLUMN access_count INTEGER DEFAULT 0",
        "ALTER TABLE entries ADD COLUMN consolidation_score REAL DEFAULT 0.0",
        "ALTER TABLE entries ADD COLUMN next_review TEXT",
        "ALTER TABLE entries ADD COLUMN review_interval INTEGER DEFAULT 1",
        "ALTER TABLE entries ADD COLUMN ease_factor REAL DEFAULT 2.5",
        # Initialize last_accessed to created_at for existing entries
        "UPDATE entries SET last_accessed = created_at WHERE last_accessed IS NULL",
        # Initialize access_count to 1 for existing entries
        "UPDATE entries SET access_count = 1 WHERE access_count = 0 OR access_count IS NULL",
        # Create indexes for cognitive memory columns
        "CREATE INDEX IF NOT EXISTS idx_entries_memory_type ON entries(memory_type)",
        "CREATE INDEX IF NOT EXISTS idx_entries_next_review ON entries(next_review)",
        "CREATE INDEX IF NOT EXISTS idx_entries_last_accessed ON entries(last_accessed)",
    ],
    2: [
        # Links table for knowledge graph
        """CREATE TABLE IF NOT EXISTS links (
            id TEXT PRIMARY KEY,
            source_id TEXT NOT NULL,
            target_id TEXT NOT NULL,
            relation_type TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (source_id) REFERENCES entries(id) ON DELETE CASCADE,
            FOREIGN KEY (target_id) REFERENCES entries(id) ON DELETE CASCADE,
            CHECK (relation_type IN ('related', 'supersedes', 'derived_from', 'contradicts')),
            UNIQUE(source_id, target_id, relation_type),
            CHECK (source_id != target_id)
        )""",
        "CREATE INDEX IF NOT EXISTS idx_links_source ON links(source_id)",
        "CREATE INDEX IF NOT EXISTS idx_links_target ON links(target_id)",
        "CREATE INDEX IF NOT EXISTS idx_links_type ON links(relation_type)",
    ],
    3: [
        # Embeddings table for semantic vectors
        """CREATE TABLE IF NOT EXISTS embeddings (
            id TEXT PRIMARY KEY,
            entry_id TEXT NOT NULL,
            embedding_type TEXT NOT NULL,
            vector BLOB NOT NULL,
            dimensions INTEGER NOT NULL,
            model_name TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (entry_id) REFERENCES entries(id) ON DELETE CASCADE,
            CHECK (embedding_type IN ('summary', 'context')),
            CHECK (dimensions IN (128, 384, 768)),
            UNIQUE(entry_id, embedding_type)
        )""",
        "CREATE INDEX IF NOT EXISTS idx_embeddings_entry ON embeddings(entry_id)",
        "CREATE INDEX IF NOT EXISTS idx_embeddings_type ON embeddings(embedding_type)",
        # Suggestions table for link/generalize proposals
        """CREATE TABLE IF NOT EXISTS suggestions (
            id TEXT PRIMARY KEY,
            suggestion_type TEXT NOT NULL,
            entry_ids TEXT NOT NULL,
            reason TEXT,
            score REAL NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            created_at TEXT NOT NULL,
            resolved_at TEXT,
            CHECK (suggestion_type IN ('link', 'generalize')),
            CHECK (status IN ('pending', 'accepted', 'rejected')),
            CHECK (score >= 0.0 AND score <= 1.0)
        )""",
        "CREATE INDEX IF NOT EXISTS idx_suggestions_status ON suggestions(status)",
        "CREATE INDEX IF NOT EXISTS idx_suggestions_type ON suggestions(suggestion_type)",
        "CREATE INDEX IF NOT EXISTS idx_suggestions_created ON suggestions(created_at)",
        # Metadata table for system configuration
        """CREATE TABLE IF NOT EXISTS metadata (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )""",
    ],
    4: [
        # Context compression for verification (zlib compressed text)
        "ALTER TABLE entries ADD COLUMN context_compressed BLOB",
    ],
    5: [
        # Link reason for justification (helps AI understand intent)
        "ALTER TABLE links ADD COLUMN reason TEXT",
    ],
    6: [
        # Structured context JSON for disambiguation (Feature 006)
        "ALTER TABLE entries ADD COLUMN context_structured TEXT",
        # Index for keyword search on structured context
        "CREATE INDEX IF NOT EXISTS idx_entries_context ON entries(context_structured)",
    ],
    7: [
        # Unified context: compressed JSON blob (Feature 007)
        "ALTER TABLE entries ADD COLUMN context_blob BLOB",
        # Keywords index table for fast search (replaces LIKE on JSON)
        """CREATE TABLE IF NOT EXISTS context_keywords (
            entry_id TEXT NOT NULL,
            keyword TEXT NOT NULL,
            FOREIGN KEY (entry_id) REFERENCES entries(id) ON DELETE CASCADE,
            PRIMARY KEY (entry_id, keyword)
        )""",
        "CREATE INDEX IF NOT EXISTS idx_context_keywords ON context_keywords(keyword)",
    ],
    8: [
        # Sources table for curated documentary sources with adaptive scoring (Feature 009)
        """CREATE TABLE IF NOT EXISTS sources (
            id TEXT PRIMARY KEY,
            domain TEXT NOT NULL,
            url_pattern TEXT,
            usage_count INTEGER DEFAULT 0,
            last_used TEXT,
            personal_score REAL DEFAULT 50.0,
            reliability TEXT DEFAULT 'B',
            decay_rate TEXT DEFAULT 'medium',
            last_verified TEXT,
            status TEXT DEFAULT 'active',
            created_at TEXT NOT NULL,
            CHECK (reliability IN ('A', 'B', 'C')),
            CHECK (decay_rate IN ('fast', 'medium', 'slow')),
            CHECK (status IN ('active', 'inaccessible', 'archived'))
        )""",
        # Entry-source links for bidirectional tracking (Feature 009)
        """CREATE TABLE IF NOT EXISTS entry_sources (
            id TEXT PRIMARY KEY,
            entry_id TEXT NOT NULL,
            source_id TEXT,
            source_type TEXT NOT NULL,
            source_ref TEXT NOT NULL,
            note TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (entry_id) REFERENCES entries(id) ON DELETE CASCADE,
            FOREIGN KEY (source_id) REFERENCES sources(id) ON DELETE SET NULL,
            CHECK (source_type IN ('theme', 'url', 'file'))
        )""",
        # Indexes for sources table
        "CREATE INDEX IF NOT EXISTS idx_sources_domain ON sources(domain)",
        "CREATE INDEX IF NOT EXISTS idx_sources_score ON sources(personal_score DESC)",
        "CREATE INDEX IF NOT EXISTS idx_sources_status ON sources(status)",
        # Indexes for entry_sources table
        "CREATE INDEX IF NOT EXISTS idx_entry_sources_entry ON entry_sources(entry_id)",
        "CREATE INDEX IF NOT EXISTS idx_entry_sources_source ON entry_sources(source_id)",
        "CREATE INDEX IF NOT EXISTS idx_entry_sources_type ON entry_sources(source_type)",
    ],
}

# Expected columns for schema verification (Option C - hybrid)
EXPECTED_ENTRY_COLUMNS = {
    "id", "title", "content", "type", "project", "confidence",
    "status", "superseded_by", "created_at", "updated_at",
    "memory_type", "last_accessed", "access_count", "consolidation_score",
    "next_review", "review_interval", "ease_factor", "context_compressed",
    "context_structured",  # Feature 006: Structured context JSON
    "context_blob",  # Feature 007: Compressed structured context
}

EXPECTED_TABLES = {"entries", "tags", "links", "entries_fts", "embeddings", "suggestions", "metadata", "context_keywords", "sources", "entry_sources"}


# SQL statements for schema creation
SCHEMA_ENTRIES = """
CREATE TABLE IF NOT EXISTS entries (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    content TEXT,
    type TEXT NOT NULL,
    project TEXT,
    confidence INTEGER DEFAULT 2,
    status TEXT DEFAULT 'active',
    superseded_by TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,

    FOREIGN KEY (superseded_by) REFERENCES entries(id),
    CHECK (type IN ('bug', 'pattern', 'decision', 'pitfall', 'config', 'reference')),
    CHECK (confidence BETWEEN 0 AND 5),
    CHECK (status IN ('active', 'obsolete'))
);

CREATE INDEX IF NOT EXISTS idx_entries_type ON entries(type);
CREATE INDEX IF NOT EXISTS idx_entries_project ON entries(project);
CREATE INDEX IF NOT EXISTS idx_entries_status ON entries(status);
CREATE INDEX IF NOT EXISTS idx_entries_created ON entries(created_at);
"""

SCHEMA_TAGS = """
CREATE TABLE IF NOT EXISTS tags (
    entry_id TEXT NOT NULL,
    tag TEXT NOT NULL,

    PRIMARY KEY (entry_id, tag),
    FOREIGN KEY (entry_id) REFERENCES entries(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_tags_tag ON tags(tag);
"""

SCHEMA_FTS5 = """
CREATE VIRTUAL TABLE IF NOT EXISTS entries_fts USING fts5(
    id UNINDEXED,
    title,
    content,
    tags,
    tokenize = 'porter unicode61'
);
"""

# Triggers to keep FTS5 index in sync
TRIGGER_INSERT = """
CREATE TRIGGER IF NOT EXISTS entries_ai AFTER INSERT ON entries BEGIN
    INSERT INTO entries_fts(id, title, content, tags)
    VALUES (
        NEW.id,
        NEW.title,
        NEW.content,
        (SELECT GROUP_CONCAT(tag, ' ') FROM tags WHERE entry_id = NEW.id)
    );
END;
"""

TRIGGER_DELETE = """
CREATE TRIGGER IF NOT EXISTS entries_ad AFTER DELETE ON entries BEGIN
    DELETE FROM entries_fts WHERE id = OLD.id;
END;
"""

TRIGGER_UPDATE = """
CREATE TRIGGER IF NOT EXISTS entries_au AFTER UPDATE ON entries BEGIN
    DELETE FROM entries_fts WHERE id = OLD.id;
    INSERT INTO entries_fts(id, title, content, tags)
    VALUES (
        NEW.id,
        NEW.title,
        NEW.content,
        (SELECT GROUP_CONCAT(tag, ' ') FROM tags WHERE entry_id = NEW.id)
    );
END;
"""

# Note: Links table is created via MIGRATIONS[2] for proper versioning


# =============================================================================
# Context Compression Helpers
# =============================================================================

def compress_context(text: str) -> bytes:
    """Compress text context using zlib.

    Args:
        text: Text to compress

    Returns:
        Compressed bytes (typically 70-85% smaller for text)
    """
    return zlib.compress(text.encode("utf-8"), level=6)


def decompress_context(data: bytes) -> str:
    """Decompress context back to text.

    Args:
        data: Compressed bytes

    Returns:
        Original text
    """
    return zlib.decompress(data).decode("utf-8")


class Database:
    """SQLite database with FTS5 for knowledge entries."""

    def __init__(self, db_path: Path):
        """Initialize database connection.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.conn: Optional[sqlite3.Connection] = None

    def init(self) -> None:
        """Initialize database: create directory, connect, create schema."""
        # Ensure directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # Connect with row factory for dict-like access
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row

        # Enable WAL mode for better concurrency
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA synchronous=NORMAL")
        self.conn.execute("PRAGMA foreign_keys=ON")

        # Create schema
        self.conn.executescript(SCHEMA_ENTRIES)
        self.conn.executescript(SCHEMA_TAGS)
        self.conn.execute(SCHEMA_FTS5)

        # Create triggers (must be done one at a time)
        self.conn.execute(TRIGGER_INSERT)
        self.conn.execute(TRIGGER_DELETE)
        self.conn.execute(TRIGGER_UPDATE)

        # Apply migrations (handles cognitive memory fields + links table)
        self._migrate_schema()

        self.conn.commit()

    def _migrate_schema(self) -> None:
        """Apply schema migrations using PRAGMA user_version tracking.

        Implements Option C (Hybrid): Sequential migrations + verification.
        - Uses PRAGMA user_version for version tracking (native SQLite)
        - Applies migrations in order, each in a transaction
        - Verifies final schema matches expected state
        """
        # Get current schema version
        current_version = self.conn.execute("PRAGMA user_version").fetchone()[0]

        # Apply pending migrations
        for version in sorted(MIGRATIONS.keys()):
            if version > current_version:
                self._apply_migration(version)

        # Verify schema integrity (Option C safety check)
        self._verify_schema()

    def _apply_migration(self, version: int) -> None:
        """Apply a single migration version.

        Args:
            version: Target version to migrate to

        Raises:
            sqlite3.Error: If migration fails (transaction rolled back)
        """
        statements = MIGRATIONS.get(version, [])
        if not statements:
            return

        # Each migration in a transaction for atomicity
        try:
            for sql in statements:
                # Handle ALTER TABLE failures gracefully (column may exist)
                if sql.strip().upper().startswith("ALTER TABLE"):
                    try:
                        self.conn.execute(sql)
                    except sqlite3.OperationalError as e:
                        # "duplicate column name" is OK (idempotent)
                        if "duplicate column name" not in str(e).lower():
                            raise
                else:
                    self.conn.execute(sql)

            # Update version after successful migration
            self.conn.execute(f"PRAGMA user_version = {version}")
            self.conn.commit()

        except sqlite3.Error:
            self.conn.rollback()
            raise

    def _verify_schema(self) -> None:
        """Verify schema matches expected state after migrations.

        Raises:
            RuntimeError: If schema is inconsistent
        """
        # Check tables exist
        cursor = self.conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
        actual_tables = {row[0] for row in cursor.fetchall()}
        missing_tables = EXPECTED_TABLES - actual_tables

        if missing_tables:
            raise RuntimeError(
                f"Schema verification failed: missing tables {missing_tables}"
            )

        # Check entries columns
        cursor = self.conn.execute("PRAGMA table_info(entries)")
        actual_columns = {row[1] for row in cursor.fetchall()}
        missing_columns = EXPECTED_ENTRY_COLUMNS - actual_columns

        if missing_columns:
            raise RuntimeError(
                f"Schema verification failed: missing columns in entries: {missing_columns}"
            )

    def get_schema_version(self) -> int:
        """Get current schema version.

        Returns:
            Current PRAGMA user_version value
        """
        return self.conn.execute("PRAGMA user_version").fetchone()[0]

    def close(self) -> None:
        """Close database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None

    def add(self, entry: Entry) -> None:
        """Add a new entry to the database.

        Args:
            entry: Entry to add
        """
        # Set initial last_accessed if not set
        if entry.last_accessed is None:
            entry.last_accessed = entry.created_at

        # Insert entry with cognitive memory fields
        self.conn.execute(
            """
            INSERT INTO entries (id, title, content, type, project, confidence,
                                 status, superseded_by, created_at, updated_at,
                                 memory_type, last_accessed, access_count,
                                 consolidation_score, next_review, review_interval, ease_factor)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                entry.id,
                entry.title,
                entry.content,
                entry.type,
                entry.project,
                entry.confidence,
                entry.status,
                entry.superseded_by,
                entry.created_at.isoformat(),
                entry.updated_at.isoformat(),
                entry.memory_type,
                entry.last_accessed.isoformat() if entry.last_accessed else None,
                entry.access_count,
                entry.consolidation_score,
                entry.next_review.isoformat() if entry.next_review else None,
                entry.review_interval,
                entry.ease_factor,
            ),
        )

        # Insert tags
        for tag in entry.tags:
            self.conn.execute(
                "INSERT INTO tags (entry_id, tag) VALUES (?, ?)",
                (entry.id, tag),
            )

        # Update FTS index (trigger handles main entry, but tags need refresh)
        if entry.tags:
            self._refresh_fts(entry.id)

        self.conn.commit()

    def _refresh_fts(self, entry_id: str) -> None:
        """Refresh FTS index for an entry (to include tags)."""
        self.conn.execute("DELETE FROM entries_fts WHERE id = ?", (entry_id,))
        self.conn.execute(
            """
            INSERT INTO entries_fts(id, title, content, tags)
            SELECT e.id, e.title, e.content,
                   (SELECT GROUP_CONCAT(tag, ' ') FROM tags WHERE entry_id = e.id)
            FROM entries e WHERE e.id = ?
            """,
            (entry_id,),
        )

    def _row_to_entry(self, row: sqlite3.Row, tags: list[str]) -> Entry:
        """Convert a database row to an Entry object.

        Args:
            row: Database row
            tags: List of tags for the entry

        Returns:
            Entry object
        """
        return Entry(
            id=row["id"],
            title=row["title"],
            content=row["content"] or "",
            type=row["type"],
            project=row["project"],
            confidence=row["confidence"],
            status=row["status"],
            superseded_by=row["superseded_by"],
            tags=tags,
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
            memory_type=row["memory_type"] or "episodic",
            last_accessed=(
                datetime.fromisoformat(row["last_accessed"])
                if row["last_accessed"]
                else None
            ),
            access_count=row["access_count"] or 0,
            consolidation_score=row["consolidation_score"] or 0.0,
            next_review=(
                date.fromisoformat(row["next_review"]) if row["next_review"] else None
            ),
            review_interval=row["review_interval"] or 1,
            ease_factor=row["ease_factor"] or 2.5,
        )

    def get(self, entry_id: str, update_access: bool = True) -> Optional[Entry]:
        """Get an entry by ID.

        Args:
            entry_id: ULID of the entry
            update_access: Whether to update access tracking (default True)

        Returns:
            Entry if found, None otherwise
        """
        cursor = self.conn.execute(
            "SELECT * FROM entries WHERE id = ?", (entry_id,)
        )
        row = cursor.fetchone()

        if row is None:
            return None

        # Get tags
        tag_cursor = self.conn.execute(
            "SELECT tag FROM tags WHERE entry_id = ?", (entry_id,)
        )
        tags = [r[0] for r in tag_cursor.fetchall()]

        entry = self._row_to_entry(row, tags)

        # Update access tracking
        if update_access:
            self._update_access_tracking(entry_id)

        return entry

    def update(self, entry: Entry) -> None:
        """Update an existing entry.

        Args:
            entry: Entry with updated fields
        """
        entry.updated_at = datetime.now()

        self.conn.execute(
            """
            UPDATE entries SET
                title = ?, content = ?, type = ?, project = ?, confidence = ?,
                status = ?, superseded_by = ?, updated_at = ?,
                memory_type = ?, last_accessed = ?, access_count = ?,
                consolidation_score = ?, next_review = ?, review_interval = ?, ease_factor = ?
            WHERE id = ?
            """,
            (
                entry.title,
                entry.content,
                entry.type,
                entry.project,
                entry.confidence,
                entry.status,
                entry.superseded_by,
                entry.updated_at.isoformat(),
                entry.memory_type,
                entry.last_accessed.isoformat() if entry.last_accessed else None,
                entry.access_count,
                entry.consolidation_score,
                entry.next_review.isoformat() if entry.next_review else None,
                entry.review_interval,
                entry.ease_factor,
                entry.id,
            ),
        )

        # Update tags: delete all and re-insert
        self.conn.execute("DELETE FROM tags WHERE entry_id = ?", (entry.id,))
        for tag in entry.tags:
            self.conn.execute(
                "INSERT INTO tags (entry_id, tag) VALUES (?, ?)",
                (entry.id, tag),
            )

        self._refresh_fts(entry.id)
        self.conn.commit()

    def delete(self, entry_id: str) -> None:
        """Delete an entry.

        Args:
            entry_id: ULID of the entry to delete
        """
        # Tags deleted by CASCADE, FTS by trigger
        self.conn.execute("DELETE FROM entries WHERE id = ?", (entry_id,))
        self.conn.commit()

    def search(
        self,
        query: str,
        entry_type: Optional[str] = None,
        project: Optional[str] = None,
        memory_type: Optional[str] = None,
        include_obsolete: bool = False,
        limit: int = 20,
        update_access: bool = True,
    ) -> list[SearchResult]:
        """Search entries using FTS5.

        Args:
            query: Search query
            entry_type: Filter by type (optional)
            project: Filter by project (optional)
            memory_type: Filter by memory_type (optional)
            include_obsolete: Include obsolete entries (default False)
            limit: Maximum results to return
            update_access: Whether to update access tracking (default True)

        Returns:
            List of SearchResult ordered by relevance
        """
        # Build query with filters
        sql = """
            SELECT e.*, entries_fts.rank
            FROM entries_fts
            JOIN entries e ON entries_fts.id = e.id
            WHERE entries_fts MATCH ?
        """
        params: list = [query]

        if not include_obsolete:
            sql += " AND e.status = 'active'"

        if entry_type:
            sql += " AND e.type = ?"
            params.append(entry_type)

        if project:
            sql += " AND e.project = ?"
            params.append(project)

        if memory_type:
            sql += " AND e.memory_type = ?"
            params.append(memory_type)

        sql += " ORDER BY rank LIMIT ?"
        params.append(limit)

        cursor = self.conn.execute(sql, params)
        results = []

        for row in cursor.fetchall():
            # Get tags
            tag_cursor = self.conn.execute(
                "SELECT tag FROM tags WHERE entry_id = ?", (row["id"],)
            )
            tags = [r[0] for r in tag_cursor.fetchall()]

            entry = self._row_to_entry(row, tags)
            results.append(SearchResult(entry=entry, rank=row["rank"]))

            # Update access tracking
            if update_access:
                self._update_access_tracking(row["id"])

        return results

    def list_all(
        self,
        entry_type: Optional[str] = None,
        project: Optional[str] = None,
        memory_type: Optional[str] = None,
        include_obsolete: bool = False,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Entry]:
        """List all entries with optional filters.

        Args:
            entry_type: Filter by type (optional)
            project: Filter by project (optional)
            memory_type: Filter by memory_type (optional)
            include_obsolete: Include obsolete entries (default False)
            limit: Maximum results
            offset: Pagination offset

        Returns:
            List of Entry objects
        """
        sql = "SELECT * FROM entries WHERE 1=1"
        params: list = []

        if not include_obsolete:
            sql += " AND status = 'active'"

        if entry_type:
            sql += " AND type = ?"
            params.append(entry_type)

        if project:
            sql += " AND project = ?"
            params.append(project)

        if memory_type:
            sql += " AND memory_type = ?"
            params.append(memory_type)

        sql += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        cursor = self.conn.execute(sql, params)
        entries = []

        for row in cursor.fetchall():
            tag_cursor = self.conn.execute(
                "SELECT tag FROM tags WHERE entry_id = ?", (row["id"],)
            )
            tags = [r[0] for r in tag_cursor.fetchall()]
            entries.append(self._row_to_entry(row, tags))

        return entries

    # =========================================================================
    # Access Tracking Methods (Phase 2)
    # =========================================================================

    def _update_access_tracking(self, entry_id: str) -> None:
        """Update access tracking for an entry.

        Args:
            entry_id: ULID of the entry
        """
        now = datetime.now()
        # Get current values
        cursor = self.conn.execute(
            "SELECT access_count, last_accessed FROM entries WHERE id = ?",
            (entry_id,),
        )
        row = cursor.fetchone()
        if row is None:
            return

        access_count = (row["access_count"] or 0) + 1
        last_accessed = row["last_accessed"]

        # Calculate days since last access for consolidation score
        days_since = 0
        if last_accessed:
            last_dt = datetime.fromisoformat(last_accessed)
            days_since = (now - last_dt).days

        # Calculate new consolidation score
        score = calculate_consolidation_score(access_count, days_since)

        # Update entry
        self.conn.execute(
            """
            UPDATE entries SET
                access_count = ?,
                last_accessed = ?,
                consolidation_score = ?
            WHERE id = ?
            """,
            (access_count, now.isoformat(), score, entry_id),
        )
        self.conn.commit()

    # =========================================================================
    # Link Methods (Phase 2)
    # =========================================================================

    def add_link(
        self,
        source_id: str,
        target_id: str,
        relation_type: str = "related",
        reason: Optional[str] = None,
    ) -> Link:
        """Create a link between two entries.

        Args:
            source_id: Source entry ULID
            target_id: Target entry ULID
            relation_type: Type of relation (default "related")
            reason: Justification for the link (helps AI understand intent)

        Returns:
            Created Link object

        Raises:
            ValueError: If entries don't exist or link already exists
        """
        # Verify entries exist
        if self.get(source_id, update_access=False) is None:
            raise ValueError(f"Source entry not found: {source_id}")
        if self.get(target_id, update_access=False) is None:
            raise ValueError(f"Target entry not found: {target_id}")

        link = Link(
            id=generate_ulid(),
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type,
            reason=reason,
        )

        try:
            self.conn.execute(
                """
                INSERT INTO links (id, source_id, target_id, relation_type, created_at, reason)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    link.id,
                    link.source_id,
                    link.target_id,
                    link.relation_type,
                    link.created_at.isoformat(),
                    link.reason,
                ),
            )
            self.conn.commit()
        except sqlite3.IntegrityError as e:
            if "UNIQUE constraint failed" in str(e):
                raise ValueError(
                    f"Link already exists: {source_id} → [{relation_type}] → {target_id}"
                ) from e
            raise

        return link

    def get_links(
        self,
        entry_id: str,
        relation_type: Optional[str] = None,
        direction: str = "both",
    ) -> list[Link]:
        """Get links for an entry.

        Args:
            entry_id: Entry ULID
            relation_type: Filter by relation type (optional)
            direction: "outgoing", "incoming", or "both" (default)

        Returns:
            List of Link objects
        """
        links = []
        params: list = []

        if direction in ("outgoing", "both"):
            sql = "SELECT * FROM links WHERE source_id = ?"
            params = [entry_id]
            if relation_type:
                sql += " AND relation_type = ?"
                params.append(relation_type)
            cursor = self.conn.execute(sql, params)
            for row in cursor.fetchall():
                links.append(
                    Link(
                        id=row["id"],
                        source_id=row["source_id"],
                        target_id=row["target_id"],
                        relation_type=row["relation_type"],
                        created_at=datetime.fromisoformat(row["created_at"]),
                        reason=row["reason"],
                    )
                )

        if direction in ("incoming", "both"):
            sql = "SELECT * FROM links WHERE target_id = ?"
            params = [entry_id]
            if relation_type:
                sql += " AND relation_type = ?"
                params.append(relation_type)
            cursor = self.conn.execute(sql, params)
            for row in cursor.fetchall():
                links.append(
                    Link(
                        id=row["id"],
                        source_id=row["source_id"],
                        target_id=row["target_id"],
                        relation_type=row["relation_type"],
                        created_at=datetime.fromisoformat(row["created_at"]),
                        reason=row["reason"],
                    )
                )

        return links

    def delete_link(
        self,
        source_id: str,
        target_id: str,
        relation_type: Optional[str] = None,
    ) -> int:
        """Delete link(s) between two entries.

        Args:
            source_id: Source entry ULID
            target_id: Target entry ULID
            relation_type: Specific type to delete (optional, deletes all if None)

        Returns:
            Number of links deleted
        """
        if relation_type:
            cursor = self.conn.execute(
                "DELETE FROM links WHERE source_id = ? AND target_id = ? AND relation_type = ?",
                (source_id, target_id, relation_type),
            )
        else:
            cursor = self.conn.execute(
                "DELETE FROM links WHERE source_id = ? AND target_id = ?",
                (source_id, target_id),
            )
        self.conn.commit()
        return cursor.rowcount

    def count_links(self, entry_id: str) -> int:
        """Count total links for an entry (incoming + outgoing).

        Args:
            entry_id: Entry ULID

        Returns:
            Total number of links (source + target)
        """
        cursor = self.conn.execute(
            "SELECT COUNT(*) FROM links WHERE source_id = ? OR target_id = ?",
            (entry_id, entry_id),
        )
        return cursor.fetchone()[0]

    def get_related_entries(
        self,
        entry_id: str,
        relation_type: Optional[str] = None,
    ) -> list[tuple[Entry, Link]]:
        """Get all entries related to a given entry with their links.

        Args:
            entry_id: Entry ULID
            relation_type: Filter by relation type (optional)

        Returns:
            List of (Entry, Link) tuples for all related entries
        """
        related = []
        links = self.get_links(entry_id, relation_type=relation_type)

        for link in links:
            # Determine the "other" entry ID
            other_id = link.target_id if link.source_id == entry_id else link.source_id
            entry = self.get(other_id, update_access=False)
            if entry:
                related.append((entry, link))

        return related

    def count_links_by_direction(self, entry_id: str) -> tuple[int, int]:
        """Count incoming and outgoing links for an entry.

        Args:
            entry_id: Entry ULID

        Returns:
            Tuple of (incoming_count, outgoing_count)
        """
        cursor = self.conn.execute(
            "SELECT COUNT(*) FROM links WHERE target_id = ?",
            (entry_id,),
        )
        incoming = cursor.fetchone()[0]

        cursor = self.conn.execute(
            "SELECT COUNT(*) FROM links WHERE source_id = ?",
            (entry_id,),
        )
        outgoing = cursor.fetchone()[0]

        return (incoming, outgoing)

    def render_graph_ascii(
        self,
        entry_id: str,
        max_depth: int = 2,
        show_incoming: bool = True,
        show_outgoing: bool = True,
        make_clickable: bool = False,
    ) -> str | tuple[str, list[str]]:
        """Render entry connections as ASCII tree.

        Args:
            entry_id: Starting entry ULID
            max_depth: Maximum depth to traverse (default 2)
            show_incoming: Show incoming links (← referenced by)
            show_outgoing: Show outgoing links (→ references to)
            make_clickable: Add navigation numbers [1]-[9] to connections

        Returns:
            If make_clickable=False: ASCII art string
            If make_clickable=True: Tuple of (ASCII art string, list of navigable IDs)
        """
        entry = self.get(entry_id, update_access=False)
        if not entry:
            return f"Entry not found: {entry_id}"

        lines: list[str] = []
        visited: set[str] = set()

        # Root node
        lines.append(f"[bold cyan]{entry.title}[/bold cyan]")
        lines.append(f"[dim]{entry.id}[/dim]")
        lines.append("")
        visited.add(entry_id)

        # Track IDs for navigation (when make_clickable=True)
        nav_ids: list[str] = []
        nav_counter = [0]  # Use list to allow mutation in nested function

        # Helper to format ID with optional number
        def format_id(eid: str) -> str:
            if make_clickable and nav_counter[0] < 9:
                nav_counter[0] += 1
                nav_ids.append(eid)
                return f"[cyan bold][{nav_counter[0]}][/cyan bold] [dim]{eid}[/dim]"
            return f"[dim]({eid})[/dim]"

        # Collect all connections
        # (direction, type, id, title, reason)
        connections: list[tuple[str, str, str, str, Optional[str]]] = []

        if show_outgoing:
            outgoing = self.get_links(entry_id, direction="outgoing")
            for link in outgoing:
                target = self.get(link.target_id, update_access=False)
                if target:
                    connections.append(
                        ("→", link.relation_type, target.id, target.title, link.reason)
                    )

        if show_incoming:
            incoming = self.get_links(entry_id, direction="incoming")
            for link in incoming:
                source = self.get(link.source_id, update_access=False)
                if source:
                    connections.append(
                        ("←", link.relation_type, source.id, source.title, link.reason)
                    )

        # Render connections
        total = len(connections)
        for i, (direction, rel_type, conn_id, conn_title, reason) in enumerate(connections):
            is_last = (i == total - 1)
            prefix = "╰" if is_last else "├"
            branch = "  " if is_last else "│ "

            # Direction indicator
            dir_symbol = "→" if direction == "→" else "←"

            # Relation type with background color for visibility
            rel_style = {
                "related": "white on blue",
                "supersedes": "black on yellow",
                "derived_from": "white on green",
                "contradicts": "white on red",
            }.get(rel_type, "white")

            lines.append(
                f" {prefix}─{dir_symbol} [{rel_style}] {rel_type} [/{rel_style}] "
                f"[bold]{conn_title[:40]}[/bold]"
            )
            lines.append(f" {branch}  {format_id(conn_id)}")
            # Show reason if available
            if reason:
                lines.append(f" {branch}  [dim italic]→ {reason}[/dim italic]")

            # Recurse if depth allows
            if max_depth > 1 and conn_id not in visited:
                visited.add(conn_id)
                sub_lines = self._render_subtree(
                    conn_id, max_depth - 1, visited, branch, direction,
                    nav_ids, nav_counter if make_clickable else None,
                )
                lines.extend(sub_lines)

        if not connections:
            lines.append(" [dim](aucune connexion)[/dim]")

        output = "\n".join(lines)
        if make_clickable:
            return (output, nav_ids)
        return output

    def _render_subtree(
        self,
        entry_id: str,
        depth: int,
        visited: set[str],
        prefix: str,
        parent_direction: str,
        nav_ids: list[str] | None = None,
        nav_counter: list[int] | None = None,
    ) -> list[str]:
        """Render subtree for recursive graph traversal."""
        lines: list[str] = []

        # Helper to format ID with optional number
        def format_id(eid: str) -> str:
            if nav_counter is not None and nav_counter[0] < 9:
                nav_counter[0] += 1
                nav_ids.append(eid)
                return f"[cyan bold][{nav_counter[0]}][/cyan bold] [dim]{eid}[/dim]"
            return f"[dim]({eid})[/dim]"

        if depth <= 0:
            return lines

        # Only follow same direction to avoid loops
        if parent_direction == "→":
            links = self.get_links(entry_id, direction="outgoing")
            connections = [
                ("→", link.relation_type, link.target_id, link.reason)
                for link in links
                if link.target_id not in visited
            ]
        else:
            links = self.get_links(entry_id, direction="incoming")
            connections = [
                ("←", link.relation_type, link.source_id, link.reason)
                for link in links
                if link.source_id not in visited
            ]

        total = len(connections)
        for i, (direction, rel_type, conn_id, reason) in enumerate(connections):
            is_last = (i == total - 1)
            conn_entry = self.get(conn_id, update_access=False)
            if not conn_entry:
                continue

            visited.add(conn_id)

            branch_char = "╰" if is_last else "├"
            next_prefix = prefix + ("   " if is_last else "│  ")

            # Direction indicator
            dir_symbol = "→" if direction == "→" else "←"

            rel_style = {
                "related": "white on blue",
                "supersedes": "black on yellow",
                "derived_from": "white on green",
                "contradicts": "white on red",
            }.get(rel_type, "white")

            # Format: branch + direction + relation type (colored) + title
            lines.append(
                f" {prefix}{branch_char}─{dir_symbol} [{rel_style}] {rel_type} [/{rel_style}] "
                f"[bold]{conn_entry.title[:40]}[/bold]"
            )
            # ID on separate line for readability
            sub_prefix = prefix + ('   ' if is_last else '│  ')
            lines.append(f" {sub_prefix}  {format_id(conn_id)}")
            # Show reason if available
            if reason:
                lines.append(f" {sub_prefix}  [dim italic]→ {reason}[/dim italic]")

            # Continue recursion
            if depth > 1:
                sub_lines = self._render_subtree(
                    conn_id, depth - 1, visited, next_prefix, direction,
                    nav_ids, nav_counter,
                )
                lines.extend(sub_lines)

        return lines

    # =========================================================================
    # Stale and Review Methods (Phase 2)
    # =========================================================================

    def get_stale_entries(self, days: int = 30, limit: int = 20) -> list[Entry]:
        """Get entries not accessed in the specified number of days.

        Args:
            days: Number of days threshold
            limit: Maximum entries to return

        Returns:
            List of stale entries
        """
        threshold = datetime.now()
        from datetime import timedelta

        threshold = threshold - timedelta(days=days)

        cursor = self.conn.execute(
            """
            SELECT * FROM entries
            WHERE status = 'active'
            AND (last_accessed IS NULL OR last_accessed < ?)
            ORDER BY last_accessed ASC
            LIMIT ?
            """,
            (threshold.isoformat(), limit),
        )

        entries = []
        for row in cursor.fetchall():
            tag_cursor = self.conn.execute(
                "SELECT tag FROM tags WHERE entry_id = ?", (row["id"],)
            )
            tags = [r[0] for r in tag_cursor.fetchall()]
            entries.append(self._row_to_entry(row, tags))

        return entries

    def get_due_entries(
        self,
        limit: int = 10,
        project: Optional[str] = None,
    ) -> list[ReviewItem]:
        """Get entries due for spaced repetition review.

        Args:
            limit: Maximum entries to return
            project: Filter by project (optional)

        Returns:
            List of ReviewItem objects ordered by priority
        """
        today = date.today()
        sql = """
            SELECT * FROM entries
            WHERE status = 'active'
            AND next_review IS NOT NULL
            AND next_review <= ?
        """
        params: list = [today.isoformat()]

        if project:
            sql += " AND project = ?"
            params.append(project)

        sql += " ORDER BY next_review ASC LIMIT ?"
        params.append(limit)

        cursor = self.conn.execute(sql, params)
        items = []

        for row in cursor.fetchall():
            tag_cursor = self.conn.execute(
                "SELECT tag FROM tags WHERE entry_id = ?", (row["id"],)
            )
            tags = [r[0] for r in tag_cursor.fetchall()]
            entry = self._row_to_entry(row, tags)

            # Calculate days overdue
            next_review = date.fromisoformat(row["next_review"])
            days_overdue = (today - next_review).days

            # Priority: higher for more overdue, lower ease factor
            priority = days_overdue + (3.0 - entry.ease_factor)

            items.append(
                ReviewItem(entry=entry, days_overdue=days_overdue, priority=priority)
            )

        # Sort by priority descending
        items.sort(key=lambda x: x.priority, reverse=True)
        return items

    def update_review_schedule(
        self,
        entry_id: str,
        quality: int,
    ) -> None:
        """Update review schedule after a review session.

        Args:
            entry_id: Entry ULID
            quality: User rating 0-5
        """
        from rekall.models import calculate_next_interval

        entry = self.get(entry_id, update_access=False)
        if entry is None:
            return

        # Calculate new interval
        new_interval = calculate_next_interval(entry.review_interval, quality)

        # Update ease factor
        new_ease = entry.ease_factor + 0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02)
        new_ease = max(1.3, new_ease)

        # Calculate next review date
        next_review = date.today()
        from datetime import timedelta

        next_review = next_review + timedelta(days=new_interval)

        self.conn.execute(
            """
            UPDATE entries SET
                review_interval = ?,
                ease_factor = ?,
                next_review = ?
            WHERE id = ?
            """,
            (new_interval, new_ease, next_review.isoformat(), entry_id),
        )
        self.conn.commit()

    # =========================================================================
    # Embedding Methods (Phase 0 - Smart Embeddings)
    # =========================================================================

    def add_embedding(self, embedding: Embedding) -> None:
        """Store an embedding vector.

        Args:
            embedding: Embedding to store
        """
        self.conn.execute(
            """
            INSERT OR REPLACE INTO embeddings
            (id, entry_id, embedding_type, vector, dimensions, model_name, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                embedding.id,
                embedding.entry_id,
                embedding.embedding_type,
                embedding.vector,
                embedding.dimensions,
                embedding.model_name,
                embedding.created_at.isoformat(),
            ),
        )
        self.conn.commit()

    def get_embedding(
        self, entry_id: str, embedding_type: str
    ) -> Optional[Embedding]:
        """Get embedding for entry by type.

        Args:
            entry_id: Entry ULID
            embedding_type: 'summary' or 'context'

        Returns:
            Embedding if found, None otherwise
        """
        cursor = self.conn.execute(
            "SELECT * FROM embeddings WHERE entry_id = ? AND embedding_type = ?",
            (entry_id, embedding_type),
        )
        row = cursor.fetchone()
        if row is None:
            return None

        return Embedding(
            id=row["id"],
            entry_id=row["entry_id"],
            embedding_type=row["embedding_type"],
            vector=row["vector"],
            dimensions=row["dimensions"],
            model_name=row["model_name"],
            created_at=datetime.fromisoformat(row["created_at"]),
        )

    def get_embeddings(self, entry_id: str) -> list[Embedding]:
        """Get all embeddings for an entry (summary + context).

        Args:
            entry_id: Entry ULID

        Returns:
            List of Embedding objects
        """
        cursor = self.conn.execute(
            "SELECT * FROM embeddings WHERE entry_id = ?",
            (entry_id,),
        )
        embeddings = []
        for row in cursor.fetchall():
            embeddings.append(
                Embedding(
                    id=row["id"],
                    entry_id=row["entry_id"],
                    embedding_type=row["embedding_type"],
                    vector=row["vector"],
                    dimensions=row["dimensions"],
                    model_name=row["model_name"],
                    created_at=datetime.fromisoformat(row["created_at"]),
                )
            )
        return embeddings

    def delete_embedding(
        self, entry_id: str, embedding_type: Optional[str] = None
    ) -> int:
        """Delete embedding(s) for entry.

        Args:
            entry_id: Entry ULID
            embedding_type: Specific type to delete (optional, deletes all if None)

        Returns:
            Number of embeddings deleted
        """
        if embedding_type:
            cursor = self.conn.execute(
                "DELETE FROM embeddings WHERE entry_id = ? AND embedding_type = ?",
                (entry_id, embedding_type),
            )
        else:
            cursor = self.conn.execute(
                "DELETE FROM embeddings WHERE entry_id = ?",
                (entry_id,),
            )
        self.conn.commit()
        return cursor.rowcount

    def get_all_embeddings(
        self, embedding_type: Optional[str] = None
    ) -> list[Embedding]:
        """Get all embeddings, optionally filtered by type.

        Args:
            embedding_type: Filter by type (optional)

        Returns:
            List of all Embedding objects
        """
        if embedding_type:
            cursor = self.conn.execute(
                "SELECT * FROM embeddings WHERE embedding_type = ?",
                (embedding_type,),
            )
        else:
            cursor = self.conn.execute("SELECT * FROM embeddings")

        embeddings = []
        for row in cursor.fetchall():
            embeddings.append(
                Embedding(
                    id=row["id"],
                    entry_id=row["entry_id"],
                    embedding_type=row["embedding_type"],
                    vector=row["vector"],
                    dimensions=row["dimensions"],
                    model_name=row["model_name"],
                    created_at=datetime.fromisoformat(row["created_at"]),
                )
            )
        return embeddings

    def count_embeddings(self) -> int:
        """Count total embeddings in database.

        Returns:
            Number of embeddings
        """
        cursor = self.conn.execute("SELECT COUNT(*) FROM embeddings")
        return cursor.fetchone()[0]

    def get_entries_without_embeddings(
        self, embedding_type: str = "summary"
    ) -> list[Entry]:
        """Get entries missing embeddings (for migration).

        Args:
            embedding_type: Type to check for (default: 'summary')

        Returns:
            List of Entry objects without the specified embedding type
        """
        cursor = self.conn.execute(
            """
            SELECT e.* FROM entries e
            WHERE e.status = 'active'
            AND NOT EXISTS (
                SELECT 1 FROM embeddings emb
                WHERE emb.entry_id = e.id AND emb.embedding_type = ?
            )
            """,
            (embedding_type,),
        )

        entries = []
        for row in cursor.fetchall():
            tag_cursor = self.conn.execute(
                "SELECT tag FROM tags WHERE entry_id = ?", (row["id"],)
            )
            tags = [r[0] for r in tag_cursor.fetchall()]
            entries.append(self._row_to_entry(row, tags))

        return entries

    # =========================================================================
    # Suggestion Methods (Phase 0 - Smart Embeddings)
    # =========================================================================

    def add_suggestion(self, suggestion: Suggestion) -> None:
        """Create a new suggestion.

        Args:
            suggestion: Suggestion to create
        """
        self.conn.execute(
            """
            INSERT INTO suggestions
            (id, suggestion_type, entry_ids, reason, score, status, created_at, resolved_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                suggestion.id,
                suggestion.suggestion_type,
                suggestion.entry_ids_json(),
                suggestion.reason,
                suggestion.score,
                suggestion.status,
                suggestion.created_at.isoformat(),
                suggestion.resolved_at.isoformat() if suggestion.resolved_at else None,
            ),
        )
        self.conn.commit()

    def get_suggestion(self, suggestion_id: str) -> Optional[Suggestion]:
        """Get suggestion by ID.

        Args:
            suggestion_id: Suggestion ULID

        Returns:
            Suggestion if found, None otherwise
        """
        cursor = self.conn.execute(
            "SELECT * FROM suggestions WHERE id = ?",
            (suggestion_id,),
        )
        row = cursor.fetchone()
        if row is None:
            return None

        return Suggestion.from_row(dict(row))

    def get_suggestions(
        self,
        status: Optional[str] = None,
        suggestion_type: Optional[str] = None,
        limit: int = 100,
    ) -> list[Suggestion]:
        """Get suggestions with optional filters.

        Args:
            status: Filter by status (optional)
            suggestion_type: Filter by type (optional)
            limit: Maximum results

        Returns:
            List of Suggestion objects
        """
        sql = "SELECT * FROM suggestions WHERE 1=1"
        params: list = []

        if status:
            sql += " AND status = ?"
            params.append(status)

        if suggestion_type:
            sql += " AND suggestion_type = ?"
            params.append(suggestion_type)

        sql += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)

        cursor = self.conn.execute(sql, params)
        return [Suggestion.from_row(dict(row)) for row in cursor.fetchall()]

    def update_suggestion_status(
        self,
        suggestion_id: str,
        status: str,
    ) -> bool:
        """Update suggestion status (accept/reject).

        Args:
            suggestion_id: Suggestion ULID
            status: New status ('accepted' or 'rejected')

        Returns:
            True if updated, False if not found
        """
        resolved_at = datetime.now().isoformat() if status != "pending" else None
        cursor = self.conn.execute(
            """
            UPDATE suggestions SET status = ?, resolved_at = ?
            WHERE id = ?
            """,
            (status, resolved_at, suggestion_id),
        )
        self.conn.commit()
        return cursor.rowcount > 0

    def suggestion_exists(
        self, entry_ids: list[str], suggestion_type: str
    ) -> bool:
        """Check if similar suggestion already exists (avoid duplicates).

        Args:
            entry_ids: List of entry IDs involved
            suggestion_type: Type of suggestion

        Returns:
            True if a pending suggestion with same entries exists
        """
        import json

        # Sort IDs for consistent comparison
        sorted_ids = json.dumps(sorted(entry_ids))

        # Check exact match on sorted entry_ids
        cursor = self.conn.execute(
            """
            SELECT 1 FROM suggestions
            WHERE suggestion_type = ? AND status = 'pending'
            AND entry_ids = ?
            """,
            (suggestion_type, sorted_ids),
        )

        if cursor.fetchone():
            return True

        # For link suggestions, also check reverse order
        if suggestion_type == "link" and len(entry_ids) == 2:
            reverse_ids = json.dumps(sorted(entry_ids, reverse=True))
            cursor = self.conn.execute(
                """
                SELECT 1 FROM suggestions
                WHERE suggestion_type = ? AND status = 'pending'
                AND entry_ids = ?
                """,
                (suggestion_type, reverse_ids),
            )
            return cursor.fetchone() is not None

        return False

    # =========================================================================
    # Metadata Methods (Phase 0 - Smart Embeddings)
    # =========================================================================

    def get_metadata(self, key: str) -> Optional[str]:
        """Get metadata value by key.

        Args:
            key: Metadata key

        Returns:
            Value if found, None otherwise
        """
        cursor = self.conn.execute(
            "SELECT value FROM metadata WHERE key = ?",
            (key,),
        )
        row = cursor.fetchone()
        return row[0] if row else None

    def set_metadata(self, key: str, value: str) -> None:
        """Set metadata key-value pair (upsert).

        Args:
            key: Metadata key
            value: Value to store
        """
        self.conn.execute(
            "INSERT OR REPLACE INTO metadata (key, value) VALUES (?, ?)",
            (key, value),
        )
        self.conn.commit()

    def delete_metadata(self, key: str) -> bool:
        """Delete metadata entry.

        Args:
            key: Metadata key

        Returns:
            True if deleted, False if not found
        """
        cursor = self.conn.execute(
            "DELETE FROM metadata WHERE key = ?",
            (key,),
        )
        self.conn.commit()
        return cursor.rowcount > 0

    def is_first_weekly_call(self) -> bool:
        """Check if this is the first call this ISO week.

        Returns:
            True if first call this week, False otherwise
        """
        from datetime import date

        last_check = self.get_metadata("last_weekly_check")
        if last_check is None:
            return True

        try:
            last_date = date.fromisoformat(last_check)
            today = date.today()
            # Same ISO week?
            return last_date.isocalendar()[:2] != today.isocalendar()[:2]
        except ValueError:
            return True

    def update_weekly_check(self) -> None:
        """Update the weekly check timestamp to today."""
        from datetime import date

        self.set_metadata("last_weekly_check", date.today().isoformat())

    # =========================================================================
    # Context Compression Methods
    # =========================================================================

    def store_context(self, entry_id: str, context: str) -> None:
        """Store compressed context for an entry.

        Useful for AI verification of suggestions - store the conversation
        context that led to the entry creation for later retrieval.

        Args:
            entry_id: Entry ULID
            context: Text context to compress and store
        """
        compressed = compress_context(context)
        self.conn.execute(
            "UPDATE entries SET context_compressed = ? WHERE id = ?",
            (compressed, entry_id),
        )
        self.conn.commit()

    def get_context(self, entry_id: str) -> Optional[str]:
        """Retrieve and decompress context for an entry.

        Args:
            entry_id: Entry ULID

        Returns:
            Decompressed context text, or None if not stored
        """
        row = self.conn.execute(
            "SELECT context_compressed FROM entries WHERE id = ?",
            (entry_id,),
        ).fetchone()

        if row is None or row["context_compressed"] is None:
            return None

        return decompress_context(row["context_compressed"])

    def get_contexts_for_verification(
        self, entry_ids: list[str]
    ) -> dict[str, Optional[str]]:
        """Retrieve contexts for multiple entries (for suggestion verification).

        Args:
            entry_ids: List of entry ULIDs

        Returns:
            Dict mapping entry_id to decompressed context (None if not stored)
        """
        placeholders = ",".join("?" * len(entry_ids))
        rows = self.conn.execute(
            f"SELECT id, context_compressed FROM entries WHERE id IN ({placeholders})",
            entry_ids,
        ).fetchall()

        result = {}
        for row in rows:
            if row["context_compressed"]:
                result[row["id"]] = decompress_context(row["context_compressed"])
            else:
                result[row["id"]] = None

        return result

    def get_context_sizes(self, entry_ids: list[str]) -> dict[str, int]:
        """Get compressed context sizes for multiple entries (single query).

        Args:
            entry_ids: List of entry ULIDs

        Returns:
            Dict mapping entry_id to compressed size in bytes (0 if no context)
        """
        if not entry_ids:
            return {}

        placeholders = ",".join("?" * len(entry_ids))
        rows = self.conn.execute(
            f"SELECT id, LENGTH(context_compressed) as size FROM entries "
            f"WHERE id IN ({placeholders})",
            entry_ids,
        ).fetchall()

        return {row["id"]: row["size"] or 0 for row in rows}

    # =========================================================================
    # Structured Context Methods (Feature 006)
    # =========================================================================

    def store_structured_context(
        self, entry_id: str, context: StructuredContext
    ) -> None:
        """Store structured context for an entry.

        Uses compressed storage in context_blob (v7+) with keywords
        indexed in context_keywords table for fast search.

        Args:
            entry_id: Entry ULID
            context: StructuredContext object to store
        """
        # Compress JSON and store in context_blob
        json_data = context.to_json()
        compressed = compress_context(json_data)

        self.conn.execute(
            "UPDATE entries SET context_blob = ?, context_structured = ? WHERE id = ?",
            (compressed, json_data, entry_id),  # Keep context_structured for backward compat
        )

        # Update keywords index
        self.conn.execute(
            "DELETE FROM context_keywords WHERE entry_id = ?",
            (entry_id,),
        )
        for keyword in context.trigger_keywords:
            self.conn.execute(
                "INSERT OR IGNORE INTO context_keywords (entry_id, keyword) VALUES (?, ?)",
                (entry_id, keyword.lower()),
            )

        self.conn.commit()

    def get_structured_context(self, entry_id: str) -> Optional[StructuredContext]:
        """Get structured context for an entry.

        Reads from context_blob (compressed, v7+) with fallback to
        context_structured (uncompressed, v6) for backward compatibility.

        Args:
            entry_id: Entry ULID

        Returns:
            StructuredContext object if exists, None otherwise
        """
        row = self.conn.execute(
            "SELECT context_blob, context_structured FROM entries WHERE id = ?",
            (entry_id,),
        ).fetchone()

        if not row:
            return None

        # Prefer compressed blob (v7+)
        if row["context_blob"]:
            json_data = decompress_context(row["context_blob"])
            return StructuredContext.from_json(json_data)

        # Fallback to uncompressed (v6)
        if row["context_structured"]:
            return StructuredContext.from_json(row["context_structured"])

        return None

    def search_by_keywords(
        self, keywords: list[str], limit: int = 20
    ) -> list[Entry]:
        """Search entries by trigger keywords in structured context.

        Uses the context_keywords index table (v7+) with fallback to
        LIKE matching on context_structured for backward compatibility.

        Args:
            keywords: List of keywords to search for
            limit: Maximum results to return

        Returns:
            List of Entry objects matching any keyword
        """
        if not keywords:
            return []

        # Normalize keywords
        keywords = [kw.lower().strip() for kw in keywords if kw.strip()]
        if not keywords:
            return []

        # Check if context_keywords table exists (v7+)
        table_exists = self.conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='context_keywords'"
        ).fetchone()

        if table_exists:
            # Use indexed keyword search (v7+)
            placeholders = ",".join("?" * len(keywords))
            query = f"""
                SELECT DISTINCT e.* FROM entries e
                JOIN context_keywords ck ON e.id = ck.entry_id
                WHERE ck.keyword IN ({placeholders})
                ORDER BY e.updated_at DESC
                LIMIT ?
            """
            params = keywords + [limit]
        else:
            # Fallback to LIKE search on JSON (v6)
            conditions = []
            params = []
            for kw in keywords:
                conditions.append("LOWER(context_structured) LIKE ?")
                params.append(f"%{kw}%")

            query = f"""
                SELECT * FROM entries
                WHERE context_structured IS NOT NULL
                AND ({" OR ".join(conditions)})
                ORDER BY updated_at DESC
                LIMIT ?
            """
            params.append(limit)

        rows = self.conn.execute(query, params).fetchall()
        entries = []
        for row in rows:
            tag_cursor = self.conn.execute(
                "SELECT tag FROM tags WHERE entry_id = ?", (row["id"],)
            )
            tags = [r[0] for r in tag_cursor.fetchall()]
            entries.append(self._row_to_entry(row, tags))
        return entries

    def get_entries_with_structured_context(
        self, limit: int = 100
    ) -> list[tuple[Entry, StructuredContext]]:
        """Get all entries that have structured context.

        Args:
            limit: Maximum entries to return

        Returns:
            List of (Entry, StructuredContext) tuples
        """
        rows = self.conn.execute(
            """
            SELECT * FROM entries
            WHERE context_blob IS NOT NULL OR context_structured IS NOT NULL
            ORDER BY updated_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

        result = []
        for row in rows:
            tag_cursor = self.conn.execute(
                "SELECT tag FROM tags WHERE entry_id = ?", (row["id"],)
            )
            tags = [r[0] for r in tag_cursor.fetchall()]
            entry = self._row_to_entry(row, tags)

            # Prefer compressed blob (v7+), fallback to uncompressed (v6)
            if row["context_blob"]:
                json_data = decompress_context(row["context_blob"])
                context = StructuredContext.from_json(json_data)
            else:
                context = StructuredContext.from_json(row["context_structured"])

            result.append((entry, context))
        return result

    def migrate_to_compressed_context(self) -> tuple[int, int]:
        """Migrate existing context data to compressed format (v7).

        This function:
        1. Compresses context_structured JSON into context_blob
        2. Populates context_keywords table from trigger_keywords
        3. Optionally migrates context_compressed into conversation_excerpt

        Returns:
            Tuple of (migrated_count, keywords_added)
        """
        # Get all entries with context_structured but no context_blob
        rows = self.conn.execute(
            """
            SELECT id, context_structured, context_compressed
            FROM entries
            WHERE context_structured IS NOT NULL
            AND (context_blob IS NULL OR context_blob = '')
            """
        ).fetchall()

        migrated_count = 0
        keywords_added = 0

        for row in rows:
            entry_id = row["id"]
            json_data = row["context_structured"]

            try:
                # Parse the structured context
                ctx = StructuredContext.from_json(json_data)

                # If context_compressed exists and conversation_excerpt is empty,
                # migrate the old compressed context
                if row["context_compressed"] and not ctx.conversation_excerpt:
                    try:
                        old_context = decompress_context(row["context_compressed"])
                        # Create new context with conversation_excerpt
                        ctx = StructuredContext(
                            situation=ctx.situation,
                            solution=ctx.solution,
                            trigger_keywords=ctx.trigger_keywords,
                            what_failed=ctx.what_failed,
                            conversation_excerpt=old_context,  # Migrate here
                            files_modified=ctx.files_modified,
                            error_messages=ctx.error_messages,
                            created_at=ctx.created_at,
                            extraction_method=ctx.extraction_method,
                        )
                        json_data = ctx.to_json()
                    except Exception:
                        pass  # Keep original if decompression fails

                # Compress and store
                compressed = compress_context(json_data)
                self.conn.execute(
                    "UPDATE entries SET context_blob = ? WHERE id = ?",
                    (compressed, entry_id),
                )

                # Add keywords to index
                for keyword in ctx.trigger_keywords:
                    self.conn.execute(
                        "INSERT OR IGNORE INTO context_keywords (entry_id, keyword) VALUES (?, ?)",
                        (entry_id, keyword.lower()),
                    )
                    keywords_added += 1

                migrated_count += 1
            except Exception:
                # Skip invalid entries
                continue

        self.conn.commit()
        return (migrated_count, keywords_added)

    def count_entries_without_context_blob(self) -> int:
        """Count entries with context_structured but no context_blob.

        Returns:
            Number of entries needing migration
        """
        row = self.conn.execute(
            """
            SELECT COUNT(*) as count FROM entries
            WHERE context_structured IS NOT NULL
            AND (context_blob IS NULL OR context_blob = '')
            """
        ).fetchone()
        return row["count"] if row else 0

    # =========================================================================
    # Source Methods (Feature 009 - Sources Integration)
    # =========================================================================

    def add_source(self, source: Source) -> Source:
        """Add a new source to the database.

        Args:
            source: Source to add (id will be generated if empty)

        Returns:
            Source with id populated

        Raises:
            ValueError: If source already exists with same domain+url_pattern
        """
        if not source.id:
            source.id = generate_ulid()

        try:
            self.conn.execute(
                """
                INSERT INTO sources
                (id, domain, url_pattern, usage_count, last_used, personal_score,
                 reliability, decay_rate, last_verified, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    source.id,
                    source.domain,
                    source.url_pattern,
                    source.usage_count,
                    source.last_used.isoformat() if source.last_used else None,
                    source.personal_score,
                    source.reliability,
                    source.decay_rate,
                    source.last_verified.isoformat() if source.last_verified else None,
                    source.status,
                    source.created_at.isoformat(),
                ),
            )
            self.conn.commit()
        except sqlite3.IntegrityError as e:
            raise ValueError(f"Source already exists: {source.domain}") from e

        return source

    def get_source(self, source_id: str) -> Optional[Source]:
        """Get a source by ID.

        Args:
            source_id: Source ULID

        Returns:
            Source if found, None otherwise
        """
        row = self.conn.execute(
            "SELECT * FROM sources WHERE id = ?",
            (source_id,),
        ).fetchone()

        if row is None:
            return None

        return self._row_to_source(row)

    def get_source_by_domain(
        self, domain: str, url_pattern: Optional[str] = None
    ) -> Optional[Source]:
        """Get a source by domain (and optional URL pattern).

        Args:
            domain: Domain to search for (e.g., "stackoverflow.com")
            url_pattern: Optional URL pattern for more specific match

        Returns:
            Source if found, None otherwise
        """
        if url_pattern:
            row = self.conn.execute(
                "SELECT * FROM sources WHERE domain = ? AND url_pattern = ?",
                (domain, url_pattern),
            ).fetchone()
        else:
            row = self.conn.execute(
                "SELECT * FROM sources WHERE domain = ? AND url_pattern IS NULL",
                (domain,),
            ).fetchone()

        if row is None:
            return None

        return self._row_to_source(row)

    def _row_to_source(self, row: sqlite3.Row) -> Source:
        """Convert a database row to a Source object.

        Args:
            row: Database row

        Returns:
            Source object
        """
        return Source(
            id=row["id"],
            domain=row["domain"],
            url_pattern=row["url_pattern"],
            usage_count=row["usage_count"] or 0,
            last_used=(
                datetime.fromisoformat(row["last_used"])
                if row["last_used"]
                else None
            ),
            personal_score=row["personal_score"] or 50.0,
            reliability=row["reliability"] or "B",
            decay_rate=row["decay_rate"] or "medium",
            last_verified=(
                datetime.fromisoformat(row["last_verified"])
                if row["last_verified"]
                else None
            ),
            status=row["status"] or "active",
            created_at=datetime.fromisoformat(row["created_at"]),
        )

    def link_entry_to_source(
        self,
        entry_id: str,
        source_type: str,
        source_ref: str,
        source_id: Optional[str] = None,
        note: Optional[str] = None,
    ) -> EntrySource:
        """Link an entry to a source.

        Args:
            entry_id: Entry ULID
            source_type: Type of source ("theme", "url", "file")
            source_ref: Reference (theme name, URL, or file path)
            source_id: Optional Source ULID (for URL sources with curated Source)
            note: Optional note about this specific reference

        Returns:
            Created EntrySource link

        Raises:
            ValueError: If entry doesn't exist
        """
        # Verify entry exists
        if self.get(entry_id, update_access=False) is None:
            raise ValueError(f"Entry not found: {entry_id}")

        link = EntrySource(
            id=generate_ulid(),
            entry_id=entry_id,
            source_id=source_id,
            source_type=source_type,
            source_ref=source_ref,
            note=note,
        )

        self.conn.execute(
            """
            INSERT INTO entry_sources
            (id, entry_id, source_id, source_type, source_ref, note, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                link.id,
                link.entry_id,
                link.source_id,
                link.source_type,
                link.source_ref,
                link.note,
                link.created_at.isoformat(),
            ),
        )
        self.conn.commit()

        # Update source usage stats if linked to a curated source (US3 integration)
        if source_id:
            self.update_source_usage(source_id)

        return link

    def get_entry_sources(self, entry_id: str) -> list[EntrySource]:
        """Get all sources linked to an entry.

        Args:
            entry_id: Entry ULID

        Returns:
            List of EntrySource objects with joined Source data
        """
        rows = self.conn.execute(
            """
            SELECT es.*, s.domain, s.url_pattern, s.usage_count, s.last_used,
                   s.personal_score, s.reliability, s.decay_rate, s.last_verified,
                   s.status, s.created_at as source_created_at
            FROM entry_sources es
            LEFT JOIN sources s ON es.source_id = s.id
            WHERE es.entry_id = ?
            ORDER BY es.created_at DESC
            """,
            (entry_id,),
        ).fetchall()

        result = []
        for row in rows:
            # Build Source if source_id exists
            source = None
            if row["source_id"] and row["domain"]:
                source = Source(
                    id=row["source_id"],
                    domain=row["domain"],
                    url_pattern=row["url_pattern"],
                    usage_count=row["usage_count"] or 0,
                    last_used=(
                        datetime.fromisoformat(row["last_used"])
                        if row["last_used"]
                        else None
                    ),
                    personal_score=row["personal_score"] or 50.0,
                    reliability=row["reliability"] or "B",
                    decay_rate=row["decay_rate"] or "medium",
                    last_verified=(
                        datetime.fromisoformat(row["last_verified"])
                        if row["last_verified"]
                        else None
                    ),
                    status=row["status"] or "active",
                    created_at=datetime.fromisoformat(row["source_created_at"]),
                )

            entry_source = EntrySource(
                id=row["id"],
                entry_id=row["entry_id"],
                source_id=row["source_id"],
                source_type=row["source_type"],
                source_ref=row["source_ref"],
                note=row["note"],
                created_at=datetime.fromisoformat(row["created_at"]),
                source=source,
            )
            result.append(entry_source)

        return result

    def unlink_entry_from_source(self, entry_source_id: str) -> bool:
        """Remove a link between an entry and a source.

        Args:
            entry_source_id: EntrySource ULID

        Returns:
            True if deleted, False if not found
        """
        cursor = self.conn.execute(
            "DELETE FROM entry_sources WHERE id = ?",
            (entry_source_id,),
        )
        self.conn.commit()
        return cursor.rowcount > 0

    def update_source(self, source: Source) -> bool:
        """Update an existing source.

        Args:
            source: Source with updated fields

        Returns:
            True if updated, False if not found
        """
        cursor = self.conn.execute(
            """
            UPDATE sources SET
                domain = ?,
                url_pattern = ?,
                usage_count = ?,
                last_used = ?,
                personal_score = ?,
                reliability = ?,
                decay_rate = ?,
                last_verified = ?,
                status = ?
            WHERE id = ?
            """,
            (
                source.domain,
                source.url_pattern,
                source.usage_count,
                source.last_used.isoformat() if source.last_used else None,
                source.personal_score,
                source.reliability,
                source.decay_rate,
                source.last_verified.isoformat() if source.last_verified else None,
                source.status,
                source.id,
            ),
        )
        self.conn.commit()
        return cursor.rowcount > 0

    def delete_source(self, source_id: str) -> bool:
        """Delete a source (entry_sources.source_id will be set to NULL).

        Args:
            source_id: Source ULID

        Returns:
            True if deleted, False if not found
        """
        cursor = self.conn.execute(
            "DELETE FROM sources WHERE id = ?",
            (source_id,),
        )
        self.conn.commit()
        return cursor.rowcount > 0

    # =========================================================================
    # Backlink Methods (Feature 009 - US2)
    # =========================================================================

    def get_source_backlinks(
        self,
        source_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> list[tuple[Entry, EntrySource]]:
        """Get all entries that cite a specific source (backlinks).

        Args:
            source_id: Source ULID
            limit: Maximum entries to return
            offset: Pagination offset

        Returns:
            List of (Entry, EntrySource) tuples for entries citing this source
        """
        rows = self.conn.execute(
            """
            SELECT e.*, es.id as es_id, es.entry_id, es.source_id, es.source_type,
                   es.source_ref, es.note, es.created_at as es_created_at
            FROM entry_sources es
            JOIN entries e ON es.entry_id = e.id
            WHERE es.source_id = ?
            ORDER BY es.created_at DESC
            LIMIT ? OFFSET ?
            """,
            (source_id, limit, offset),
        ).fetchall()

        result = []
        for row in rows:
            # Get tags for entry
            tag_cursor = self.conn.execute(
                "SELECT tag FROM tags WHERE entry_id = ?", (row["id"],)
            )
            tags = [r[0] for r in tag_cursor.fetchall()]

            entry = self._row_to_entry(row, tags)

            entry_source = EntrySource(
                id=row["es_id"],
                entry_id=row["entry_id"],
                source_id=row["source_id"],
                source_type=row["source_type"],
                source_ref=row["source_ref"],
                note=row["note"],
                created_at=datetime.fromisoformat(row["es_created_at"]),
            )

            result.append((entry, entry_source))

        return result

    def count_source_backlinks(self, source_id: str) -> int:
        """Count entries citing a specific source.

        Args:
            source_id: Source ULID

        Returns:
            Number of entries citing this source
        """
        row = self.conn.execute(
            "SELECT COUNT(*) as count FROM entry_sources WHERE source_id = ?",
            (source_id,),
        ).fetchone()
        return row["count"] if row else 0

    def get_backlinks_by_domain(
        self,
        domain: str,
        limit: int = 50,
    ) -> list[tuple[Entry, EntrySource]]:
        """Get entries citing any source from a given domain.

        Useful for finding all entries that reference a site like
        stackoverflow.com regardless of specific URL pattern.

        Args:
            domain: Domain to search for (e.g., "stackoverflow.com")
            limit: Maximum entries to return

        Returns:
            List of (Entry, EntrySource) tuples
        """
        rows = self.conn.execute(
            """
            SELECT e.*, es.id as es_id, es.entry_id, es.source_id, es.source_type,
                   es.source_ref, es.note, es.created_at as es_created_at
            FROM entry_sources es
            JOIN entries e ON es.entry_id = e.id
            JOIN sources s ON es.source_id = s.id
            WHERE s.domain = ?
            ORDER BY es.created_at DESC
            LIMIT ?
            """,
            (domain, limit),
        ).fetchall()

        result = []
        for row in rows:
            tag_cursor = self.conn.execute(
                "SELECT tag FROM tags WHERE entry_id = ?", (row["id"],)
            )
            tags = [r[0] for r in tag_cursor.fetchall()]

            entry = self._row_to_entry(row, tags)

            entry_source = EntrySource(
                id=row["es_id"],
                entry_id=row["entry_id"],
                source_id=row["source_id"],
                source_type=row["source_type"],
                source_ref=row["source_ref"],
                note=row["note"],
                created_at=datetime.fromisoformat(row["es_created_at"]),
            )

            result.append((entry, entry_source))

        return result

    # =========================================================================
    # Scoring Methods (Feature 009 - US3)
    # =========================================================================

    def calculate_source_score(self, source: Source) -> float:
        """Calculate personal score for a source using composite formula.

        Formula: base_score * usage_factor * recency_factor * reliability_factor

        - base_score: 50 (starting point)
        - usage_factor: log2(usage_count + 1) / 5, capped at 2.0
        - recency_factor: decay based on days since last use
        - reliability_factor: A=1.2, B=1.0, C=0.8

        Args:
            source: Source to calculate score for

        Returns:
            Calculated score (0-100)
        """
        from math import log2

        from rekall.models import DECAY_RATE_HALF_LIVES

        base_score = 50.0

        # Usage factor: logarithmic growth, capped
        usage_factor = min(2.0, log2(source.usage_count + 1) / 5 + 1)

        # Recency factor: exponential decay based on days since last use
        recency_factor = 1.0
        if source.last_used:
            days_since = (datetime.now() - source.last_used).days
            half_life = DECAY_RATE_HALF_LIVES.get(source.decay_rate, 180)
            # Exponential decay: 0.5^(days/half_life)
            recency_factor = 0.5 ** (days_since / half_life)
            # Minimum factor of 0.2 to prevent scores from going to zero
            recency_factor = max(0.2, recency_factor)

        # Reliability factor
        reliability_factors = {"A": 1.2, "B": 1.0, "C": 0.8}
        reliability_factor = reliability_factors.get(source.reliability, 1.0)

        # Calculate final score
        score = base_score * usage_factor * recency_factor * reliability_factor

        # Clamp to 0-100 range
        return min(100.0, max(0.0, score))

    def update_source_usage(self, source_id: str) -> Optional[Source]:
        """Increment usage count and recalculate score for a source.

        Should be called when a source is cited in a new entry.

        Args:
            source_id: Source ULID

        Returns:
            Updated Source with new score, or None if not found
        """
        source = self.get_source(source_id)
        if source is None:
            return None

        # Increment usage
        source.usage_count += 1
        source.last_used = datetime.now()

        # Recalculate score
        source.personal_score = self.calculate_source_score(source)

        # Save
        self.update_source(source)

        return source

    def recalculate_source_score(self, source_id: str) -> Optional[float]:
        """Recalculate and update score for a source (e.g., for decay).

        Args:
            source_id: Source ULID

        Returns:
            New score, or None if source not found
        """
        source = self.get_source(source_id)
        if source is None:
            return None

        # Calculate new score
        new_score = self.calculate_source_score(source)
        source.personal_score = new_score

        # Save
        self.update_source(source)

        return new_score

    def recalculate_all_scores(self) -> int:
        """Recalculate scores for all active sources.

        Useful for daily batch update to apply decay.

        Returns:
            Number of sources updated
        """
        rows = self.conn.execute(
            "SELECT id FROM sources WHERE status = 'active'"
        ).fetchall()

        count = 0
        for row in rows:
            if self.recalculate_source_score(row["id"]) is not None:
                count += 1

        return count

    def get_top_sources(
        self,
        limit: int = 20,
        min_score: float = 0.0,
    ) -> list[Source]:
        """Get sources sorted by personal score (descending).

        Args:
            limit: Maximum sources to return
            min_score: Minimum score threshold

        Returns:
            List of Source objects sorted by score
        """
        rows = self.conn.execute(
            """
            SELECT * FROM sources
            WHERE status = 'active' AND personal_score >= ?
            ORDER BY personal_score DESC
            LIMIT ?
            """,
            (min_score, limit),
        ).fetchall()

        return [self._row_to_source(row) for row in rows]

    def list_sources(
        self,
        status: Optional[str] = None,
        min_score: Optional[float] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Source]:
        """List sources with optional filters and pagination.

        Args:
            status: Filter by status (optional)
            min_score: Minimum score threshold (optional)
            limit: Maximum sources to return
            offset: Pagination offset

        Returns:
            List of Source objects
        """
        sql = "SELECT * FROM sources WHERE 1=1"
        params: list = []

        if status:
            sql += " AND status = ?"
            params.append(status)

        if min_score is not None:
            sql += " AND personal_score >= ?"
            params.append(min_score)

        sql += " ORDER BY personal_score DESC, usage_count DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        rows = self.conn.execute(sql, params).fetchall()
        return [self._row_to_source(row) for row in rows]

    # =========================================================================
    # Search Boost Methods (Feature 009 - US4)
    # =========================================================================

    def get_prioritized_sources_for_theme(
        self,
        theme: str,
        limit: int = 10,
        min_score: float = 20.0,
    ) -> list[Source]:
        """Get sources prioritized by score for a given theme.

        Used for boosting search queries with trusted sources.

        Args:
            theme: Theme to find sources for
            limit: Maximum sources to return
            min_score: Minimum score threshold (default 20 to exclude low-value sources)

        Returns:
            List of Source objects sorted by score
        """
        # Find entry_sources that match the theme
        rows = self.conn.execute(
            """
            SELECT DISTINCT s.*
            FROM sources s
            JOIN entry_sources es ON s.id = es.source_id
            WHERE es.source_type = 'theme'
            AND es.source_ref LIKE ?
            AND s.status = 'active'
            AND s.personal_score >= ?
            ORDER BY s.personal_score DESC
            LIMIT ?
            """,
            (f"%{theme}%", min_score, limit),
        ).fetchall()

        return [self._row_to_source(row) for row in rows]

    def get_sources_for_domain_boost(
        self,
        limit: int = 20,
        min_score: float = 20.0,
    ) -> list[Source]:
        """Get top sources for search domain boosting.

        Returns unique domains with highest scores for building
        site:domain search queries.

        Args:
            limit: Maximum sources to return
            min_score: Minimum score threshold

        Returns:
            List of Source objects (one per domain, highest score)
        """
        # Get best source per domain
        rows = self.conn.execute(
            """
            SELECT s.*
            FROM sources s
            INNER JOIN (
                SELECT domain, MAX(personal_score) as max_score
                FROM sources
                WHERE status = 'active' AND personal_score >= ?
                GROUP BY domain
            ) best ON s.domain = best.domain AND s.personal_score = best.max_score
            ORDER BY s.personal_score DESC
            LIMIT ?
            """,
            (min_score, limit),
        ).fetchall()

        return [self._row_to_source(row) for row in rows]

    # =========================================================================
    # Dashboard Methods (Feature 009 - US5)
    # =========================================================================

    def get_dormant_sources(
        self,
        months: int = 6,
        limit: int = 20,
    ) -> list[Source]:
        """Get sources not used in the specified number of months.

        Args:
            months: Number of months of inactivity (default 6)
            limit: Maximum sources to return

        Returns:
            List of dormant Source objects
        """
        from datetime import timedelta

        cutoff = datetime.now() - timedelta(days=months * 30)

        rows = self.conn.execute(
            """
            SELECT * FROM sources
            WHERE status = 'active'
            AND (last_used IS NULL OR last_used < ?)
            ORDER BY last_used ASC NULLS FIRST
            LIMIT ?
            """,
            (cutoff.isoformat(), limit),
        ).fetchall()

        return [self._row_to_source(row) for row in rows]

    def get_emerging_sources(
        self,
        min_citations: int = 3,
        days: int = 30,
        limit: int = 20,
    ) -> list[Source]:
        """Get sources with high recent citation activity.

        Identifies sources that are being frequently cited recently,
        indicating emerging importance.

        Args:
            min_citations: Minimum citations in the period (default 3)
            days: Number of days to look back (default 30)
            limit: Maximum sources to return

        Returns:
            List of emerging Source objects with citation counts
        """
        from datetime import timedelta

        cutoff = datetime.now() - timedelta(days=days)

        rows = self.conn.execute(
            """
            SELECT s.*, COUNT(es.id) as recent_citations
            FROM sources s
            JOIN entry_sources es ON s.id = es.source_id
            WHERE s.status = 'active'
            AND es.created_at >= ?
            GROUP BY s.id
            HAVING COUNT(es.id) >= ?
            ORDER BY recent_citations DESC, s.personal_score DESC
            LIMIT ?
            """,
            (cutoff.isoformat(), min_citations, limit),
        ).fetchall()

        return [self._row_to_source(row) for row in rows]

    def get_source_statistics(self) -> dict:
        """Get aggregate statistics about sources.

        Returns:
            Dictionary with source statistics
        """
        stats = {}

        # Total counts
        row = self.conn.execute(
            "SELECT COUNT(*) as total FROM sources"
        ).fetchone()
        stats["total"] = row["total"] if row else 0

        # By status
        rows = self.conn.execute(
            "SELECT status, COUNT(*) as count FROM sources GROUP BY status"
        ).fetchall()
        stats["by_status"] = {row["status"]: row["count"] for row in rows}

        # Average score
        row = self.conn.execute(
            "SELECT AVG(personal_score) as avg_score FROM sources WHERE status = 'active'"
        ).fetchone()
        stats["avg_score"] = round(row["avg_score"], 2) if row and row["avg_score"] else 0

        # Total usage
        row = self.conn.execute(
            "SELECT SUM(usage_count) as total_usage FROM sources"
        ).fetchone()
        stats["total_usage"] = row["total_usage"] if row and row["total_usage"] else 0

        # Count of entry_sources links
        row = self.conn.execute(
            "SELECT COUNT(*) as total_links FROM entry_sources"
        ).fetchone()
        stats["total_links"] = row["total_links"] if row else 0

        return stats

    # =========================================================================
    # Link Rot Detection Methods (Feature 009 - US6)
    # =========================================================================

    def get_sources_to_verify(
        self,
        days_since_check: int = 1,
        limit: int = 100,
    ) -> list[Source]:
        """Get sources that need accessibility verification.

        Returns sources that haven't been verified recently or never.

        Args:
            days_since_check: Minimum days since last check (default 1)
            limit: Maximum sources to return

        Returns:
            List of Source objects needing verification
        """
        from datetime import timedelta

        cutoff = datetime.now() - timedelta(days=days_since_check)

        rows = self.conn.execute(
            """
            SELECT * FROM sources
            WHERE domain IS NOT NULL AND domain != ''
            AND (last_verified IS NULL OR last_verified < ?)
            ORDER BY last_verified ASC NULLS FIRST
            LIMIT ?
            """,
            (cutoff.isoformat(), limit),
        ).fetchall()

        return [self._row_to_source(row) for row in rows]

    def update_source_status(
        self,
        source_id: str,
        status: str,
        last_verified: Optional[datetime] = None,
    ) -> bool:
        """Update source status after verification.

        Args:
            source_id: Source ULID
            status: New status ("active", "inaccessible", "archived")
            last_verified: When the check was performed

        Returns:
            True if updated, False if not found
        """
        verify_time = last_verified or datetime.now()

        cursor = self.conn.execute(
            """
            UPDATE sources SET
                status = ?,
                last_verified = ?
            WHERE id = ?
            """,
            (status, verify_time.isoformat(), source_id),
        )
        self.conn.commit()
        return cursor.rowcount > 0

    def get_inaccessible_sources(self, limit: int = 50) -> list[Source]:
        """Get sources marked as inaccessible.

        Args:
            limit: Maximum sources to return

        Returns:
            List of inaccessible Source objects
        """
        rows = self.conn.execute(
            """
            SELECT * FROM sources
            WHERE status = 'inaccessible'
            ORDER BY last_verified DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

        return [self._row_to_source(row) for row in rows]
