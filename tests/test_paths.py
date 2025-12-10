"""Tests for rekall.paths module."""

import os
from unittest import mock

from rekall.paths import (
    MigrationInfo,
    PathResolver,
    PathSource,
    ResolvedPaths,
    check_legacy_migration,
    init_local_project,
    perform_migration,
)


class TestPathSource:
    """Tests for PathSource enum."""

    def test_path_source_values(self):
        """Test PathSource enum values."""
        assert PathSource.CLI.value == "cli"
        assert PathSource.ENV.value == "env"
        assert PathSource.LOCAL.value == "local"
        assert PathSource.CONFIG.value == "config"
        assert PathSource.XDG.value == "xdg"
        assert PathSource.DEFAULT.value == "default"

    def test_path_source_priority_order(self):
        """Test that PathSource values are in priority order."""
        sources = list(PathSource)
        assert sources[0] == PathSource.CLI
        assert sources[-1] == PathSource.DEFAULT


class TestResolvedPaths:
    """Tests for ResolvedPaths dataclass."""

    def test_resolved_paths_creation(self, tmp_path):
        """Test ResolvedPaths can be created."""
        paths = ResolvedPaths(
            config_dir=tmp_path / "config",
            data_dir=tmp_path / "data",
            cache_dir=tmp_path / "cache",
            db_path=tmp_path / "data" / "knowledge.db",
            source=PathSource.DEFAULT,
        )
        assert paths.config_dir == tmp_path / "config"
        assert paths.data_dir == tmp_path / "data"
        assert paths.source == PathSource.DEFAULT
        assert paths.is_local_project is False

    def test_resolved_paths_local_project(self, tmp_path):
        """Test ResolvedPaths with local project flag."""
        paths = ResolvedPaths(
            config_dir=tmp_path / ".rekall",
            data_dir=tmp_path / ".rekall",
            cache_dir=tmp_path / ".rekall" / "cache",
            db_path=tmp_path / ".rekall" / "knowledge.db",
            source=PathSource.LOCAL,
            is_local_project=True,
        )
        assert paths.is_local_project is True

    def test_ensure_dirs(self, tmp_path):
        """Test ensure_dirs creates all directories."""
        paths = ResolvedPaths(
            config_dir=tmp_path / "config",
            data_dir=tmp_path / "data",
            cache_dir=tmp_path / "cache",
            db_path=tmp_path / "data" / "knowledge.db",
            source=PathSource.DEFAULT,
        )

        # Directories don't exist yet
        assert not paths.config_dir.exists()
        assert not paths.data_dir.exists()
        assert not paths.cache_dir.exists()

        # Create them
        paths.ensure_dirs()

        # Now they exist
        assert paths.config_dir.exists()
        assert paths.data_dir.exists()
        assert paths.cache_dir.exists()


class TestPathResolver:
    """Tests for PathResolver class."""

    def test_default_paths_linux_macos(self):
        """Test default paths on Linux/macOS."""
        with mock.patch.dict(os.environ, {}, clear=True):
            paths = PathResolver._from_default()

        assert paths.source == PathSource.DEFAULT
        assert "rekall" in str(paths.config_dir)
        assert "rekall" in str(paths.data_dir)
        assert paths.db_path.name == "knowledge.db"

    def test_xdg_vars_respected(self, tmp_path):
        """Test that XDG environment variables are respected."""
        xdg_config = tmp_path / "custom_config"
        xdg_data = tmp_path / "custom_data"

        with mock.patch.dict(
            os.environ,
            {
                "XDG_CONFIG_HOME": str(xdg_config),
                "XDG_DATA_HOME": str(xdg_data),
            },
            clear=True,
        ):
            paths = PathResolver._from_xdg()

        assert paths is not None
        assert paths.source == PathSource.XDG
        assert paths.config_dir == xdg_config / "rekall"
        assert paths.data_dir == xdg_data / "rekall"

    def test_xdg_returns_none_when_not_set(self):
        """Test _from_xdg returns None when no XDG vars set."""
        with mock.patch.dict(os.environ, {}, clear=True):
            paths = PathResolver._from_xdg()
        assert paths is None

    def test_env_rekall_home(self, tmp_path):
        """Test REKALL_HOME environment variable."""
        rekall_home = tmp_path / "rekall_custom"

        with mock.patch.dict(
            os.environ,
            {"REKALL_HOME": str(rekall_home)},
            clear=True,
        ):
            paths = PathResolver._from_env()

        assert paths is not None
        assert paths.source == PathSource.ENV
        assert paths.config_dir == rekall_home
        assert paths.data_dir == rekall_home
        assert paths.db_path == rekall_home / "knowledge.db"

    def test_env_rekall_db_path(self, tmp_path):
        """Test REKALL_DB_PATH environment variable."""
        db_path = tmp_path / "custom" / "my.db"

        with mock.patch.dict(
            os.environ,
            {"REKALL_DB_PATH": str(db_path)},
            clear=True,
        ):
            paths = PathResolver._from_env()

        assert paths is not None
        assert paths.source == PathSource.ENV
        assert paths.db_path == db_path
        assert paths.data_dir == db_path.parent

    def test_env_returns_none_when_not_set(self):
        """Test _from_env returns None when no env vars set."""
        with mock.patch.dict(os.environ, {}, clear=True):
            paths = PathResolver._from_env()
        assert paths is None

    def test_local_project_detection(self, tmp_path):
        """Test local .rekall/ detection."""
        local_dir = tmp_path / ".rekall"
        local_dir.mkdir()

        with mock.patch("rekall.paths.Path.cwd", return_value=tmp_path):
            paths = PathResolver._from_local()

        assert paths is not None
        assert paths.source == PathSource.LOCAL
        assert paths.is_local_project is True
        assert paths.config_dir == local_dir
        assert paths.data_dir == local_dir

    def test_local_returns_none_when_no_rekall_dir(self, tmp_path):
        """Test _from_local returns None when no .rekall/ exists."""
        with mock.patch("rekall.paths.Path.cwd", return_value=tmp_path):
            paths = PathResolver._from_local()
        assert paths is None

    def test_local_priority_over_global(self, tmp_path):
        """Test local project has priority over global XDG."""
        local_dir = tmp_path / ".rekall"
        local_dir.mkdir()

        with mock.patch("rekall.paths.Path.cwd", return_value=tmp_path):
            with mock.patch.dict(
                os.environ,
                {"XDG_CONFIG_HOME": str(tmp_path / "xdg")},
                clear=True,
            ):
                paths = PathResolver.resolve()

        assert paths.source == PathSource.LOCAL
        assert paths.is_local_project is True

    def test_config_data_dir(self, tmp_path):
        """Test data_dir from config.toml."""
        config_dir = tmp_path / "config" / "rekall"
        config_dir.mkdir(parents=True)
        config_file = config_dir / "config.toml"
        custom_data = tmp_path / "custom_data"
        config_file.write_text(f'data_dir = "{custom_data}"')

        with mock.patch.dict(
            os.environ,
            {"XDG_CONFIG_HOME": str(tmp_path / "config")},
            clear=True,
        ):
            paths = PathResolver._from_config()

        assert paths is not None
        assert paths.source == PathSource.CONFIG
        assert paths.data_dir == custom_data

    def test_cli_db_path(self, tmp_path):
        """Test CLI --db-path argument."""
        db_path = tmp_path / "custom" / "db.sqlite"

        paths = PathResolver._from_cli(db_path=db_path, config_path=None)

        assert paths is not None
        assert paths.source == PathSource.CLI
        assert paths.db_path == db_path
        assert paths.data_dir == db_path.parent

    def test_resolve_priority_cli_first(self, tmp_path):
        """Test CLI args have highest priority."""
        db_path = tmp_path / "cli.db"
        local_dir = tmp_path / ".rekall"
        local_dir.mkdir()

        with mock.patch("rekall.paths.Path.cwd", return_value=tmp_path):
            with mock.patch.dict(
                os.environ,
                {"REKALL_HOME": str(tmp_path / "env")},
                clear=True,
            ):
                paths = PathResolver.resolve(cli_db_path=db_path)

        assert paths.source == PathSource.CLI

    def test_resolve_force_global_skips_local(self, tmp_path):
        """Test force_global=True skips local project detection."""
        local_dir = tmp_path / ".rekall"
        local_dir.mkdir()

        with mock.patch("rekall.paths.Path.cwd", return_value=tmp_path):
            with mock.patch.dict(os.environ, {}, clear=True):
                paths = PathResolver.resolve(force_global=True)

        assert paths.source == PathSource.DEFAULT
        assert paths.is_local_project is False


class TestMigration:
    """Tests for migration functions."""

    def test_migration_info_creation(self, tmp_path):
        """Test MigrationInfo dataclass."""
        info = MigrationInfo(
            legacy_path=tmp_path / ".rekall",
            new_config_dir=tmp_path / "config",
            new_data_dir=tmp_path / "data",
            has_db=True,
            has_config=False,
        )

        assert info.legacy_path == tmp_path / ".rekall"
        assert info.migrated_marker == tmp_path / ".rekall" / ".rekall-migrated"

    def test_check_legacy_migration_no_legacy(self, tmp_path):
        """Test check_legacy_migration returns None when no legacy dir."""
        with mock.patch("rekall.paths.Path.home", return_value=tmp_path):
            info = check_legacy_migration()
        assert info is None

    def test_check_legacy_migration_already_migrated(self, tmp_path):
        """Test check_legacy_migration returns None when already migrated."""
        legacy_dir = tmp_path / ".rekall"
        legacy_dir.mkdir()
        (legacy_dir / "knowledge.db").touch()
        (legacy_dir / ".rekall-migrated").touch()

        with mock.patch("rekall.paths.Path.home", return_value=tmp_path):
            info = check_legacy_migration()
        assert info is None

    def test_check_legacy_migration_found(self, tmp_path):
        """Test check_legacy_migration detects legacy installation."""
        legacy_dir = tmp_path / ".rekall"
        legacy_dir.mkdir()
        (legacy_dir / "knowledge.db").write_text("test")
        (legacy_dir / "config.toml").write_text("test")

        with mock.patch("rekall.paths.Path.home", return_value=tmp_path):
            with mock.patch("rekall.paths.user_config_dir", return_value=str(tmp_path / "config")):
                with mock.patch("rekall.paths.user_data_dir", return_value=str(tmp_path / "data")):
                    info = check_legacy_migration()

        assert info is not None
        assert info.has_db is True
        assert info.has_config is True

    def test_perform_migration(self, tmp_path):
        """Test perform_migration copies files."""
        legacy_dir = tmp_path / ".rekall"
        legacy_dir.mkdir()
        (legacy_dir / "knowledge.db").write_text("db content")
        (legacy_dir / "config.toml").write_text("config content")

        info = MigrationInfo(
            legacy_path=legacy_dir,
            new_config_dir=tmp_path / "config" / "rekall",
            new_data_dir=tmp_path / "data" / "rekall",
            has_db=True,
            has_config=True,
        )

        result = perform_migration(info)

        assert result is True
        assert (tmp_path / "data" / "rekall" / "knowledge.db").exists()
        assert (tmp_path / "config" / "rekall" / "config.toml").exists()
        assert info.migrated_marker.exists()


class TestInitLocalProject:
    """Tests for init_local_project function."""

    def test_init_local_project(self, tmp_path):
        """Test init_local_project creates .rekall/ with .gitignore."""
        result = init_local_project(tmp_path)

        assert result == tmp_path / ".rekall"
        assert result.exists()
        assert (result / ".gitignore").exists()

        gitignore = (result / ".gitignore").read_text()
        assert "cache/" in gitignore

    def test_init_local_project_idempotent(self, tmp_path):
        """Test init_local_project is safe to run multiple times."""
        init_local_project(tmp_path)
        (tmp_path / ".rekall" / "knowledge.db").write_text("test")

        # Run again
        result = init_local_project(tmp_path)

        # Should not overwrite existing files
        assert result == tmp_path / ".rekall"
        assert (tmp_path / ".rekall" / "knowledge.db").read_text() == "test"
