"""Tests for rekall archive module."""

from __future__ import annotations

import json
import zipfile
from datetime import datetime
from pathlib import Path

from rekall.models import Entry


class TestArchiveDataclasses:
    """Tests for archive dataclasses."""

    def test_archive_stats_creation(self):
        """Test ArchiveStats dataclass creation."""
        from rekall.archive import ArchiveStats

        stats = ArchiveStats(
            entries_count=10, projects=["p1", "p2"], types={"bug": 5, "pattern": 5}
        )
        assert stats.entries_count == 10
        assert stats.projects == ["p1", "p2"]
        assert stats.types["bug"] == 5

    def test_manifest_to_dict(self):
        """Test Manifest serialization to dict."""
        from rekall.archive import ArchiveStats, Manifest

        stats = ArchiveStats(entries_count=10, projects=["p1"], types={"bug": 5})
        manifest = Manifest(
            format_version="1.0",
            created_at=datetime(2025, 12, 7, 14, 30),
            rekall_version="0.1.0",
            checksum="sha256:abc123",
            stats=stats,
        )
        d = manifest.to_dict()
        assert d["format_version"] == "1.0"
        assert d["stats"]["entries_count"] == 10
        assert d["created_at"] == "2025-12-07T14:30:00"

    def test_manifest_from_dict(self):
        """Test Manifest deserialization from dict."""
        from rekall.archive import Manifest

        data = {
            "format_version": "1.0",
            "created_at": "2025-12-07T14:30:00",
            "rekall_version": "0.1.0",
            "checksum": "sha256:abc",
            "stats": {"entries_count": 5, "projects": [], "types": {}},
        }
        manifest = Manifest.from_dict(data)
        assert manifest.format_version == "1.0"
        assert manifest.rekall_version == "0.1.0"
        assert manifest.stats.entries_count == 5

    def test_validation_result_bool(self):
        """Test ValidationResult boolean behavior."""
        from rekall.archive import ValidationResult

        valid = ValidationResult(valid=True, errors=[], warnings=[])
        invalid = ValidationResult(valid=False, errors=["err"], warnings=[])
        assert valid
        assert not invalid


class TestChecksum:
    """Tests for checksum calculation."""

    def test_calculate_checksum(self):
        """Test checksum format."""
        from rekall.archive import calculate_checksum

        data = b'{"entries": []}'
        checksum = calculate_checksum(data)
        assert checksum.startswith("sha256:")
        assert len(checksum) == 71  # "sha256:" + 64 hex chars

    def test_checksum_deterministic(self):
        """Test checksum is deterministic."""
        from rekall.archive import calculate_checksum

        data = b"same content"
        assert calculate_checksum(data) == calculate_checksum(data)

    def test_checksum_different_content(self):
        """Test different content produces different checksums."""
        from rekall.archive import calculate_checksum

        assert calculate_checksum(b"a") != calculate_checksum(b"b")


class TestEntrySerialization:
    """Tests for entry serialization."""

    def test_entries_to_json(self):
        """Test entries serialization to JSON."""
        from rekall.archive import entries_to_json

        entries = [
            Entry(id="ABC123", title="Test", type="bug"),
        ]
        json_str = entries_to_json(entries)
        data = json.loads(json_str)
        assert len(data) == 1
        assert data[0]["id"] == "ABC123"

    def test_entries_from_json(self):
        """Test entries deserialization from JSON."""
        from rekall.archive import entries_from_json

        json_str = '[{"id": "X", "title": "T", "type": "bug", "content": "", "project": null, "tags": [], "confidence": 2, "status": "active", "superseded_by": null, "created_at": "2025-12-07T10:00:00", "updated_at": "2025-12-07T10:00:00"}]'
        entries = entries_from_json(json_str)
        assert len(entries) == 1
        assert entries[0].id == "X"
        assert entries[0].type == "bug"

    def test_round_trip_preserves_all_fields(self):
        """Test JSON round-trip preserves all fields."""
        from rekall.archive import entries_from_json, entries_to_json

        original = Entry(
            id="TEST123",
            title="Test Entry",
            type="pattern",
            content="Some content",
            project="myproj",
            tags=["a", "b"],
            confidence=4,
            status="active",
            created_at=datetime(2025, 12, 7, 10, 0),
            updated_at=datetime(2025, 12, 7, 12, 0),
        )
        json_str = entries_to_json([original])
        restored = entries_from_json(json_str)[0]

        assert restored.id == original.id
        assert restored.title == original.title
        assert restored.type == original.type
        assert restored.content == original.content
        assert restored.project == original.project
        assert restored.tags == original.tags
        assert restored.confidence == original.confidence
        assert restored.status == original.status
        assert restored.created_at == original.created_at
        assert restored.updated_at == original.updated_at


class TestRekallArchiveCreate:
    """Tests for RekallArchive.create()."""

    def test_create_archive_empty(self, tmp_path):
        """Test creating empty archive."""
        from rekall.archive import RekallArchive

        archive_path = tmp_path / "test.rekall"
        RekallArchive.create(archive_path, entries=[])

        assert archive_path.exists()
        assert zipfile.is_zipfile(archive_path)

    def test_create_archive_contains_manifest(self, tmp_path):
        """Test archive contains manifest.json."""
        from rekall.archive import RekallArchive

        archive_path = tmp_path / "test.rekall"
        RekallArchive.create(archive_path, entries=[])

        with zipfile.ZipFile(archive_path) as zf:
            assert "manifest.json" in zf.namelist()

    def test_create_archive_contains_entries(self, tmp_path):
        """Test archive contains entries.json."""
        from rekall.archive import RekallArchive

        archive_path = tmp_path / "test.rekall"
        entries = [Entry(id="X", title="T", type="bug")]
        RekallArchive.create(archive_path, entries=entries)

        with zipfile.ZipFile(archive_path) as zf:
            assert "entries.json" in zf.namelist()
            data = json.loads(zf.read("entries.json"))
            assert len(data) == 1
            assert data[0]["id"] == "X"

    def test_create_archive_manifest_stats(self, tmp_path):
        """Test manifest contains correct stats."""
        from rekall.archive import RekallArchive

        archive_path = tmp_path / "test.rekall"
        entries = [
            Entry(id="1", title="Bug1", type="bug", project="p1"),
            Entry(id="2", title="Pattern1", type="pattern", project="p1"),
            Entry(id="3", title="Bug2", type="bug", project="p2"),
        ]
        RekallArchive.create(archive_path, entries=entries)

        with zipfile.ZipFile(archive_path) as zf:
            manifest = json.loads(zf.read("manifest.json"))
            assert manifest["stats"]["entries_count"] == 3
            assert set(manifest["stats"]["projects"]) == {"p1", "p2"}
            assert manifest["stats"]["types"]["bug"] == 2
            assert manifest["stats"]["types"]["pattern"] == 1


class TestRekallArchiveOpen:
    """Tests for RekallArchive.open() and validate()."""

    def test_open_valid_archive(self, tmp_path):
        """Test opening valid archive."""
        from rekall.archive import RekallArchive

        archive_path = tmp_path / "test.rekall"
        RekallArchive.create(archive_path, entries=[])

        archive = RekallArchive.open(archive_path)
        assert archive is not None

    def test_open_invalid_file(self, tmp_path):
        """Test opening invalid file returns None or raises."""
        from rekall.archive import RekallArchive

        bad_file = tmp_path / "bad.rekall"
        bad_file.write_text("not a zip")

        archive = RekallArchive.open(bad_file)
        assert archive is None

    def test_validate_missing_manifest(self, tmp_path):
        """Test validation detects missing manifest."""
        from rekall.archive import RekallArchive

        archive_path = tmp_path / "bad.rekall"
        with zipfile.ZipFile(archive_path, "w") as zf:
            zf.writestr("entries.json", "[]")

        archive = RekallArchive.open(archive_path)
        result = archive.validate()
        assert not result.valid
        assert any("manifest" in err.lower() for err in result.errors)

    def test_validate_checksum_mismatch(self, tmp_path):
        """Test validation detects checksum mismatch."""
        from rekall.archive import RekallArchive

        archive_path = tmp_path / "test.rekall"
        RekallArchive.create(
            archive_path, entries=[Entry(id="X", title="T", type="bug")]
        )

        # Corrupt the archive by modifying entries.json
        # ZipFile doesn't allow in-place modification, so we recreate
        import tempfile

        with tempfile.NamedTemporaryFile(delete=False, suffix=".rekall") as tf:
            temp_path = Path(tf.name)

        with zipfile.ZipFile(archive_path, "r") as zf_in:
            manifest_data = zf_in.read("manifest.json")
            with zipfile.ZipFile(temp_path, "w") as zf_out:
                zf_out.writestr("manifest.json", manifest_data)
                zf_out.writestr("entries.json", '[{"id": "Y"}]')  # Different

        archive = RekallArchive.open(temp_path)
        result = archive.validate()
        assert not result.valid
        assert any("checksum" in err.lower() for err in result.errors)

        temp_path.unlink()

    def test_validate_success(self, tmp_path):
        """Test validation succeeds for valid archive."""
        from rekall.archive import RekallArchive

        archive_path = tmp_path / "test.rekall"
        RekallArchive.create(archive_path, entries=[])

        archive = RekallArchive.open(archive_path)
        result = archive.validate()
        assert result.valid

    def test_get_entries(self, tmp_path):
        """Test getting entries from archive."""
        from rekall.archive import RekallArchive

        archive_path = tmp_path / "test.rekall"
        original_entries = [
            Entry(id="A", title="First", type="bug"),
            Entry(id="B", title="Second", type="pattern"),
        ]
        RekallArchive.create(archive_path, entries=original_entries)

        archive = RekallArchive.open(archive_path)
        entries = archive.get_entries()
        assert len(entries) == 2
        assert entries[0].id == "A"
        assert entries[1].id == "B"

    def test_get_manifest(self, tmp_path):
        """Test getting manifest from archive."""
        from rekall.archive import RekallArchive

        archive_path = tmp_path / "test.rekall"
        RekallArchive.create(archive_path, entries=[Entry(id="X", title="T", type="bug")])

        archive = RekallArchive.open(archive_path)
        manifest = archive.get_manifest()
        assert manifest.format_version == "1.0"
        assert manifest.stats.entries_count == 1
