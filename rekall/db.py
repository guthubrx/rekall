"""Rekall database operations with SQLite + FTS5."""

from __future__ import annotations

import sqlite3
from datetime import date, datetime
from pathlib import Path
from typing import Optional

from rekall.models import (
    Entry,
    Link,
    ReviewItem,
    SearchResult,
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

CURRENT_SCHEMA_VERSION = 2

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
}

# Expected columns for schema verification (Option C - hybrid)
EXPECTED_ENTRY_COLUMNS = {
    "id", "title", "content", "type", "project", "confidence",
    "status", "superseded_by", "created_at", "updated_at",
    "memory_type", "last_accessed", "access_count", "consolidation_score",
    "next_review", "review_interval", "ease_factor",
}

EXPECTED_TABLES = {"entries", "tags", "links", "entries_fts"}


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
    ) -> Link:
        """Create a link between two entries.

        Args:
            source_id: Source entry ULID
            target_id: Target entry ULID
            relation_type: Type of relation (default "related")

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
        )

        try:
            self.conn.execute(
                """
                INSERT INTO links (id, source_id, target_id, relation_type, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    link.id,
                    link.source_id,
                    link.target_id,
                    link.relation_type,
                    link.created_at.isoformat(),
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

    def count_links(self, entry_id: str) -> int:
        """Count total links for an entry.

        Args:
            entry_id: Entry ULID

        Returns:
            Number of links (both directions)
        """
        cursor = self.conn.execute(
            "SELECT COUNT(*) FROM links WHERE source_id = ? OR target_id = ?",
            (entry_id, entry_id),
        )
        return cursor.fetchone()[0]

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
    ) -> str:
        """Render entry connections as ASCII tree.

        Args:
            entry_id: Starting entry ULID
            max_depth: Maximum depth to traverse (default 2)
            show_incoming: Show incoming links (← referenced by)
            show_outgoing: Show outgoing links (→ references to)

        Returns:
            ASCII art representation of the connection graph
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

        # Collect all connections
        connections: list[tuple[str, str, str, str]] = []  # (direction, type, id, title)

        if show_outgoing:
            outgoing = self.get_links(entry_id, direction="outgoing")
            for link in outgoing:
                target = self.get(link.target_id, update_access=False)
                if target:
                    connections.append(("→", link.relation_type, target.id, target.title))

        if show_incoming:
            incoming = self.get_links(entry_id, direction="incoming")
            for link in incoming:
                source = self.get(link.source_id, update_access=False)
                if source:
                    connections.append(("←", link.relation_type, source.id, source.title))

        # Render connections
        total = len(connections)
        for i, (direction, rel_type, conn_id, conn_title) in enumerate(connections):
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
            lines.append(f" {branch}  [dim]({conn_id})[/dim]")

            # Recurse if depth allows
            if max_depth > 1 and conn_id not in visited:
                visited.add(conn_id)
                sub_lines = self._render_subtree(
                    conn_id, max_depth - 1, visited, branch, direction
                )
                lines.extend(sub_lines)

        if not connections:
            lines.append(" [dim](aucune connexion)[/dim]")

        return "\n".join(lines)

    def _render_subtree(
        self,
        entry_id: str,
        depth: int,
        visited: set[str],
        prefix: str,
        parent_direction: str,
    ) -> list[str]:
        """Render subtree for recursive graph traversal."""
        lines: list[str] = []

        if depth <= 0:
            return lines

        # Only follow same direction to avoid loops
        if parent_direction == "→":
            links = self.get_links(entry_id, direction="outgoing")
            connections = [
                ("→", link.relation_type, link.target_id)
                for link in links
                if link.target_id not in visited
            ]
        else:
            links = self.get_links(entry_id, direction="incoming")
            connections = [
                ("←", link.relation_type, link.source_id)
                for link in links
                if link.source_id not in visited
            ]

        total = len(connections)
        for i, (direction, rel_type, conn_id) in enumerate(connections):
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
            lines.append(f" {prefix}{'   ' if is_last else '│  '}  [dim]({conn_id})[/dim]")

            # Continue recursion
            if depth > 1:
                sub_lines = self._render_subtree(
                    conn_id, depth - 1, visited, next_prefix, direction
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
