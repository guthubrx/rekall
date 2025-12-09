"""Rekall database backup and restore operations.

This module provides backup, restore, and database information functions
for maintaining the Rekall knowledge database.
"""

from __future__ import annotations

import shutil
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

from rekall.db import CURRENT_SCHEMA_VERSION


@dataclass
class BackupInfo:
    """Information about a backup file."""

    path: Path
    """Full path to the backup file."""

    timestamp: datetime
    """Creation timestamp of the backup."""

    size: int
    """Size in bytes."""

    db_name: str = "knowledge.db"
    """Original database name."""

    @property
    def size_human(self) -> str:
        """Human-readable size (e.g., '256 KB')."""
        if self.size < 1024:
            return f"{self.size} B"
        elif self.size < 1024 * 1024:
            return f"{self.size / 1024:.1f} KB"
        else:
            return f"{self.size / (1024 * 1024):.1f} MB"


@dataclass
class DatabaseStats:
    """Statistics about the Rekall database."""

    path: Path
    """Path to the database file."""

    schema_version: int
    """Current schema version (PRAGMA user_version)."""

    is_current: bool
    """True if schema version matches CURRENT_SCHEMA_VERSION."""

    total_entries: int
    """Total number of entries."""

    active_entries: int
    """Number of active entries."""

    obsolete_entries: int
    """Number of obsolete entries."""

    links_count: int
    """Number of links between entries."""

    file_size: int
    """Database file size in bytes."""

    @property
    def file_size_human(self) -> str:
        """Human-readable file size (e.g., '256 KB')."""
        if self.file_size < 1024:
            return f"{self.file_size} B"
        elif self.file_size < 1024 * 1024:
            return f"{self.file_size / 1024:.1f} KB"
        else:
            return f"{self.file_size / (1024 * 1024):.1f} MB"


def get_default_backups_dir() -> Path:
    """Get the default backups directory.

    Returns:
        Path to ~/.rekall/backups/
    """
    backups_dir = Path.home() / ".rekall" / "backups"
    backups_dir.mkdir(parents=True, exist_ok=True)
    return backups_dir


def validate_backup(backup_path: Path) -> bool:
    """Validate a backup file using SQLite integrity check.

    Args:
        backup_path: Path to the backup file

    Returns:
        True if backup is valid, False otherwise
    """
    if not backup_path.exists():
        return False

    try:
        conn = sqlite3.connect(str(backup_path))
        result = conn.execute("PRAGMA integrity_check").fetchone()
        conn.close()
        return result[0] == "ok"
    except sqlite3.Error:
        return False


def create_backup(
    db_path: Path,
    output: Optional[Path] = None,
) -> BackupInfo:
    """Create a backup of the database.

    Flushes WAL journal before copying to ensure consistency.

    Args:
        db_path: Path to the source database
        output: Optional output path (auto-generated if None)

    Returns:
        BackupInfo with backup details

    Raises:
        FileNotFoundError: If source database doesn't exist
        RuntimeError: If backup validation fails
    """
    if not db_path.exists():
        raise FileNotFoundError(f"Database not found: {db_path}")

    # Generate output path if not provided
    if output is None:
        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        backups_dir = get_default_backups_dir()
        output = backups_dir / f"knowledge_{timestamp}.db"

    # Ensure output directory exists
    output.parent.mkdir(parents=True, exist_ok=True)

    # Flush WAL to main database file
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
    conn.close()

    # Copy database file with metadata
    shutil.copy2(db_path, output)

    # Validate the backup
    if not validate_backup(output):
        output.unlink()  # Delete invalid backup
        raise RuntimeError("Backup validation failed (integrity check)")

    # Get backup info
    stat = output.stat()
    return BackupInfo(
        path=output,
        timestamp=datetime.fromtimestamp(stat.st_mtime),
        size=stat.st_size,
    )


def restore_backup(
    backup_path: Path,
    db_path: Path,
    create_safety_backup: bool = True,
) -> tuple[bool, Optional[BackupInfo]]:
    """Restore database from a backup.

    Args:
        backup_path: Path to the backup file to restore
        db_path: Path to the target database location
        create_safety_backup: Create safety backup before restore (default True)

    Returns:
        Tuple of (success, safety_backup_info or None)

    Raises:
        FileNotFoundError: If backup file doesn't exist
        ValueError: If backup is invalid
    """
    if not backup_path.exists():
        raise FileNotFoundError(f"Backup file not found: {backup_path}")

    # Validate backup before proceeding
    if not validate_backup(backup_path):
        raise ValueError("Invalid backup file (integrity check failed)")

    safety_backup: Optional[BackupInfo] = None

    # Create safety backup of current database
    if create_safety_backup and db_path.exists():
        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        backups_dir = get_default_backups_dir()
        safety_path = backups_dir / f"knowledge_{timestamp}_pre-restore.db"

        # Flush WAL before safety backup
        conn = sqlite3.connect(str(db_path))
        conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        conn.close()

        shutil.copy2(db_path, safety_path)

        stat = safety_path.stat()
        safety_backup = BackupInfo(
            path=safety_path,
            timestamp=datetime.fromtimestamp(stat.st_mtime),
            size=stat.st_size,
        )

    # Replace current database with backup
    shutil.copy2(backup_path, db_path)

    # Remove WAL and SHM files if they exist (fresh start)
    wal_path = Path(str(db_path) + "-wal")
    shm_path = Path(str(db_path) + "-shm")
    if wal_path.exists():
        wal_path.unlink()
    if shm_path.exists():
        shm_path.unlink()

    return True, safety_backup


def list_backups(backups_dir: Optional[Path] = None) -> list[BackupInfo]:
    """List all available backups.

    Args:
        backups_dir: Directory to search (default: ~/.rekall/backups/)

    Returns:
        List of BackupInfo sorted by timestamp (newest first)
    """
    if backups_dir is None:
        backups_dir = get_default_backups_dir()

    if not backups_dir.exists():
        return []

    backups = []
    for path in backups_dir.glob("knowledge_*.db"):
        if path.is_file():
            stat = path.stat()
            backups.append(
                BackupInfo(
                    path=path,
                    timestamp=datetime.fromtimestamp(stat.st_mtime),
                    size=stat.st_size,
                )
            )

    # Sort by timestamp, newest first
    backups.sort(key=lambda b: b.timestamp, reverse=True)
    return backups


def get_database_stats(db_path: Path) -> Optional[DatabaseStats]:
    """Get statistics about the database.

    Args:
        db_path: Path to the database

    Returns:
        DatabaseStats or None if database doesn't exist
    """
    if not db_path.exists():
        return None

    try:
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row

        # Get schema version
        schema_version = conn.execute("PRAGMA user_version").fetchone()[0]

        # Count entries
        total = conn.execute("SELECT COUNT(*) FROM entries").fetchone()[0]
        active = conn.execute(
            "SELECT COUNT(*) FROM entries WHERE status = 'active'"
        ).fetchone()[0]
        obsolete = total - active

        # Count links (may not exist in older schemas)
        try:
            links = conn.execute("SELECT COUNT(*) FROM links").fetchone()[0]
        except sqlite3.OperationalError:
            links = 0

        conn.close()

        # Get file size
        file_size = db_path.stat().st_size

        return DatabaseStats(
            path=db_path,
            schema_version=schema_version,
            is_current=schema_version == CURRENT_SCHEMA_VERSION,
            total_entries=total,
            active_entries=active,
            obsolete_entries=obsolete,
            links_count=links,
            file_size=file_size,
        )
    except sqlite3.Error:
        return None
