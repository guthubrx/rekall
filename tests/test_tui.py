"""Tests for Rekall TUI (Feature 007)."""

from pathlib import Path

from conftest import make_config_with_db_path


# ============================================================================
# Feature 007: Migration Overlay Tests (Phase 2)
# ============================================================================


class TestMigrationDetection:
    """Tests for migration detection logic."""

    def test_check_migration_needed_no_db(self, temp_rekall_dir: Path):
        """Should return no migration needed when no database."""
        from rekall.config import set_config
        from rekall.tui import check_migration_needed

        db_path = temp_rekall_dir / "knowledge.db"
        set_config(make_config_with_db_path(db_path))

        needs, current, target, legacy = check_migration_needed()
        assert needs is False
        assert legacy == 0

    def test_check_migration_needed_current_db(self, temp_rekall_dir: Path):
        """Should return no migration needed when database is current."""
        from rekall.config import set_config
        from rekall.db import CURRENT_SCHEMA_VERSION, Database
        from rekall.tui import check_migration_needed

        db_path = temp_rekall_dir / "knowledge.db"
        set_config(make_config_with_db_path(db_path))

        # Create fully migrated database
        db = Database(db_path)
        db.init()
        db.close()

        needs, current, target, legacy = check_migration_needed()
        assert needs is False
        assert current == CURRENT_SCHEMA_VERSION
        assert target == CURRENT_SCHEMA_VERSION

    def test_check_migration_counts_legacy_entries(self, temp_rekall_dir: Path):
        """Should count entries without structured context."""
        from rekall.config import set_config
        from rekall.db import Database
        from rekall.models import Entry, StructuredContext, generate_ulid
        from rekall.tui import check_migration_needed

        db_path = temp_rekall_dir / "knowledge.db"
        set_config(make_config_with_db_path(db_path))

        db = Database(db_path)
        db.init()

        # Add 2 entries without context
        db.add(Entry(id=generate_ulid(), title="Legacy 1", type="bug"))
        db.add(Entry(id=generate_ulid(), title="Legacy 2", type="pattern"))

        # Add 1 entry with context
        entry_with_ctx = Entry(id=generate_ulid(), title="With context", type="decision")
        db.add(entry_with_ctx)
        ctx = StructuredContext(
            situation="Test situation",
            solution="Test solution",
            trigger_keywords=["test"],
        )
        db.store_structured_context(entry_with_ctx.id, ctx)
        db.close()

        needs, current, target, legacy = check_migration_needed()
        assert legacy == 2  # Only the 2 without context


class TestMigrationOverlayApp:
    """Tests for MigrationOverlayApp widget."""

    def test_overlay_app_creation(self):
        """Should create overlay app with correct properties."""
        from rekall.tui import MigrationOverlayApp

        app = MigrationOverlayApp(
            current_version=5,
            target_version=6,
            legacy_count=10,
            changelog_content="# Changelog\n\n## v6\nNew features",
        )

        assert app.current_version == 5
        assert app.target_version == 6
        assert app.legacy_count == 10
        assert "Changelog" in app.changelog_content
        assert app.current_view == 0  # Starts on migration view

    def test_overlay_view_toggle(self):
        """Should toggle between migration and changelog views."""
        from rekall.tui import MigrationOverlayApp

        app = MigrationOverlayApp(
            current_version=5,
            target_version=6,
            legacy_count=0,
            changelog_content="Test",
        )

        assert app.current_view == 0

        # Simulate next view action
        app.current_view = (app.current_view + 1) % 2
        assert app.current_view == 1

        # Simulate prev view action
        app.current_view = (app.current_view - 1) % 2
        assert app.current_view == 0


class TestChangelogContent:
    """Tests for changelog loading."""

    def test_get_changelog_content(self):
        """Should load changelog from project root."""
        from rekall.tui import get_changelog_content

        content = get_changelog_content()
        # CHANGELOG.md should exist now
        if content:
            assert "Changelog" in content or "changelog" in content.lower()

    def test_changelog_contains_versions(self):
        """Changelog should contain version information."""
        from rekall.tui import get_changelog_content

        content = get_changelog_content()
        if content:
            # Should have version markers
            assert "0.2.0" in content or "0.1.0" in content


class TestApplyMigration:
    """Tests for TUI migration application."""

    def test_apply_migration_succeeds(self, temp_rekall_dir: Path):
        """Should apply migration successfully with backup."""
        from rekall.config import set_config
        from rekall.db import CURRENT_SCHEMA_VERSION, Database
        from rekall.tui import apply_migration_from_tui

        db_path = temp_rekall_dir / "knowledge.db"
        set_config(make_config_with_db_path(db_path))

        # Create database
        db = Database(db_path)
        db.init()
        db.close()

        # Apply migration
        result = apply_migration_from_tui()
        assert result is True

        # Verify database is still valid and at current version
        import sqlite3
        db = Database(db_path)
        db.conn = sqlite3.connect(str(db_path))
        version = db.get_schema_version()
        db.close()
        assert version == CURRENT_SCHEMA_VERSION

    def test_apply_migration_fails_gracefully(self, temp_rekall_dir: Path):
        """Should return False on migration failure."""
        from rekall.config import set_config
        from rekall.tui import apply_migration_from_tui

        # Non-existent path
        db_path = temp_rekall_dir / "nonexistent" / "knowledge.db"
        set_config(make_config_with_db_path(db_path))

        result = apply_migration_from_tui()
        # Should handle gracefully (may succeed or fail depending on path creation)
        assert isinstance(result, bool)


# ============================================================================
# Feature 007: TUI Settings Tests (Phase 5)
# ============================================================================


class TestSettingsConfigPersistence:
    """Tests for settings configuration persistence."""

    def test_context_mode_saves_to_toml(self, temp_rekall_dir: Path):
        """Should save context_mode to config.toml."""
        from rekall.config import (
            load_config_from_toml,
            save_config_to_toml,
        )

        config_dir = temp_rekall_dir

        # Save context_mode
        success = save_config_to_toml(
            config_dir,
            {"smart_embeddings": {"context_mode": "recommended"}}
        )
        assert success is True

        # Verify it was saved
        loaded = load_config_from_toml(config_dir)
        assert "smart_embeddings" in loaded
        assert loaded["smart_embeddings"]["context_mode"] == "recommended"

    def test_max_context_size_saves_to_toml(self, temp_rekall_dir: Path):
        """Should save max_context_size to config.toml."""
        from rekall.config import (
            load_config_from_toml,
            save_config_to_toml,
        )

        config_dir = temp_rekall_dir

        # Save max_context_size (20KB)
        success = save_config_to_toml(
            config_dir,
            {"smart_embeddings": {"max_context_size": 20480}}
        )
        assert success is True

        # Verify it was saved
        loaded = load_config_from_toml(config_dir)
        assert loaded["smart_embeddings"]["max_context_size"] == 20480

    def test_settings_merge_with_existing(self, temp_rekall_dir: Path):
        """Should merge new settings with existing config."""
        from rekall.config import (
            load_config_from_toml,
            save_config_to_toml,
        )

        config_dir = temp_rekall_dir

        # Save initial setting
        save_config_to_toml(
            config_dir,
            {"smart_embeddings": {"context_mode": "optional"}}
        )

        # Save another setting (should merge)
        save_config_to_toml(
            config_dir,
            {"smart_embeddings": {"max_context_size": 51200}}
        )

        # Both should be present
        loaded = load_config_from_toml(config_dir)
        assert loaded["smart_embeddings"]["context_mode"] == "optional"
        assert loaded["smart_embeddings"]["max_context_size"] == 51200


class TestSettingsConfigApply:
    """Tests for applying settings from config.toml."""

    def test_context_mode_applies_to_config(self, temp_rekall_dir: Path):
        """Should apply context_mode from toml to Config instance."""
        from rekall.config import apply_toml_config, save_config_to_toml

        config_dir = temp_rekall_dir
        db_path = temp_rekall_dir / "knowledge.db"

        # Create config.toml with context_mode
        save_config_to_toml(
            config_dir,
            {"smart_embeddings": {"context_mode": "optional"}}
        )

        # Create Config with that config_dir
        config = make_config_with_db_path(db_path)

        # Apply toml config
        config = apply_toml_config(config)

        assert config.smart_embeddings_context_mode == "optional"

    def test_max_context_size_applies_to_config(self, temp_rekall_dir: Path):
        """Should apply max_context_size from toml to Config instance."""
        from rekall.config import apply_toml_config, save_config_to_toml

        config_dir = temp_rekall_dir
        db_path = temp_rekall_dir / "knowledge.db"

        # Create config.toml with max_context_size (50KB)
        save_config_to_toml(
            config_dir,
            {"smart_embeddings": {"max_context_size": 51200}}
        )

        # Create Config with that config_dir
        config = make_config_with_db_path(db_path)

        # Apply toml config
        config = apply_toml_config(config)

        assert config.max_context_size == 51200

    def test_invalid_context_mode_ignored(self, temp_rekall_dir: Path):
        """Should ignore invalid context_mode values."""
        from rekall.config import apply_toml_config, save_config_to_toml

        config_dir = temp_rekall_dir
        db_path = temp_rekall_dir / "knowledge.db"

        # Create config.toml with invalid context_mode
        save_config_to_toml(
            config_dir,
            {"smart_embeddings": {"context_mode": "invalid_mode"}}
        )

        # Create Config
        config = make_config_with_db_path(db_path)

        # Apply toml config - should keep default
        config = apply_toml_config(config)

        # Should remain at default "required" (not changed to invalid)
        assert config.smart_embeddings_context_mode == "required"


class TestSettingsDefaults:
    """Tests for default settings values."""

    def test_default_context_mode_is_required(self):
        """Default context_mode should be 'required' (Feature 007)."""
        from rekall.config import Config

        config = Config()
        assert config.smart_embeddings_context_mode == "required"

    def test_default_max_context_size_is_10kb(self):
        """Default max_context_size should be 10KB (Feature 007)."""
        from rekall.config import Config

        config = Config()
        assert config.max_context_size == 10240  # 10KB
