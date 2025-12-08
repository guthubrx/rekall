"""Rekall sync module for import conflict detection and resolution."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Literal, Optional

from rekall.archive import RekallArchive
from rekall.db import Database
from rekall.models import Entry, generate_ulid


@dataclass
class Conflict:
    """Conflict between local and imported entry."""

    entry_id: str
    local: Entry
    imported: Entry
    fields_changed: list[str]

    @property
    def summary(self) -> str:
        """Get summary of differences."""
        return f"{len(self.fields_changed)} field(s) changed: {', '.join(self.fields_changed)}"


@dataclass
class ImportPlan:
    """Plan for import with classified entries."""

    new_entries: list[Entry] = field(default_factory=list)
    conflicts: list[Conflict] = field(default_factory=list)
    identical: list[str] = field(default_factory=list)

    @property
    def total(self) -> int:
        """Get total number of entries in plan."""
        return len(self.new_entries) + len(self.conflicts) + len(self.identical)

    @property
    def has_conflicts(self) -> bool:
        """Check if plan has conflicts."""
        return len(self.conflicts) > 0


@dataclass
class ImportResult:
    """Result of import execution."""

    success: bool
    added: int = 0
    replaced: int = 0
    skipped: int = 0
    merged: int = 0
    backup_path: Optional[Path] = None
    errors: list[str] = field(default_factory=list)

    @property
    def total_processed(self) -> int:
        """Get total processed entries."""
        return self.added + self.replaced + self.skipped + self.merged


ImportStrategy = Literal["skip", "replace", "merge", "interactive"]


def detect_conflict(local: Entry, imported: Entry) -> Optional[Conflict]:
    """Detect conflict between local and imported entry.

    Args:
        local: Local entry from database
        imported: Entry from archive

    Returns:
        Conflict if entries differ, None if identical
    """
    if local.id != imported.id:
        return None

    fields_changed = []

    if local.title != imported.title:
        fields_changed.append("title")
    if local.content != imported.content:
        fields_changed.append("content")
    if local.type != imported.type:
        fields_changed.append("type")
    if local.project != imported.project:
        fields_changed.append("project")
    if set(local.tags) != set(imported.tags):
        fields_changed.append("tags")
    if local.confidence != imported.confidence:
        fields_changed.append("confidence")
    if local.status != imported.status:
        fields_changed.append("status")
    if local.superseded_by != imported.superseded_by:
        fields_changed.append("superseded_by")

    if not fields_changed:
        return None

    return Conflict(
        entry_id=local.id,
        local=local,
        imported=imported,
        fields_changed=fields_changed,
    )


def build_import_plan(db: Database, imported_entries: list[Entry]) -> ImportPlan:
    """Build import plan by comparing with database.

    Args:
        db: Database to compare against
        imported_entries: Entries from archive

    Returns:
        ImportPlan with classified entries
    """
    plan = ImportPlan()

    for imported in imported_entries:
        local = db.get(imported.id)

        if local is None:
            # New entry
            plan.new_entries.append(imported)
        else:
            # Exists - check for conflict
            conflict = detect_conflict(local, imported)
            if conflict is None:
                # Identical
                plan.identical.append(imported.id)
            else:
                # Conflict
                plan.conflicts.append(conflict)

    return plan


class ImportExecutor:
    """Executes import plan with specified strategy."""

    def __init__(self, db: Database, backup_dir: Optional[Path] = None):
        """Initialize executor.

        Args:
            db: Database to import into
            backup_dir: Directory for backup files
        """
        self.db = db
        self.backup_dir = backup_dir

    @staticmethod
    def preview(plan: ImportPlan) -> str:
        """Generate preview of import plan.

        Args:
            plan: Import plan to preview

        Returns:
            Formatted preview string
        """
        if plan.total == 0:
            return "Nothing to import."

        lines = []
        lines.append(f"Import preview: {plan.total} entries")
        lines.append("")

        if plan.new_entries:
            lines.append(f"New entries ({len(plan.new_entries)}):")
            for entry in plan.new_entries:
                lines.append(f"  [NEW] {entry.id[:12]}... {entry.title}")
            lines.append("")

        if plan.conflicts:
            lines.append(f"Conflicts ({len(plan.conflicts)}):")
            for conflict in plan.conflicts:
                lines.append(
                    f"  [CONFLICT] {conflict.entry_id[:12]}... {conflict.local.title}"
                )
                lines.append(f"             Changed: {', '.join(conflict.fields_changed)}")
            lines.append("")

        if plan.identical:
            lines.append(f"Identical ({len(plan.identical)}):")
            for entry_id in plan.identical:
                lines.append(f"  [SKIP] {entry_id[:12]}...")

        return "\n".join(lines)

    def _create_backup(self) -> Path:
        """Create backup before destructive operation.

        Returns:
            Path to backup file
        """
        if self.backup_dir is None:
            self.backup_dir = self.db.db_path.parent / "backups"

        self.backup_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        backup_path = self.backup_dir / f"pre-import-{timestamp}.rekall.zip"

        # Export all entries to backup
        entries = self.db.list_all(include_obsolete=True, limit=100000)
        RekallArchive.create(backup_path, entries)

        return backup_path

    def _add_entry_no_commit(self, entry: Entry) -> None:
        """Add entry without committing (for transaction batching).

        Args:
            entry: Entry to add
        """
        self.db.conn.execute(
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
            self.db.conn.execute(
                "INSERT INTO tags (entry_id, tag) VALUES (?, ?)",
                (entry.id, tag),
            )

        # Update FTS index
        self.db.conn.execute("DELETE FROM entries_fts WHERE id = ?", (entry.id,))
        self.db.conn.execute(
            """
            INSERT INTO entries_fts(id, title, content, tags)
            SELECT e.id, e.title, e.content,
                   (SELECT GROUP_CONCAT(tag, ' ') FROM tags WHERE entry_id = e.id)
            FROM entries e WHERE e.id = ?
            """,
            (entry.id,),
        )

    def _update_entry_no_commit(self, entry: Entry) -> None:
        """Update entry without committing (for transaction batching).

        Args:
            entry: Entry to update
        """
        self.db.conn.execute(
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
        self.db.conn.execute("DELETE FROM tags WHERE entry_id = ?", (entry.id,))
        for tag in entry.tags:
            self.db.conn.execute(
                "INSERT INTO tags (entry_id, tag) VALUES (?, ?)",
                (entry.id, tag),
            )

        # Update FTS index
        self.db.conn.execute("DELETE FROM entries_fts WHERE id = ?", (entry.id,))
        self.db.conn.execute(
            """
            INSERT INTO entries_fts(id, title, content, tags)
            SELECT e.id, e.title, e.content,
                   (SELECT GROUP_CONCAT(tag, ' ') FROM tags WHERE entry_id = e.id)
            FROM entries e WHERE e.id = ?
            """,
            (entry.id,),
        )

    def execute(
        self, plan: ImportPlan, strategy: ImportStrategy = "skip"
    ) -> ImportResult:
        """Execute import plan with specified strategy.

        Args:
            plan: Import plan to execute
            strategy: Conflict resolution strategy

        Returns:
            ImportResult with execution details
        """
        result = ImportResult(success=True)

        # Create backup if using replace strategy and there are conflicts
        if strategy == "replace" and plan.conflicts:
            result.backup_path = self._create_backup()

        # Use transaction for atomicity
        try:
            # Start explicit transaction
            self.db.conn.execute("BEGIN")

            # Add new entries
            for entry in plan.new_entries:
                self._add_entry_no_commit(entry)
                result.added += 1

            # Handle conflicts based on strategy
            for conflict in plan.conflicts:
                if strategy == "skip":
                    result.skipped += 1
                elif strategy == "replace":
                    # Update existing entry with imported data
                    imported = conflict.imported
                    imported.updated_at = datetime.now()
                    self._update_entry_no_commit(imported)
                    result.replaced += 1
                elif strategy == "merge":
                    # Create new entry with new ID
                    new_entry = Entry(
                        id=generate_ulid(),
                        title=conflict.imported.title,
                        type=conflict.imported.type,
                        content=conflict.imported.content,
                        project=conflict.imported.project,
                        tags=conflict.imported.tags.copy(),
                        confidence=conflict.imported.confidence,
                        status=conflict.imported.status,
                        superseded_by=conflict.imported.superseded_by,
                        created_at=conflict.imported.created_at,
                        updated_at=datetime.now(),
                    )
                    self._add_entry_no_commit(new_entry)
                    result.merged += 1

            # Count skipped identical entries
            result.skipped += len(plan.identical)

            # Commit transaction
            self.db.conn.commit()

        except Exception as e:
            # Rollback on error
            self.db.conn.rollback()
            result.success = False
            result.errors.append(str(e))

        return result


def load_entries_from_external_db(db_path: Path) -> list[Entry]:
    """Load entries from an external knowledge.db file.

    Args:
        db_path: Path to external knowledge.db

    Returns:
        List of Entry objects

    Raises:
        ValueError: If file is not a valid Rekall database
    """
    if not db_path.exists():
        raise ValueError(f"File not found: {db_path}")

    # Check it's a SQLite file
    try:
        conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        conn.row_factory = sqlite3.Row
    except sqlite3.Error as e:
        raise ValueError(f"Cannot open database: {e}")

    # Check it has the entries table
    try:
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='entries'"
        )
        if cursor.fetchone() is None:
            conn.close()
            raise ValueError("Not a valid Rekall database: missing 'entries' table")
    except sqlite3.Error as e:
        conn.close()
        raise ValueError(f"Database error: {e}")

    # Load entries
    entries = []
    try:
        cursor = conn.execute(
            """
            SELECT id, title, content, type, project, confidence,
                   status, superseded_by, created_at, updated_at
            FROM entries
            """
        )

        for row in cursor:
            # Load tags for this entry
            tag_cursor = conn.execute(
                "SELECT tag FROM tags WHERE entry_id = ?", (row["id"],)
            )
            tags = [t["tag"] for t in tag_cursor]

            entry = Entry(
                id=row["id"],
                title=row["title"],
                type=row["type"],
                content=row["content"] or "",
                project=row["project"],
                tags=tags,
                confidence=row["confidence"] or 2,
                status=row["status"] or "active",
                superseded_by=row["superseded_by"],
                created_at=datetime.fromisoformat(row["created_at"]),
                updated_at=datetime.fromisoformat(row["updated_at"]),
            )
            entries.append(entry)

    except sqlite3.Error as e:
        conn.close()
        raise ValueError(f"Error reading entries: {e}")

    conn.close()
    return entries
