"""Security tests for Rekall - File permissions and data protection."""

import os
import stat
from pathlib import Path

import pytest

from rekall.constants import FILE_PERMISSIONS
from rekall.utils import check_file_permissions, secure_file_permissions


class TestFilePermissions:
    """Tests for file permission utilities."""

    def test_secure_file_permissions_sets_600(self, tmp_path: Path):
        """Test that secure_file_permissions sets mode to 0o600."""
        test_file = tmp_path / "test_file.txt"
        test_file.write_text("sensitive data")

        # Set insecure permissions first
        os.chmod(test_file, 0o644)
        assert stat.S_IMODE(test_file.stat().st_mode) == 0o644

        # Apply secure permissions
        secure_file_permissions(test_file)

        # Verify permissions are now 0o600
        actual_mode = stat.S_IMODE(test_file.stat().st_mode)
        assert actual_mode == FILE_PERMISSIONS, f"Expected 0o600, got {oct(actual_mode)}"

    def test_secure_file_permissions_idempotent(self, tmp_path: Path):
        """Test that calling secure_file_permissions twice is safe."""
        test_file = tmp_path / "test_file.txt"
        test_file.write_text("data")
        os.chmod(test_file, 0o644)

        # Call twice
        secure_file_permissions(test_file)
        secure_file_permissions(test_file)

        # Should still be 0o600
        assert stat.S_IMODE(test_file.stat().st_mode) == FILE_PERMISSIONS

    def test_secure_file_permissions_nonexistent_file(self, tmp_path: Path):
        """Test that secure_file_permissions handles nonexistent files gracefully."""
        nonexistent = tmp_path / "does_not_exist.txt"

        # Should not raise
        secure_file_permissions(nonexistent)

    def test_check_file_permissions_correct(self, tmp_path: Path):
        """Test check_file_permissions returns True for correct permissions."""
        test_file = tmp_path / "test_file.txt"
        test_file.write_text("data")
        os.chmod(test_file, FILE_PERMISSIONS)

        assert check_file_permissions(test_file) is True

    def test_check_file_permissions_incorrect(self, tmp_path: Path):
        """Test check_file_permissions returns False for incorrect permissions."""
        test_file = tmp_path / "test_file.txt"
        test_file.write_text("data")
        os.chmod(test_file, 0o644)

        assert check_file_permissions(test_file) is False

    def test_check_file_permissions_nonexistent(self, tmp_path: Path):
        """Test check_file_permissions returns True for nonexistent files."""
        nonexistent = tmp_path / "does_not_exist.txt"

        # Nonexistent files are considered OK (will be created with correct perms)
        assert check_file_permissions(nonexistent) is True


class TestDatabasePermissions:
    """Tests for database file permissions."""

    def test_database_init_sets_secure_permissions(self, tmp_path: Path):
        """Test that Database.init() sets secure permissions on DB file."""
        from rekall.db import Database

        db_path = tmp_path / "test.db"
        db = Database(db_path)
        db.init()

        try:
            # Verify DB file has 0o600 permissions
            actual_mode = stat.S_IMODE(db_path.stat().st_mode)
            assert actual_mode == FILE_PERMISSIONS, (
                f"DB file should have 0o600 permissions, got {oct(actual_mode)}"
            )
        finally:
            db.close()


class TestConfigPermissions:
    """Tests for config file permissions."""

    def test_save_config_sets_secure_permissions(self, tmp_path: Path):
        """Test that save_config_to_toml sets secure permissions."""
        from rekall.config import save_config_to_toml

        config_dir = tmp_path / "config"
        config_dir.mkdir()

        # Save config
        result = save_config_to_toml(config_dir, {"test_key": "test_value"})
        assert result is True

        # Verify config file has 0o600 permissions
        config_file = config_dir / "config.toml"
        assert config_file.exists()

        actual_mode = stat.S_IMODE(config_file.stat().st_mode)
        assert actual_mode == FILE_PERMISSIONS, (
            f"Config file should have 0o600 permissions, got {oct(actual_mode)}"
        )


class TestSecurityConstants:
    """Tests for security constants."""

    def test_file_permissions_is_600(self):
        """Test that FILE_PERMISSIONS constant is 0o600."""
        assert FILE_PERMISSIONS == 0o600

    def test_constants_are_reasonable(self):
        """Test that security constants have reasonable values."""
        from rekall.constants import (
            MAX_ARCHIVE_SIZE,
            MAX_COMPRESSION_RATIO,
            MAX_CONTENT_LENGTH,
            MAX_DECOMPRESSED_SIZE,
            MAX_ENTRIES_COUNT,
        )

        # Archive limits
        assert MAX_ARCHIVE_SIZE == 50 * 1024 * 1024  # 50 MB
        assert MAX_DECOMPRESSED_SIZE == 200 * 1024 * 1024  # 200 MB
        assert MAX_COMPRESSION_RATIO == 100  # 100:1 max

        # Entry limits
        assert MAX_CONTENT_LENGTH == 1_000_000  # 1 MB
        assert MAX_ENTRIES_COUNT == 100_000
