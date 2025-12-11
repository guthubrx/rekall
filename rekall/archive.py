"""Rekall archive module for export/import functionality."""

from __future__ import annotations

import hashlib
import json
import zipfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from rekall import __version__
from rekall.models import Entry
from rekall.serializers import entries_from_json, entries_to_json


@dataclass
class ArchiveStats:
    """Statistics about archive contents."""

    entries_count: int
    projects: list[str]
    types: dict[str, int]


@dataclass
class Manifest:
    """Archive manifest with metadata."""

    format_version: str
    created_at: datetime
    rekall_version: str
    checksum: str
    stats: ArchiveStats

    def to_dict(self) -> dict:
        """Serialize manifest to dictionary."""
        return {
            "format_version": self.format_version,
            "created_at": self.created_at.isoformat(),
            "rekall_version": self.rekall_version,
            "checksum": self.checksum,
            "stats": {
                "entries_count": self.stats.entries_count,
                "projects": self.stats.projects,
                "types": self.stats.types,
            },
        }

    @classmethod
    def from_dict(cls, data: dict) -> Manifest:
        """Deserialize manifest from dictionary."""
        return cls(
            format_version=data["format_version"],
            created_at=datetime.fromisoformat(data["created_at"]),
            rekall_version=data["rekall_version"],
            checksum=data["checksum"],
            stats=ArchiveStats(
                entries_count=data["stats"]["entries_count"],
                projects=data["stats"]["projects"],
                types=data["stats"]["types"],
            ),
        )


@dataclass
class ValidationResult:
    """Result of archive validation."""

    valid: bool
    errors: list[str]
    warnings: list[str]

    def __bool__(self) -> bool:
        return self.valid


def calculate_checksum(data: bytes) -> str:
    """Calculate SHA256 checksum of data.

    Args:
        data: Bytes to hash

    Returns:
        Checksum string in format "sha256:<64 hex chars>"
    """
    hash_obj = hashlib.sha256(data)
    return f"sha256:{hash_obj.hexdigest()}"


class RekallArchive:
    """Handler for .rekall archive files."""

    FORMAT_VERSION = "1.0"

    def __init__(self, path: Path, zipf: zipfile.ZipFile | None = None):
        """Initialize archive handler.

        Args:
            path: Path to archive file
            zipf: Optional open ZipFile object
        """
        self.path = path
        self._zipf = zipf
        self._manifest: Manifest | None = None
        self._entries: list[Entry] | None = None

    @classmethod
    def create(cls, path: Path, entries: list[Entry]) -> RekallArchive:
        """Create a new archive file.

        Args:
            path: Path where to create archive
            entries: List of entries to include

        Returns:
            RekallArchive instance
        """
        # Serialize entries
        entries_json = entries_to_json(entries)
        entries_bytes = entries_json.encode("utf-8")

        # Calculate checksum
        checksum = calculate_checksum(entries_bytes)

        # Build stats
        projects = list(set(e.project for e in entries if e.project))
        types: dict[str, int] = {}
        for entry in entries:
            types[entry.type] = types.get(entry.type, 0) + 1

        stats = ArchiveStats(
            entries_count=len(entries),
            projects=sorted(projects),
            types=types,
        )

        # Build manifest
        manifest = Manifest(
            format_version=cls.FORMAT_VERSION,
            created_at=datetime.now(),
            rekall_version=__version__,
            checksum=checksum,
            stats=stats,
        )

        # Write archive
        with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("manifest.json", json.dumps(manifest.to_dict(), indent=2))
            zf.writestr("entries.json", entries_json)

        return cls(path)

    @classmethod
    def open(cls, path: Path) -> RekallArchive | None:
        """Open an existing archive file.

        Args:
            path: Path to archive file

        Returns:
            RekallArchive instance or None if invalid
        """
        if not path.exists():
            return None

        if not zipfile.is_zipfile(path):
            return None

        try:
            zipf = zipfile.ZipFile(path, "r")
            return cls(path, zipf)
        except zipfile.BadZipFile:
            return None

    def close(self) -> None:
        """Close the archive file."""
        if self._zipf:
            self._zipf.close()
            self._zipf = None

    def validate(self) -> ValidationResult:
        """Validate archive integrity.

        Returns:
            ValidationResult with status and any errors
        """
        errors = []
        warnings = []

        # Check if we have an open zipfile
        if self._zipf is None:
            try:
                self._zipf = zipfile.ZipFile(self.path, "r")
            except zipfile.BadZipFile:
                return ValidationResult(
                    valid=False, errors=["Invalid ZIP file"], warnings=[]
                )

        # Check required files
        namelist = self._zipf.namelist()
        if "manifest.json" not in namelist:
            errors.append("Missing manifest.json")

        if "entries.json" not in namelist:
            errors.append("Missing entries.json")

        if errors:
            return ValidationResult(valid=False, errors=errors, warnings=warnings)

        # Parse manifest
        try:
            manifest_data = json.loads(self._zipf.read("manifest.json"))
            self._manifest = Manifest.from_dict(manifest_data)
        except (json.JSONDecodeError, KeyError) as e:
            errors.append(f"Invalid manifest.json: {e}")
            return ValidationResult(valid=False, errors=errors, warnings=warnings)

        # Check version compatibility
        if self._manifest.format_version != self.FORMAT_VERSION:
            errors.append(
                f"Unsupported format version: {self._manifest.format_version} "
                f"(expected {self.FORMAT_VERSION})"
            )
            return ValidationResult(valid=False, errors=errors, warnings=warnings)

        # Verify checksum
        entries_data = self._zipf.read("entries.json")
        actual_checksum = calculate_checksum(entries_data)
        if actual_checksum != self._manifest.checksum:
            errors.append(
                f"Checksum mismatch: archive may be corrupted. "
                f"Expected {self._manifest.checksum}, got {actual_checksum}"
            )
            return ValidationResult(valid=False, errors=errors, warnings=warnings)

        return ValidationResult(valid=True, errors=[], warnings=warnings)

    def get_manifest(self) -> Manifest:
        """Get archive manifest.

        Returns:
            Manifest object
        """
        if self._manifest is None:
            if self._zipf is None:
                self._zipf = zipfile.ZipFile(self.path, "r")
            manifest_data = json.loads(self._zipf.read("manifest.json"))
            self._manifest = Manifest.from_dict(manifest_data)
        return self._manifest

    def get_entries(self) -> list[Entry]:
        """Get all entries from archive.

        Returns:
            List of Entry objects
        """
        if self._entries is None:
            if self._zipf is None:
                self._zipf = zipfile.ZipFile(self.path, "r")
            entries_json = self._zipf.read("entries.json").decode("utf-8")
            self._entries = entries_from_json(entries_json)
        return self._entries
