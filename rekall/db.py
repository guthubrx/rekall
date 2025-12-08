"""Rekall database operations with SQLite + FTS5."""

from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional

from rekall.models import Entry, SearchResult

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

        self.conn.commit()

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
        # Insert entry
        self.conn.execute(
            """
            INSERT INTO entries (id, title, content, type, project, confidence,
                                 status, superseded_by, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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

    def get(self, entry_id: str) -> Optional[Entry]:
        """Get an entry by ID.

        Args:
            entry_id: ULID of the entry

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
        )

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
                status = ?, superseded_by = ?, updated_at = ?
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
        include_obsolete: bool = False,
        limit: int = 20,
    ) -> list[SearchResult]:
        """Search entries using FTS5.

        Args:
            query: Search query
            entry_type: Filter by type (optional)
            project: Filter by project (optional)
            include_obsolete: Include obsolete entries (default False)
            limit: Maximum results to return

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

            entry = Entry(
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
            )

            results.append(SearchResult(entry=entry, rank=row["rank"]))

        return results

    def list_all(
        self,
        entry_type: Optional[str] = None,
        project: Optional[str] = None,
        include_obsolete: bool = False,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Entry]:
        """List all entries with optional filters.

        Args:
            entry_type: Filter by type (optional)
            project: Filter by project (optional)
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

        sql += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        cursor = self.conn.execute(sql, params)
        entries = []

        for row in cursor.fetchall():
            tag_cursor = self.conn.execute(
                "SELECT tag FROM tags WHERE entry_id = ?", (row["id"],)
            )
            tags = [r[0] for r in tag_cursor.fetchall()]

            entries.append(
                Entry(
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
                )
            )

        return entries
