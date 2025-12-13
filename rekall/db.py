"""Rekall database operations with SQLite + FTS5."""

from __future__ import annotations

import sqlite3
import zlib
from datetime import date, datetime
from pathlib import Path

from rekall.cache import get_embedding_cache
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
from rekall.utils import secure_file_permissions

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
#   9 = Sources autonomes (seed/promoted/role, source_themes, known_domains tables)
#  10 = Saved filters (saved_filters table for persistent filter views)

CURRENT_SCHEMA_VERSION = 11

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
    9: [
        # Feature 010 - Sources Autonomes: Add new columns to sources table
        "ALTER TABLE sources ADD COLUMN is_seed INTEGER DEFAULT 0",
        "ALTER TABLE sources ADD COLUMN is_promoted INTEGER DEFAULT 0",
        "ALTER TABLE sources ADD COLUMN promoted_at TEXT",
        "ALTER TABLE sources ADD COLUMN role TEXT DEFAULT 'unclassified'",
        "ALTER TABLE sources ADD COLUMN seed_origin TEXT",
        "ALTER TABLE sources ADD COLUMN citation_quality_factor REAL DEFAULT 0.0",
        # Indexes for new source columns
        "CREATE INDEX IF NOT EXISTS idx_sources_is_seed ON sources(is_seed)",
        "CREATE INDEX IF NOT EXISTS idx_sources_is_promoted ON sources(is_promoted)",
        "CREATE INDEX IF NOT EXISTS idx_sources_role ON sources(role)",
        # Source themes junction table (many-to-many)
        """CREATE TABLE IF NOT EXISTS source_themes (
            source_id TEXT NOT NULL,
            theme TEXT NOT NULL,
            PRIMARY KEY (source_id, theme),
            FOREIGN KEY (source_id) REFERENCES sources(id) ON DELETE CASCADE
        )""",
        "CREATE INDEX IF NOT EXISTS idx_source_themes_theme ON source_themes(theme)",
        # Known domains for automatic hub/authority classification
        """CREATE TABLE IF NOT EXISTS known_domains (
            domain TEXT PRIMARY KEY,
            role TEXT NOT NULL CHECK(role IN ('hub', 'authority')),
            notes TEXT,
            created_at TEXT NOT NULL
        )""",
        # Insert initial known domains (authorities - official documentation)
        "INSERT OR IGNORE INTO known_domains VALUES ('developer.mozilla.org', 'authority', 'MDN Web Docs', datetime('now'))",
        "INSERT OR IGNORE INTO known_domains VALUES ('docs.python.org', 'authority', 'Python docs', datetime('now'))",
        "INSERT OR IGNORE INTO known_domains VALUES ('tc39.es', 'authority', 'ECMAScript specs', datetime('now'))",
        "INSERT OR IGNORE INTO known_domains VALUES ('www.w3.org', 'authority', 'W3C specs', datetime('now'))",
        "INSERT OR IGNORE INTO known_domains VALUES ('www.rfc-editor.org', 'authority', 'RFCs', datetime('now'))",
        "INSERT OR IGNORE INTO known_domains VALUES ('rust-lang.org', 'authority', 'Rust docs', datetime('now'))",
        "INSERT OR IGNORE INTO known_domains VALUES ('go.dev', 'authority', 'Go docs', datetime('now'))",
        "INSERT OR IGNORE INTO known_domains VALUES ('react.dev', 'authority', 'React docs', datetime('now'))",
        "INSERT OR IGNORE INTO known_domains VALUES ('vuejs.org', 'authority', 'Vue docs', datetime('now'))",
        "INSERT OR IGNORE INTO known_domains VALUES ('angular.io', 'authority', 'Angular docs', datetime('now'))",
        "INSERT OR IGNORE INTO known_domains VALUES ('nodejs.org', 'authority', 'Node.js docs', datetime('now'))",
        "INSERT OR IGNORE INTO known_domains VALUES ('www.typescriptlang.org', 'authority', 'TypeScript docs', datetime('now'))",
        "INSERT OR IGNORE INTO known_domains VALUES ('kubernetes.io', 'authority', 'K8s docs', datetime('now'))",
        "INSERT OR IGNORE INTO known_domains VALUES ('docs.docker.com', 'authority', 'Docker docs', datetime('now'))",
        "INSERT OR IGNORE INTO known_domains VALUES ('www.sqlite.org', 'authority', 'SQLite docs', datetime('now'))",
        "INSERT OR IGNORE INTO known_domains VALUES ('www.postgresql.org', 'authority', 'PostgreSQL docs', datetime('now'))",
        # Insert initial known domains (hubs - aggregators, forums, news)
        "INSERT OR IGNORE INTO known_domains VALUES ('stackoverflow.com', 'hub', 'Q&A dev', datetime('now'))",
        "INSERT OR IGNORE INTO known_domains VALUES ('news.ycombinator.com', 'hub', 'Hacker News', datetime('now'))",
        "INSERT OR IGNORE INTO known_domains VALUES ('reddit.com', 'hub', 'Reddit', datetime('now'))",
        "INSERT OR IGNORE INTO known_domains VALUES ('github.com', 'hub', 'GitHub repos/issues', datetime('now'))",
        "INSERT OR IGNORE INTO known_domains VALUES ('dev.to', 'hub', 'Dev community', datetime('now'))",
        "INSERT OR IGNORE INTO known_domains VALUES ('medium.com', 'hub', 'Blog platform', datetime('now'))",
        "INSERT OR IGNORE INTO known_domains VALUES ('hashnode.dev', 'hub', 'Blog platform', datetime('now'))",
        "INSERT OR IGNORE INTO known_domains VALUES ('lobste.rs', 'hub', 'Tech news', datetime('now'))",
        "INSERT OR IGNORE INTO known_domains VALUES ('slashdot.org', 'hub', 'Tech news', datetime('now'))",
    ],
    10: [
        # Feature 012 - Sources Organisation: Saved filters table
        """CREATE TABLE IF NOT EXISTS saved_filters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            filter_json TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        )""",
        "CREATE INDEX IF NOT EXISTS idx_saved_filters_name ON saved_filters(name)",
    ],
    11: [
        # Feature 013 - Sources Medallion: Bronze layer (inbox)
        """CREATE TABLE IF NOT EXISTS sources_inbox (
            id TEXT PRIMARY KEY,
            url TEXT NOT NULL,
            domain TEXT,
            cli_source TEXT NOT NULL,
            project TEXT,
            conversation_id TEXT,
            user_query TEXT,
            assistant_snippet TEXT,
            surrounding_text TEXT,
            captured_at TEXT DEFAULT (datetime('now')),
            import_source TEXT,
            raw_json TEXT,
            is_valid INTEGER DEFAULT 1,
            validation_error TEXT,
            enriched_at TEXT
        )""",
        "CREATE INDEX IF NOT EXISTS idx_inbox_url ON sources_inbox(url)",
        "CREATE INDEX IF NOT EXISTS idx_inbox_domain ON sources_inbox(domain)",
        "CREATE INDEX IF NOT EXISTS idx_inbox_cli ON sources_inbox(cli_source)",
        "CREATE INDEX IF NOT EXISTS idx_inbox_captured ON sources_inbox(captured_at)",
        "CREATE INDEX IF NOT EXISTS idx_inbox_valid ON sources_inbox(is_valid)",
        "CREATE INDEX IF NOT EXISTS idx_inbox_enriched ON sources_inbox(enriched_at)",
        # Feature 013 - Sources Medallion: Silver layer (staging)
        """CREATE TABLE IF NOT EXISTS sources_staging (
            id TEXT PRIMARY KEY,
            url TEXT NOT NULL UNIQUE,
            domain TEXT NOT NULL,
            title TEXT,
            description TEXT,
            content_type TEXT,
            language TEXT,
            last_verified TEXT,
            is_accessible INTEGER DEFAULT 1,
            http_status INTEGER,
            citation_count INTEGER DEFAULT 1,
            project_count INTEGER DEFAULT 1,
            projects_list TEXT,
            first_seen TEXT,
            last_seen TEXT,
            promotion_score REAL DEFAULT 0.0,
            inbox_ids TEXT,
            enriched_at TEXT,
            promoted_at TEXT,
            promoted_to TEXT,
            FOREIGN KEY (promoted_to) REFERENCES sources(id) ON DELETE SET NULL
        )""",
        "CREATE INDEX IF NOT EXISTS idx_staging_domain ON sources_staging(domain)",
        "CREATE INDEX IF NOT EXISTS idx_staging_score ON sources_staging(promotion_score DESC)",
        "CREATE INDEX IF NOT EXISTS idx_staging_promoted ON sources_staging(promoted_at)",
        "CREATE INDEX IF NOT EXISTS idx_staging_content_type ON sources_staging(content_type)",
        # Feature 013 - Sources Medallion: CDC tracking
        """CREATE TABLE IF NOT EXISTS connector_imports (
            connector TEXT PRIMARY KEY,
            last_import TEXT,
            last_file_marker TEXT,
            entries_imported INTEGER DEFAULT 0,
            errors_count INTEGER DEFAULT 0
        )""",
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

EXPECTED_TABLES = {"entries", "tags", "links", "entries_fts", "embeddings", "suggestions", "metadata", "context_keywords", "sources", "entry_sources", "source_themes", "known_domains", "sources_inbox", "sources_staging", "connector_imports"}


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
        self.conn: sqlite3.Connection | None = None

    def init(self) -> None:
        """Initialize database: create directory, connect, create schema."""
        # Ensure directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # Connect with row factory for dict-like access
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row

        # Secure file permissions (rw------- for sensitive data)
        secure_file_permissions(self.db_path)

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

    def get(self, entry_id: str, update_access: bool = True) -> Entry | None:
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

        # Invalidate embedding cache for modified entry (Feature 020)
        get_embedding_cache().invalidate(entry.id)

    def delete(self, entry_id: str) -> None:
        """Delete an entry.

        Args:
            entry_id: ULID of the entry to delete
        """
        # Tags deleted by CASCADE, FTS by trigger
        self.conn.execute("DELETE FROM entries WHERE id = ?", (entry_id,))
        self.conn.commit()

        # Invalidate embedding cache for deleted entry (Feature 020)
        get_embedding_cache().invalidate(entry_id)

    def search(
        self,
        query: str,
        entry_type: str | None = None,
        project: str | None = None,
        memory_type: str | None = None,
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
        entry_type: str | None = None,
        project: str | None = None,
        memory_type: str | None = None,
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
        reason: str | None = None,
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
        relation_type: str | None = None,
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
        relation_type: str | None = None,
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
        relation_type: str | None = None,
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
        connections: list[tuple[str, str, str, str, str | None]] = []

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
        project: str | None = None,
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
    ) -> Embedding | None:
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
        self, entry_id: str, embedding_type: str | None = None
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
        self, embedding_type: str | None = None
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

    def get_all_vectors_batch(
        self, embedding_type: str = "summary"
    ) -> tuple[list[str], "ndarray"] | None:  # ndarray from numpy
        """Get all embedding vectors as a numpy matrix for batch operations.

        This method is optimized for vectorized similarity computation.
        Returns entry_ids and vectors as a single numpy array.

        Args:
            embedding_type: Filter by type (default: 'summary')

        Returns:
            Tuple of (entry_ids list, vectors ndarray) or None if no embeddings
            The vectors array has shape (N, D) where N is count, D is dimensions.
        """
        import numpy as np

        cursor = self.conn.execute(
            "SELECT entry_id, vector FROM embeddings WHERE embedding_type = ?",
            (embedding_type,),
        )

        entry_ids: list[str] = []
        vectors: list[np.ndarray] = []

        for row in cursor.fetchall():
            entry_ids.append(row["entry_id"])
            # Deserialize blob to numpy array
            vec = np.frombuffer(row["vector"], dtype=np.float32)
            vectors.append(vec)

        if not entry_ids:
            return None

        # Stack into (N, D) matrix
        vectors_matrix = np.vstack(vectors)
        return entry_ids, vectors_matrix

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

    def get_suggestion(self, suggestion_id: str) -> Suggestion | None:
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
        status: str | None = None,
        suggestion_type: str | None = None,
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

    def get_metadata(self, key: str) -> str | None:
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

    def get_context(self, entry_id: str) -> str | None:
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
    ) -> dict[str, str | None]:
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

    def get_structured_context(self, entry_id: str) -> StructuredContext | None:
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

        Auto-classifies the source based on known domains if role is unclassified.

        Args:
            source: Source to add (id will be generated if empty)

        Returns:
            Source with id populated

        Raises:
            ValueError: If source already exists with same domain+url_pattern
        """
        if not source.id:
            source.id = generate_ulid()

        # Auto-classify if role is unclassified (Feature 010)
        if source.role == "unclassified":
            known = self.get_known_domain(source.domain)
            if known:
                source.role = known["role"]

        try:
            self.conn.execute(
                """
                INSERT INTO sources
                (id, domain, url_pattern, usage_count, last_used, personal_score,
                 reliability, decay_rate, last_verified, status, created_at,
                 is_seed, is_promoted, promoted_at, role, seed_origin, citation_quality_factor)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                    1 if source.is_seed else 0,
                    1 if source.is_promoted else 0,
                    source.promoted_at.isoformat() if source.promoted_at else None,
                    source.role,
                    source.seed_origin,
                    source.citation_quality_factor,
                ),
            )
            self.conn.commit()
        except sqlite3.IntegrityError as e:
            raise ValueError(f"Source already exists: {source.domain}") from e

        return source

    def get_source(self, source_id: str) -> Source | None:
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
        self, domain: str, url_pattern: str | None = None
    ) -> Source | None:
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

    def get_source_by_url(self, url: str) -> Optional[Source]:
        """Get a source by exact URL (stored as url_pattern).

        Args:
            url: Full URL to search for

        Returns:
            Source if found, None otherwise
        """
        row = self.conn.execute(
            "SELECT * FROM sources WHERE url_pattern = ?",
            (url,),
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
        # Handle v9 fields with defaults for backward compatibility
        is_seed = bool(row["is_seed"]) if "is_seed" in row.keys() else False
        is_promoted = bool(row["is_promoted"]) if "is_promoted" in row.keys() else False
        promoted_at = None
        if "promoted_at" in row.keys() and row["promoted_at"]:
            promoted_at = datetime.fromisoformat(row["promoted_at"])
        role = row["role"] if "role" in row.keys() else "unclassified"
        seed_origin = row["seed_origin"] if "seed_origin" in row.keys() else None
        citation_quality = row["citation_quality_factor"] if "citation_quality_factor" in row.keys() else 0.0

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
            is_seed=is_seed,
            is_promoted=is_promoted,
            promoted_at=promoted_at,
            role=role or "unclassified",
            seed_origin=seed_origin,
            citation_quality_factor=citation_quality or 0.0,
        )

    def link_entry_to_source(
        self,
        entry_id: str,
        source_type: str,
        source_ref: str,
        source_id: str | None = None,
        note: str | None = None,
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

    def calculate_citation_quality(self, source_id: str) -> float:
        """Calculate citation quality factor based on co-citation patterns.

        Citation quality measures how often this source is cited alongside
        high-quality sources (seeds, authorities, promoted). Higher scores
        indicate the source appears in contexts with trusted sources.

        Formula: weighted_cocitations / total_cocitations
        - Seed co-citation: 1.5
        - Authority co-citation: 1.3
        - Promoted co-citation: 1.2
        - Normal co-citation: 1.0

        Args:
            source_id: Source ULID

        Returns:
            Citation quality factor (0.0 to 1.0)
        """
        # Get all entries citing this source
        cited_entries = self.conn.execute(
            "SELECT entry_id FROM entry_sources WHERE source_id = ?",
            (source_id,)
        ).fetchall()

        if not cited_entries:
            return 0.0

        entry_ids = [row["entry_id"] for row in cited_entries]

        # Get all co-cited sources for these entries
        placeholders = ",".join("?" * len(entry_ids))
        co_citations = self.conn.execute(
            f"""
            SELECT s.is_seed, s.is_promoted, s.role
            FROM entry_sources es
            JOIN sources s ON es.source_id = s.id
            WHERE es.entry_id IN ({placeholders})
              AND es.source_id != ?
            """,
            (*entry_ids, source_id)
        ).fetchall()

        if not co_citations:
            return 0.0

        # Calculate weighted sum
        total_weight = 0.0
        for cocite in co_citations:
            weight = 1.0
            if cocite["is_seed"]:
                weight = max(weight, 1.5)
            if cocite["role"] == "authority":
                weight = max(weight, 1.3)
            if cocite["is_promoted"]:
                weight = max(weight, 1.2)
            total_weight += weight

        # Normalize to 0.0-1.0 range
        # Max possible weight is 1.5 * len(co_citations)
        max_weight = 1.5 * len(co_citations)
        quality_factor = total_weight / max_weight if max_weight > 0 else 0.0

        return round(quality_factor, 3)

    def calculate_source_score_v2(self, source: Source) -> float:
        """Calculate personal score v2 with role bonus, seed bonus, and citation quality.

        Enhanced formula from Feature 010 - Sources Autonomes:
        score_v2 = base_score * usage_factor * recency_factor * reliability_factor
                   * role_bonus * seed_bonus * (1 + citation_quality_factor * 0.2)

        New factors (v2):
        - role_bonus: authority=1.2x, hub=1.0x, unclassified=1.0x
        - seed_bonus: 1.2x for seed sources
        - citation_quality_factor: 0-20% boost based on co-citation quality

        Args:
            source: Source to calculate score for

        Returns:
            Calculated score (0-100)
        """
        from math import log2

        from rekall.models import DECAY_RATE_HALF_LIVES, ROLE_BONUS, SEED_BONUS

        base_score = 50.0

        # Usage factor: logarithmic growth, capped
        usage_factor = min(2.0, log2(source.usage_count + 1) / 5 + 1)

        # Recency factor: exponential decay based on days since last use
        recency_factor = 1.0
        if source.last_used:
            days_since = (datetime.now() - source.last_used).days
            half_life = DECAY_RATE_HALF_LIVES.get(source.decay_rate, 180)
            recency_factor = 0.5 ** (days_since / half_life)
            recency_factor = max(0.2, recency_factor)

        # Reliability factor
        reliability_factors = {"A": 1.2, "B": 1.0, "C": 0.8}
        reliability_factor = reliability_factors.get(source.reliability, 1.0)

        # V2 factors
        role_bonus = ROLE_BONUS.get(source.role, 1.0)
        seed_bonus = SEED_BONUS if source.is_seed else 1.0

        # Citation quality adds up to 20% boost
        cq_factor = source.citation_quality_factor or 0.0
        citation_bonus = 1 + (cq_factor * 0.2)

        # Calculate final score
        score = (
            base_score
            * usage_factor
            * recency_factor
            * reliability_factor
            * role_bonus
            * seed_bonus
            * citation_bonus
        )

        # Clamp to 0-100 range
        return min(100.0, max(0.0, score))

    def update_citation_quality(self, source_id: str) -> float | None:
        """Update citation quality factor for a source.

        Args:
            source_id: Source ULID

        Returns:
            New citation quality factor, or None if source not found
        """
        source = self.get_source(source_id)
        if source is None:
            return None

        # Calculate new citation quality
        cq_factor = self.calculate_citation_quality(source_id)

        # Update in database
        self.conn.execute(
            "UPDATE sources SET citation_quality_factor = ? WHERE id = ?",
            (cq_factor, source_id)
        )
        self.conn.commit()

        return cq_factor

    def update_source_usage(self, source_id: str) -> Source | None:
        """Increment usage count and recalculate score for a source.

        Should be called when a source is cited in a new entry.
        Uses score v2 formula with role bonus, seed bonus, and citation quality.

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

        # Recalculate score using v2 formula
        source.personal_score = self.calculate_source_score_v2(source)

        # Save
        self.update_source(source)

        return source

    def recalculate_source_score(
        self,
        source_id: str,
        update_citation_quality: bool = True
    ) -> float | None:
        """Recalculate and update score for a source (e.g., for decay).

        Uses score v2 formula with role bonus, seed bonus, and citation quality.

        Args:
            source_id: Source ULID
            update_citation_quality: Also recalculate citation quality factor

        Returns:
            New score, or None if source not found
        """
        source = self.get_source(source_id)
        if source is None:
            return None

        # Update citation quality first if requested
        if update_citation_quality:
            cq_factor = self.calculate_citation_quality(source_id)
            source.citation_quality_factor = cq_factor
            self.conn.execute(
                "UPDATE sources SET citation_quality_factor = ? WHERE id = ?",
                (cq_factor, source_id)
            )

        # Calculate new score using v2 formula
        new_score = self.calculate_source_score_v2(source)
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
        status: str | None = None,
        min_score: float | None = None,
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
        last_verified: datetime | None = None,
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

    # =========================================================================
    # Feature 010: Sources Autonomes - Theme Management
    # =========================================================================

    def add_source_theme(self, source_id: str, theme: str) -> bool:
        """Add a theme to a source.

        Args:
            source_id: Source ULID
            theme: Theme name (kebab-case)

        Returns:
            True if added, False if already exists
        """
        try:
            self.conn.execute(
                "INSERT INTO source_themes (source_id, theme) VALUES (?, ?)",
                (source_id, theme.lower().strip()),
            )
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False  # Already exists

    def get_source_themes(self, source_id: str) -> list[str]:
        """Get all themes for a source.

        Args:
            source_id: Source ULID

        Returns:
            List of theme names
        """
        rows = self.conn.execute(
            "SELECT theme FROM source_themes WHERE source_id = ? ORDER BY theme",
            (source_id,),
        ).fetchall()
        return [row["theme"] for row in rows]

    def remove_source_theme(self, source_id: str, theme: str) -> bool:
        """Remove a theme from a source.

        Args:
            source_id: Source ULID
            theme: Theme name

        Returns:
            True if removed, False if not found
        """
        cursor = self.conn.execute(
            "DELETE FROM source_themes WHERE source_id = ? AND theme = ?",
            (source_id, theme.lower().strip()),
        )
        self.conn.commit()
        return cursor.rowcount > 0

    def update_source_as_seed(
        self,
        source_id: str,
        seed_origin: str,
        role: Optional[str] = None,
    ) -> bool:
        """Mark a source as a seed (migrated from speckit).

        Args:
            source_id: Source ULID
            seed_origin: Path to original speckit file
            role: Optional role override (hub/authority/unclassified)

        Returns:
            True if updated, False if source not found
        """
        if role:
            cursor = self.conn.execute(
                """
                UPDATE sources
                SET is_seed = 1, seed_origin = ?, role = ?
                WHERE id = ?
                """,
                (seed_origin, role, source_id),
            )
        else:
            cursor = self.conn.execute(
                """
                UPDATE sources
                SET is_seed = 1, seed_origin = ?
                WHERE id = ?
                """,
                (seed_origin, source_id),
            )
        self.conn.commit()
        return cursor.rowcount > 0

    def get_seed_sources(self, limit: int = 100) -> list[Source]:
        """Get all seed sources (migrated from speckit).

        Args:
            limit: Maximum sources to return

        Returns:
            List of seed Source objects
        """
        rows = self.conn.execute(
            """
            SELECT * FROM sources
            WHERE is_seed = 1
            ORDER BY personal_score DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        return [self._row_to_source(row) for row in rows]

    # =========================================================================
    # Feature 010: Sources Autonomes - Known Domains
    # =========================================================================

    def get_known_domain(self, domain: str) -> Optional[dict]:
        """Get known domain classification.

        Args:
            domain: Domain to look up

        Returns:
            Dict with role and notes, or None if not found
        """
        row = self.conn.execute(
            "SELECT domain, role, notes FROM known_domains WHERE domain = ?",
            (domain.lower(),),
        ).fetchone()
        if row:
            return {"domain": row["domain"], "role": row["role"], "notes": row["notes"]}
        return None

    def add_known_domain(self, domain: str, role: str, notes: Optional[str] = None) -> bool:
        """Add a domain to known domains for auto-classification.

        Args:
            domain: Domain name
            role: hub or authority
            notes: Optional description

        Returns:
            True if added, False if already exists
        """
        try:
            self.conn.execute(
                """
                INSERT INTO known_domains (domain, role, notes, created_at)
                VALUES (?, ?, ?, datetime('now'))
                """,
                (domain.lower(), role, notes),
            )
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    # =========================================================================
    # Feature 010: Sources Autonomes - Promotion System (US2)
    # =========================================================================

    def check_promotion_criteria(self, source: Source) -> bool:
        """Check if a source meets promotion criteria.

        Criteria:
        - usage_count >= 3
        - personal_score >= 30
        - last_used within 180 days

        Args:
            source: Source to check

        Returns:
            True if source meets all criteria
        """
        from rekall.models import PROMOTION_THRESHOLDS

        # Check usage count
        if source.usage_count < PROMOTION_THRESHOLDS["min_usage_count"]:
            return False

        # Check score
        if source.personal_score < PROMOTION_THRESHOLDS["min_score"]:
            return False

        # Check recency
        if source.last_used:
            days_since_use = (datetime.now() - source.last_used).days
            if days_since_use > PROMOTION_THRESHOLDS["max_days_inactive"]:
                return False
        else:
            return False  # Never used = not promotable

        return True

    def promote_source(self, source_id: str) -> bool:
        """Promote a source (mark as is_promoted=1).

        Args:
            source_id: Source ULID

        Returns:
            True if promoted, False if not found
        """
        cursor = self.conn.execute(
            """
            UPDATE sources
            SET is_promoted = 1, promoted_at = datetime('now')
            WHERE id = ?
            """,
            (source_id,),
        )
        self.conn.commit()
        return cursor.rowcount > 0

    def demote_source(self, source_id: str) -> bool:
        """Demote a source (mark as is_promoted=0).

        Does NOT demote seed sources (is_seed=1).

        Args:
            source_id: Source ULID

        Returns:
            True if demoted, False if not found or is seed
        """
        cursor = self.conn.execute(
            """
            UPDATE sources
            SET is_promoted = 0, promoted_at = NULL
            WHERE id = ? AND is_seed = 0
            """,
            (source_id,),
        )
        self.conn.commit()
        return cursor.rowcount > 0

    def get_promoted_sources(self, limit: int = 100) -> list[Source]:
        """Get all promoted sources.

        Args:
            limit: Maximum sources to return

        Returns:
            List of promoted Source objects
        """
        rows = self.conn.execute(
            """
            SELECT * FROM sources
            WHERE is_promoted = 1
            ORDER BY personal_score DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        return [self._row_to_source(row) for row in rows]

    def recalculate_all_promotions(self) -> dict:
        """Recalculate promotion status for all sources.

        Returns:
            Dict with counts: promoted, demoted, unchanged
        """
        promoted_count = 0
        demoted_count = 0
        unchanged_count = 0

        rows = self.conn.execute("SELECT * FROM sources").fetchall()

        for row in rows:
            source = self._row_to_source(row)

            meets_criteria = self.check_promotion_criteria(source)

            if meets_criteria and not source.is_promoted:
                # Promote
                self.promote_source(source.id)
                promoted_count += 1
            elif not meets_criteria and source.is_promoted and not source.is_seed:
                # Demote (but not seeds)
                self.demote_source(source.id)
                demoted_count += 1
            else:
                unchanged_count += 1

        return {
            "promoted": promoted_count,
            "demoted": demoted_count,
            "unchanged": unchanged_count,
        }

    # =========================================================================
    # Feature 010: Sources Autonomes - Classification (US3)
    # =========================================================================

    def classify_source_auto(self, source_id: str) -> Optional[str]:
        """Automatically classify a source based on known domains.

        Args:
            source_id: Source ULID

        Returns:
            Role assigned (hub/authority/unclassified), or None if source not found
        """
        source = self.get_source(source_id)
        if not source:
            return None

        known = self.get_known_domain(source.domain)
        role = known["role"] if known else "unclassified"

        self.conn.execute(
            "UPDATE sources SET role = ? WHERE id = ?",
            (role, source_id),
        )
        self.conn.commit()
        return role

    def classify_source_manual(self, source_id: str, role: str) -> bool:
        """Manually classify a source.

        Args:
            source_id: Source ULID
            role: hub/authority/unclassified

        Returns:
            True if updated, False if source not found
        """
        from rekall.models import VALID_SOURCE_ROLES

        if role not in VALID_SOURCE_ROLES:
            raise ValueError(f"Invalid role: {role}. Must be one of {VALID_SOURCE_ROLES}")

        cursor = self.conn.execute(
            "UPDATE sources SET role = ? WHERE id = ?",
            (role, source_id),
        )
        self.conn.commit()
        return cursor.rowcount > 0

    # =========================================================================
    # Feature 010: Sources Autonomes - Theme Queries (US5)
    # =========================================================================

    def get_sources_by_theme(
        self,
        theme: str,
        limit: int = 20,
        min_score: float = 0.0,
        include_unclassified: bool = True,
        seeds_only: bool = False,
        promoted_only: bool = False,
    ) -> list[Source]:
        """Get sources for a specific theme, sorted by score.

        Args:
            theme: Theme to filter by
            limit: Maximum sources to return
            min_score: Minimum personal score
            include_unclassified: Include sources with role='unclassified'
            seeds_only: Only return seed sources
            promoted_only: Only return promoted sources

        Returns:
            List of Source objects sorted by score (descending)
        """
        query = """
            SELECT s.* FROM sources s
            JOIN source_themes st ON s.id = st.source_id
            WHERE st.theme = ?
            AND s.personal_score >= ?
        """
        params: list = [theme.lower(), min_score]

        if not include_unclassified:
            query += " AND s.role != 'unclassified'"

        if seeds_only:
            query += " AND s.is_seed = 1"

        if promoted_only:
            query += " AND s.is_promoted = 1"

        query += """
            ORDER BY
                CASE WHEN s.is_seed = 1 THEN 0
                     WHEN s.is_promoted = 1 THEN 1
                     ELSE 2 END,
                s.personal_score DESC
            LIMIT ?
        """
        params.append(limit)

        rows = self.conn.execute(query, params).fetchall()
        return [self._row_to_source(row) for row in rows]

    def list_themes_with_counts(self, min_sources: int = 1) -> list[dict]:
        """List all themes with source counts and average scores.

        Args:
            min_sources: Minimum sources per theme to include

        Returns:
            List of dicts with theme, count, avg_score
        """
        rows = self.conn.execute(
            """
            SELECT theme, COUNT(*) as count,
                   AVG(s.personal_score) as avg_score
            FROM source_themes st
            JOIN sources s ON st.source_id = s.id
            GROUP BY theme
            HAVING count >= ?
            ORDER BY count DESC
            """,
            (min_sources,),
        ).fetchall()

        return [
            {
                "theme": row["theme"],
                "count": row["count"],
                "avg_score": round(row["avg_score"] or 0, 1),
            }
            for row in rows
        ]

    # Alias for Feature 012 compatibility (tags = themes)
    def get_all_tags_with_counts(self, min_sources: int = 1) -> list[dict]:
        """Alias for list_themes_with_counts - tags and themes are the same."""
        return self.list_themes_with_counts(min_sources)

    def get_sources_by_tags(
        self,
        tags: list[str],
        limit: int = 100,
        min_score: float = 0.0,
    ) -> list[Source]:
        """Get sources matching ANY of the given tags (OR logic).

        Args:
            tags: List of tags to match (OR logic - source must have at least one)
            limit: Maximum sources to return
            min_score: Minimum personal score

        Returns:
            List of Source objects sorted by score (descending)
        """
        if not tags:
            return []

        # Normalize tags to lowercase
        normalized_tags = [t.lower().strip() for t in tags if t.strip()]
        if not normalized_tags:
            return []

        # Build query with placeholders for tags
        placeholders = ",".join("?" * len(normalized_tags))
        query = f"""
            SELECT DISTINCT s.* FROM sources s
            JOIN source_themes st ON s.id = st.source_id
            WHERE st.theme IN ({placeholders})
            AND s.personal_score >= ?
            ORDER BY s.personal_score DESC
            LIMIT ?
        """
        params = normalized_tags + [min_score, limit]

        rows = self.conn.execute(query, params).fetchall()
        return [self._row_to_source(row) for row in rows]

    def get_tags_suggestions(self, prefix: str, limit: int = 10) -> list[str]:
        """Get tag suggestions for auto-completion.

        Args:
            prefix: Prefix to match (case-insensitive)
            limit: Maximum suggestions to return

        Returns:
            List of tag names matching the prefix, ordered by usage count
        """
        rows = self.conn.execute(
            """
            SELECT theme, COUNT(*) as cnt FROM source_themes
            WHERE theme LIKE ? || '%'
            GROUP BY theme
            ORDER BY cnt DESC
            LIMIT ?
            """,
            (prefix.lower(), limit),
        ).fetchall()
        return [row["theme"] for row in rows]

    def search_sources_advanced(
        self,
        tags: list[str] | None = None,
        score_min: float | None = None,
        score_max: float | None = None,
        statuses: list[str] | None = None,
        roles: list[str] | None = None,
        last_used_days: int | None = None,
        text_search: str | None = None,
        limit: int = 100,
    ) -> list[Source]:
        """Advanced search for sources with multiple filter criteria.

        Filter logic:
        - Tags: OR (source has at least one of the specified tags)
        - Other criteria: AND (all specified criteria must match)

        Args:
            tags: Filter by tags (OR logic)
            score_min: Minimum personal score
            score_max: Maximum personal score
            statuses: Filter by statuses (OR logic within)
            roles: Filter by roles (OR logic within)
            last_used_days: Only sources used within N days
            text_search: Search in domain name
            limit: Maximum results

        Returns:
            List of matching Source objects sorted by score descending
        """
        from datetime import datetime, timedelta

        # Base query
        if tags:
            # If tags specified, need to join source_themes
            query = """
                SELECT DISTINCT s.* FROM sources s
                JOIN source_themes st ON s.id = st.source_id
                WHERE 1=1
            """
        else:
            query = "SELECT * FROM sources s WHERE 1=1"

        params: list = []

        # Tags filter (OR logic)
        if tags:
            normalized_tags = [t.lower().strip() for t in tags if t.strip()]
            if normalized_tags:
                placeholders = ",".join("?" * len(normalized_tags))
                query += f" AND st.theme IN ({placeholders})"
                params.extend(normalized_tags)

        # Score range
        if score_min is not None:
            query += " AND s.personal_score >= ?"
            params.append(score_min)

        if score_max is not None:
            query += " AND s.personal_score <= ?"
            params.append(score_max)

        # Statuses (OR)
        if statuses:
            placeholders = ",".join("?" * len(statuses))
            query += f" AND s.status IN ({placeholders})"
            params.extend(statuses)

        # Roles (OR)
        if roles:
            placeholders = ",".join("?" * len(roles))
            query += f" AND s.role IN ({placeholders})"
            params.extend(roles)

        # Freshness (last used within N days)
        if last_used_days is not None:
            cutoff = datetime.now() - timedelta(days=last_used_days)
            query += " AND s.last_used >= ?"
            params.append(cutoff.isoformat())

        # Text search in domain
        if text_search:
            query += " AND s.domain LIKE ?"
            params.append(f"%{text_search}%")

        query += " ORDER BY s.personal_score DESC LIMIT ?"
        params.append(limit)

        rows = self.conn.execute(query, params).fetchall()
        return [self._row_to_source(row) for row in rows]

    # =========================================================================
    # Saved Filters (Feature 012 - Sources Organisation)
    # =========================================================================

    def save_filter(self, name: str, filter_dict: dict) -> int:
        """Save a filter configuration.

        Args:
            name: Unique name for the filter
            filter_dict: Dictionary of filter parameters

        Returns:
            ID of the saved filter
        """
        import json

        filter_json = json.dumps(filter_dict)
        cursor = self.conn.execute(
            "INSERT INTO saved_filters (name, filter_json) VALUES (?, ?)",
            (name, filter_json),
        )
        self.conn.commit()
        return cursor.lastrowid

    def get_saved_filters(self) -> list[dict]:
        """Get all saved filters.

        Returns:
            List of dicts with id, name, filter_json, created_at
        """
        rows = self.conn.execute(
            "SELECT id, name, filter_json, created_at FROM saved_filters ORDER BY name"
        ).fetchall()

        return [
            {
                "id": row["id"],
                "name": row["name"],
                "filter_json": row["filter_json"],
                "created_at": row["created_at"],
            }
            for row in rows
        ]

    def get_saved_filter_by_id(self, filter_id: int) -> dict | None:
        """Get a saved filter by ID.

        Args:
            filter_id: ID of the filter

        Returns:
            Dict with filter data or None if not found
        """
        row = self.conn.execute(
            "SELECT id, name, filter_json, created_at FROM saved_filters WHERE id = ?",
            (filter_id,),
        ).fetchone()

        if not row:
            return None

        return {
            "id": row["id"],
            "name": row["name"],
            "filter_json": row["filter_json"],
            "created_at": row["created_at"],
        }

    def delete_saved_filter(self, filter_id: int) -> bool:
        """Delete a saved filter.

        Args:
            filter_id: ID of the filter to delete

        Returns:
            True if deleted, False if not found
        """
        cursor = self.conn.execute(
            "DELETE FROM saved_filters WHERE id = ?", (filter_id,)
        )
        self.conn.commit()
        return cursor.rowcount > 0

    # =========================================================================
    # Sources Inbox (Bronze Layer) - Feature 013
    # =========================================================================

    def add_inbox_entry(self, entry: "InboxEntry") -> str:
        """Add a new inbox entry (Bronze layer).

        Args:
            entry: InboxEntry to add

        Returns:
            The entry ID
        """

        self.conn.execute(
            """INSERT INTO sources_inbox
               (id, url, domain, cli_source, project, conversation_id, user_query,
                assistant_snippet, surrounding_text, captured_at, import_source,
                raw_json, is_valid, validation_error, enriched_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                entry.id,
                entry.url,
                entry.domain,
                entry.cli_source,
                entry.project,
                entry.conversation_id,
                entry.user_query,
                entry.assistant_snippet,
                entry.surrounding_text,
                entry.captured_at.isoformat() if entry.captured_at else None,
                entry.import_source,
                entry.raw_json,
                1 if entry.is_valid else 0,
                entry.validation_error,
                entry.enriched_at.isoformat() if entry.enriched_at else None,
            ),
        )
        self.conn.commit()
        return entry.id

    def get_inbox_entries(
        self,
        cli_source: Optional[str] = None,
        is_valid: Optional[bool] = None,
        valid_only: bool = False,
        quarantine_only: bool = False,
        limit: int = 100,
        offset: int = 0,
    ) -> list["InboxEntry"]:
        """Get inbox entries with optional filtering.

        Args:
            cli_source: Filter by CLI source
            is_valid: Filter by validation status (deprecated, use valid_only/quarantine_only)
            valid_only: If True, only return valid entries
            quarantine_only: If True, only return invalid (quarantined) entries
            limit: Maximum entries to return
            offset: Offset for pagination

        Returns:
            List of InboxEntry objects
        """

        query = "SELECT * FROM sources_inbox WHERE 1=1"
        params: list = []

        if cli_source:
            query += " AND cli_source = ?"
            params.append(cli_source)
        # Handle valid_only / quarantine_only convenience parameters
        if valid_only:
            query += " AND is_valid = 1"
        elif quarantine_only:
            query += " AND is_valid = 0"
        elif is_valid is not None:
            query += " AND is_valid = ?"
            params.append(1 if is_valid else 0)

        query += " ORDER BY captured_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        cursor = self.conn.execute(query, params)
        entries = []
        for row in cursor.fetchall():
            entries.append(self._row_to_inbox_entry(row))
        return entries

    def get_inbox_not_enriched(self, limit: int = 50) -> list["InboxEntry"]:
        """Get inbox entries not yet enriched (for Bronze → Silver processing).

        Args:
            limit: Maximum entries to return

        Returns:
            List of InboxEntry objects awaiting enrichment
        """

        cursor = self.conn.execute(
            """SELECT * FROM sources_inbox
               WHERE enriched_at IS NULL AND is_valid = 1
               ORDER BY captured_at ASC
               LIMIT ?""",
            (limit,),
        )
        entries = []
        for row in cursor.fetchall():
            entries.append(self._row_to_inbox_entry(row))
        return entries

    def mark_inbox_enriched(self, entry_id: str) -> bool:
        """Mark an inbox entry as enriched.

        Args:
            entry_id: ID of the entry to mark

        Returns:
            True if updated, False if not found
        """
        cursor = self.conn.execute(
            "UPDATE sources_inbox SET enriched_at = datetime('now') WHERE id = ?",
            (entry_id,),
        )
        self.conn.commit()
        return cursor.rowcount > 0

    def delete_inbox_entry(self, entry_id: str) -> bool:
        """Delete an inbox entry.

        Args:
            entry_id: ID of the entry to delete

        Returns:
            True if deleted, False if not found
        """
        cursor = self.conn.execute(
            "DELETE FROM sources_inbox WHERE id = ?",
            (entry_id,),
        )
        self.conn.commit()
        return cursor.rowcount > 0

    def clear_inbox(
        self,
        all_entries: bool = False,
        quarantine_only: bool = False,
        enriched_only: bool = False,
    ) -> int:
        """Clear inbox entries.

        Args:
            all_entries: Delete all entries
            quarantine_only: Delete only quarantine entries (is_valid = 0)
            enriched_only: Delete only enriched entries

        Returns:
            Number of entries deleted
        """
        if all_entries:
            cursor = self.conn.execute("DELETE FROM sources_inbox")
        elif quarantine_only:
            cursor = self.conn.execute("DELETE FROM sources_inbox WHERE is_valid = 0")
        elif enriched_only:
            cursor = self.conn.execute("DELETE FROM sources_inbox WHERE enriched_at IS NOT NULL")
        else:
            return 0
        self.conn.commit()
        return cursor.rowcount

    def get_inbox_stats(self) -> dict:
        """Get inbox statistics.

        Returns:
            Dict with total, pending, quarantine, enriched counts
        """
        cursor = self.conn.execute(
            """SELECT
                COUNT(*) as total,
                SUM(CASE WHEN enriched_at IS NULL AND is_valid = 1 THEN 1 ELSE 0 END) as pending,
                SUM(CASE WHEN is_valid = 0 THEN 1 ELSE 0 END) as quarantine,
                SUM(CASE WHEN enriched_at IS NOT NULL THEN 1 ELSE 0 END) as enriched
               FROM sources_inbox"""
        )
        row = cursor.fetchone()
        return {
            "total": row["total"] or 0,
            "pending": row["pending"] or 0,
            "quarantine": row["quarantine"] or 0,
            "enriched": row["enriched"] or 0,
        }

    def _row_to_inbox_entry(self, row) -> "InboxEntry":
        """Convert database row to InboxEntry."""
        from rekall.models import InboxEntry

        return InboxEntry(
            id=row["id"],
            url=row["url"],
            domain=row["domain"],
            cli_source=row["cli_source"],
            project=row["project"],
            conversation_id=row["conversation_id"],
            user_query=row["user_query"],
            assistant_snippet=row["assistant_snippet"],
            surrounding_text=row["surrounding_text"],
            captured_at=datetime.fromisoformat(row["captured_at"]) if row["captured_at"] else datetime.now(),
            import_source=row["import_source"] or "history_import",
            raw_json=row["raw_json"],
            is_valid=bool(row["is_valid"]),
            validation_error=row["validation_error"],
            enriched_at=datetime.fromisoformat(row["enriched_at"]) if row["enriched_at"] else None,
        )

    # =========================================================================
    # Sources Staging (Silver Layer) - Feature 013
    # =========================================================================

    def add_staging_entry(self, entry: "StagingEntry") -> str:
        """Add a new staging entry (Silver layer).

        Args:
            entry: StagingEntry to add

        Returns:
            The entry ID
        """

        self.conn.execute(
            """INSERT INTO sources_staging
               (id, url, domain, title, description, content_type, language,
                last_verified, is_accessible, http_status, citation_count,
                project_count, projects_list, first_seen, last_seen,
                promotion_score, inbox_ids, enriched_at, promoted_at, promoted_to)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                entry.id,
                entry.url,
                entry.domain,
                entry.title,
                entry.description,
                entry.content_type,
                entry.language,
                entry.last_verified.isoformat() if entry.last_verified else None,
                1 if entry.is_accessible else 0,
                entry.http_status,
                entry.citation_count,
                entry.project_count,
                entry.projects_list,
                entry.first_seen.isoformat() if entry.first_seen else None,
                entry.last_seen.isoformat() if entry.last_seen else None,
                entry.promotion_score,
                entry.inbox_ids,
                entry.enriched_at.isoformat() if entry.enriched_at else None,
                entry.promoted_at.isoformat() if entry.promoted_at else None,
                entry.promoted_to,
            ),
        )
        self.conn.commit()
        return entry.id

    def get_staging_by_url(self, url: str) -> Optional["StagingEntry"]:
        """Get a staging entry by URL.

        Args:
            url: URL to find

        Returns:
            StagingEntry or None if not found
        """
        cursor = self.conn.execute(
            "SELECT * FROM sources_staging WHERE url = ?", (url,)
        )
        row = cursor.fetchone()
        if row:
            return self._row_to_staging_entry(row)
        return None

    def get_staging_entries(
        self,
        promoted: Optional[bool] = None,
        content_type: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list["StagingEntry"]:
        """Get staging entries with optional filtering.

        Args:
            promoted: Filter by promotion status (True=promoted, False=not, None=all)
            content_type: Filter by content type
            limit: Maximum entries to return
            offset: Offset for pagination

        Returns:
            List of StagingEntry objects
        """
        query = "SELECT * FROM sources_staging WHERE 1=1"
        params: list = []

        if promoted is not None:
            if promoted:
                query += " AND promoted_at IS NOT NULL"
            else:
                query += " AND promoted_at IS NULL"
        if content_type:
            query += " AND content_type = ?"
            params.append(content_type)

        query += " ORDER BY promotion_score DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        cursor = self.conn.execute(query, params)
        entries = []
        for row in cursor.fetchall():
            entries.append(self._row_to_staging_entry(row))
        return entries

    def get_staging_eligible_for_promotion(self, threshold: float) -> list["StagingEntry"]:
        """Get staging entries eligible for promotion.

        Args:
            threshold: Minimum score threshold

        Returns:
            List of StagingEntry objects with score >= threshold and not yet promoted
        """
        cursor = self.conn.execute(
            """SELECT * FROM sources_staging
               WHERE promotion_score >= ? AND promoted_at IS NULL AND is_accessible = 1
               ORDER BY promotion_score DESC""",
            (threshold,),
        )
        entries = []
        for row in cursor.fetchall():
            entries.append(self._row_to_staging_entry(row))
        return entries

    def update_staging(self, entry: "StagingEntry") -> bool:
        """Update a staging entry.

        Args:
            entry: StagingEntry with updated values

        Returns:
            True if updated, False if not found
        """
        cursor = self.conn.execute(
            """UPDATE sources_staging SET
               title = ?, description = ?, content_type = ?, language = ?,
               last_verified = ?, is_accessible = ?, http_status = ?,
               citation_count = ?, project_count = ?, projects_list = ?,
               first_seen = ?, last_seen = ?, promotion_score = ?,
               inbox_ids = ?, enriched_at = ?, promoted_at = ?, promoted_to = ?
               WHERE id = ?""",
            (
                entry.title,
                entry.description,
                entry.content_type,
                entry.language,
                entry.last_verified.isoformat() if entry.last_verified else None,
                1 if entry.is_accessible else 0,
                entry.http_status,
                entry.citation_count,
                entry.project_count,
                entry.projects_list,
                entry.first_seen.isoformat() if entry.first_seen else None,
                entry.last_seen.isoformat() if entry.last_seen else None,
                entry.promotion_score,
                entry.inbox_ids,
                entry.enriched_at.isoformat() if entry.enriched_at else None,
                entry.promoted_at.isoformat() if entry.promoted_at else None,
                entry.promoted_to,
                entry.id,
            ),
        )
        self.conn.commit()
        return cursor.rowcount > 0

    def _row_to_staging_entry(self, row) -> "StagingEntry":
        """Convert database row to StagingEntry."""
        from rekall.models import StagingEntry

        return StagingEntry(
            id=row["id"],
            url=row["url"],
            domain=row["domain"],
            title=row["title"],
            description=row["description"],
            content_type=row["content_type"],
            language=row["language"],
            last_verified=datetime.fromisoformat(row["last_verified"]) if row["last_verified"] else None,
            is_accessible=bool(row["is_accessible"]),
            http_status=row["http_status"],
            citation_count=row["citation_count"] or 1,
            project_count=row["project_count"] or 1,
            projects_list=row["projects_list"],
            first_seen=datetime.fromisoformat(row["first_seen"]) if row["first_seen"] else None,
            last_seen=datetime.fromisoformat(row["last_seen"]) if row["last_seen"] else None,
            promotion_score=row["promotion_score"] or 0.0,
            inbox_ids=row["inbox_ids"],
            enriched_at=datetime.fromisoformat(row["enriched_at"]) if row["enriched_at"] else None,
            promoted_at=datetime.fromisoformat(row["promoted_at"]) if row["promoted_at"] else None,
            promoted_to=row["promoted_to"],
        )

    # =========================================================================
    # Connector Imports (CDC Tracking) - Feature 013
    # =========================================================================

    def get_connector_import(self, connector: str) -> Optional["ConnectorImport"]:
        """Get import tracking info for a connector.

        Args:
            connector: Connector name (e.g., 'claude_cli', 'cursor')

        Returns:
            ConnectorImport or None if not found
        """
        from rekall.models import ConnectorImport

        cursor = self.conn.execute(
            "SELECT * FROM connector_imports WHERE connector = ?", (connector,)
        )
        row = cursor.fetchone()
        if row:
            return ConnectorImport(
                connector=row["connector"],
                last_import=datetime.fromisoformat(row["last_import"]) if row["last_import"] else None,
                last_file_marker=row["last_file_marker"],
                entries_imported=row["entries_imported"] or 0,
                errors_count=row["errors_count"] or 0,
            )
        return None

    def upsert_connector_import(self, info: "ConnectorImport") -> None:
        """Insert or update connector import tracking.

        Args:
            info: ConnectorImport to upsert
        """
        self.conn.execute(
            """INSERT INTO connector_imports
               (connector, last_import, last_file_marker, entries_imported, errors_count)
               VALUES (?, ?, ?, ?, ?)
               ON CONFLICT(connector) DO UPDATE SET
               last_import = excluded.last_import,
               last_file_marker = excluded.last_file_marker,
               entries_imported = excluded.entries_imported,
               errors_count = excluded.errors_count""",
            (
                info.connector,
                info.last_import.isoformat() if info.last_import else None,
                info.last_file_marker,
                info.entries_imported,
                info.errors_count,
            ),
        )
        self.conn.commit()
