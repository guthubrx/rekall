"""Rekall path resolution with XDG support.

This module handles cross-platform path resolution for Rekall configuration,
data, and cache directories. It follows the XDG Base Directory Specification
on Linux and macOS, and uses standard locations on Windows.

Priority order (first match wins):
1. CLI arguments (--db-path, --config-path)
2. Environment variables (REKALL_HOME, REKALL_DB_PATH)
3. Local project (.rekall/ in current directory)
4. User config file (data_dir in config.toml)
5. XDG environment variables ($XDG_CONFIG_HOME, $XDG_DATA_HOME)
6. Platform defaults (via platformdirs)
"""

from __future__ import annotations

import os
import platform
import shutil
import sys
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional

# On macOS, force XDG-style paths instead of ~/Library/
# This is per spec: "XDG uniquement sur Mac, identique à Linux"
if platform.system() == "Darwin":
    # Use Unix-style paths on macOS
    def user_config_dir(app: str) -> str:
        return str(Path.home() / ".config" / app)

    def user_data_dir(app: str) -> str:
        return str(Path.home() / ".local" / "share" / app)

    def user_cache_dir(app: str) -> str:
        return str(Path.home() / ".cache" / app)
else:
    from platformdirs import user_cache_dir, user_config_dir, user_data_dir

# TOML support: use stdlib tomllib in Python 3.11+, fallback to tomli
if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

APP_NAME = "rekall"


class PathSource(Enum):
    """Source of path resolution, in priority order."""

    CLI = "cli"  # --db-path, --config-path
    ENV = "env"  # REKALL_HOME, REKALL_DB_PATH
    LOCAL = "local"  # .rekall/ in current directory
    CONFIG = "config"  # data_dir in config.toml
    XDG = "xdg"  # $XDG_CONFIG_HOME, $XDG_DATA_HOME
    DEFAULT = "default"  # platformdirs defaults


@dataclass
class ResolvedPaths:
    """Resolved paths with source metadata."""

    config_dir: Path
    """Configuration directory (config.toml, etc.)"""

    data_dir: Path
    """Data directory (knowledge.db, etc.)"""

    cache_dir: Path
    """Cache directory (temporary files, etc.)"""

    db_path: Path
    """Full path to knowledge.db"""

    source: PathSource
    """Source that determined these paths"""

    is_local_project: bool = False
    """True if using .rekall/ in current directory"""

    def ensure_dirs(self) -> None:
        """Create all directories if they don't exist."""
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)


@dataclass
class MigrationInfo:
    """Information about a legacy installation migration."""

    legacy_path: Path
    """Old path (~/.rekall/)"""

    new_config_dir: Path
    new_data_dir: Path

    has_db: bool
    """True if knowledge.db exists in legacy"""

    has_config: bool
    """True if config.toml exists in legacy"""

    migrated_marker: Path = field(init=False)
    """Marker file created after migration"""

    def __post_init__(self):
        self.migrated_marker = self.legacy_path / ".rekall-migrated"


class PathResolver:
    """Resolves Rekall paths according to priority order."""

    @classmethod
    def resolve(
        cls,
        cli_db_path: Optional[Path] = None,
        cli_config_path: Optional[Path] = None,
        force_global: bool = False,
    ) -> ResolvedPaths:
        """Resolve paths according to priority order.

        Args:
            cli_db_path: Database path from CLI argument
            cli_config_path: Config path from CLI argument
            force_global: If True, skip local project detection (--global flag)

        Returns:
            ResolvedPaths with resolved directories and source
        """
        # 1. CLI arguments have highest priority
        result = cls._from_cli(cli_db_path, cli_config_path)
        if result is not None:
            return result

        # 2. Environment variables
        result = cls._from_env()
        if result is not None:
            return result

        # 3. Local project (unless --global)
        if not force_global:
            result = cls._from_local()
            if result is not None:
                return result

        # 4. User config file
        result = cls._from_config()
        if result is not None:
            return result

        # 5. XDG environment variables
        result = cls._from_xdg()
        if result is not None:
            return result

        # 6. Platform defaults (always returns a result)
        return cls._from_default()

    @classmethod
    def _from_cli(
        cls,
        db_path: Optional[Path],
        config_path: Optional[Path],
    ) -> Optional[ResolvedPaths]:
        """Resolve from CLI arguments."""
        if db_path is None and config_path is None:
            return None

        # Use provided paths or defaults
        if db_path is not None:
            data_dir = db_path.parent
            resolved_db = db_path
        else:
            data_dir = Path(user_data_dir(APP_NAME))
            resolved_db = data_dir / "knowledge.db"

        if config_path is not None:
            config_dir = config_path if config_path.is_dir() else config_path.parent
        else:
            config_dir = Path(user_config_dir(APP_NAME))

        cache_dir = Path(user_cache_dir(APP_NAME))

        return ResolvedPaths(
            config_dir=config_dir,
            data_dir=data_dir,
            cache_dir=cache_dir,
            db_path=resolved_db,
            source=PathSource.CLI,
        )

    @classmethod
    def _from_env(cls) -> Optional[ResolvedPaths]:
        """Resolve from environment variables."""
        rekall_home = os.environ.get("REKALL_HOME")
        rekall_db_path = os.environ.get("REKALL_DB_PATH")

        if rekall_home is None and rekall_db_path is None:
            return None

        if rekall_home is not None:
            # REKALL_HOME sets all directories
            home = Path(rekall_home)
            return ResolvedPaths(
                config_dir=home,
                data_dir=home,
                cache_dir=home / "cache",
                db_path=home / "knowledge.db",
                source=PathSource.ENV,
            )

        if rekall_db_path is not None:
            # REKALL_DB_PATH sets only the database location
            db_path = Path(rekall_db_path)
            return ResolvedPaths(
                config_dir=Path(user_config_dir(APP_NAME)),
                data_dir=db_path.parent,
                cache_dir=Path(user_cache_dir(APP_NAME)),
                db_path=db_path,
                source=PathSource.ENV,
            )

        return None

    @classmethod
    def _from_local(cls) -> Optional[ResolvedPaths]:
        """Resolve from local project .rekall/ directory."""
        local_dir = Path.cwd() / ".rekall"

        if not local_dir.exists():
            return None

        return ResolvedPaths(
            config_dir=local_dir,
            data_dir=local_dir,
            cache_dir=local_dir / "cache",
            db_path=local_dir / "knowledge.db",
            source=PathSource.LOCAL,
            is_local_project=True,
        )

    @classmethod
    def _from_config(cls) -> Optional[ResolvedPaths]:
        """Resolve from user config file."""
        # Find config file in XDG or default location
        xdg_config = os.environ.get("XDG_CONFIG_HOME")
        if xdg_config:
            config_dir = Path(xdg_config) / APP_NAME
        else:
            config_dir = Path(user_config_dir(APP_NAME))

        config_file = config_dir / "config.toml"

        if not config_file.exists():
            return None

        try:
            with open(config_file, "rb") as f:
                config_data = tomllib.load(f)
        except Exception:
            return None

        data_dir_str = config_data.get("data_dir")
        if data_dir_str is None:
            return None

        data_dir = Path(data_dir_str).expanduser()
        cache_dir = Path(user_cache_dir(APP_NAME))

        return ResolvedPaths(
            config_dir=config_dir,
            data_dir=data_dir,
            cache_dir=cache_dir,
            db_path=data_dir / "knowledge.db",
            source=PathSource.CONFIG,
        )

    @classmethod
    def _from_xdg(cls) -> Optional[ResolvedPaths]:
        """Resolve from XDG environment variables."""
        xdg_config = os.environ.get("XDG_CONFIG_HOME")
        xdg_data = os.environ.get("XDG_DATA_HOME")
        xdg_cache = os.environ.get("XDG_CACHE_HOME")

        # Only use XDG source if at least one XDG var is set
        if xdg_config is None and xdg_data is None and xdg_cache is None:
            return None

        config_dir = Path(xdg_config) / APP_NAME if xdg_config else Path(user_config_dir(APP_NAME))
        data_dir = Path(xdg_data) / APP_NAME if xdg_data else Path(user_data_dir(APP_NAME))
        cache_dir = Path(xdg_cache) / APP_NAME if xdg_cache else Path(user_cache_dir(APP_NAME))

        return ResolvedPaths(
            config_dir=config_dir,
            data_dir=data_dir,
            cache_dir=cache_dir,
            db_path=data_dir / "knowledge.db",
            source=PathSource.XDG,
        )

    @classmethod
    def _from_default(cls) -> ResolvedPaths:
        """Resolve from platform defaults (always succeeds)."""
        config_dir = Path(user_config_dir(APP_NAME))
        data_dir = Path(user_data_dir(APP_NAME))
        cache_dir = Path(user_cache_dir(APP_NAME))

        return ResolvedPaths(
            config_dir=config_dir,
            data_dir=data_dir,
            cache_dir=cache_dir,
            db_path=data_dir / "knowledge.db",
            source=PathSource.DEFAULT,
        )


def check_legacy_migration() -> Optional[MigrationInfo]:
    """Check if legacy installation exists and needs migration.

    Returns:
        MigrationInfo if legacy installation found, None otherwise
    """
    legacy_path = Path.home() / ".rekall"

    # No legacy installation
    if not legacy_path.exists():
        return None

    # Already migrated
    marker = legacy_path / ".rekall-migrated"
    if marker.exists():
        return None

    # Check what exists in legacy
    has_db = (legacy_path / "knowledge.db").exists()
    has_config = (legacy_path / "config.toml").exists()

    # Nothing to migrate
    if not has_db and not has_config:
        return None

    # Get new paths
    new_config_dir = Path(user_config_dir(APP_NAME))
    new_data_dir = Path(user_data_dir(APP_NAME))

    # Skip if new paths already have data
    if (new_data_dir / "knowledge.db").exists():
        return None

    return MigrationInfo(
        legacy_path=legacy_path,
        new_config_dir=new_config_dir,
        new_data_dir=new_data_dir,
        has_db=has_db,
        has_config=has_config,
    )


def perform_migration(info: MigrationInfo) -> bool:
    """Perform migration from legacy to XDG paths.

    Args:
        info: Migration information

    Returns:
        True if successful, False otherwise
    """
    try:
        # Create new directories
        info.new_config_dir.mkdir(parents=True, exist_ok=True)
        info.new_data_dir.mkdir(parents=True, exist_ok=True)

        # Copy database
        if info.has_db:
            src_db = info.legacy_path / "knowledge.db"
            dst_db = info.new_data_dir / "knowledge.db"
            shutil.copy2(src_db, dst_db)

        # Copy config
        if info.has_config:
            src_config = info.legacy_path / "config.toml"
            dst_config = info.new_config_dir / "config.toml"
            shutil.copy2(src_config, dst_config)

        # Create migration marker
        info.migrated_marker.write_text(
            f"Migrated to XDG paths on {__import__('datetime').datetime.now().isoformat()}\n"
            f"Config: {info.new_config_dir}\n"
            f"Data: {info.new_data_dir}\n"
        )

        return True
    except Exception:
        return False


def init_local_project(path: Optional[Path] = None, exclude_db_from_git: bool = False) -> Path:
    """Initialize a local .rekall/ project directory.

    Args:
        path: Directory to initialize (defaults to cwd)
        exclude_db_from_git: If True, exclude knowledge.db from git (default: False = versioned)

    Returns:
        Path to created .rekall/ directory
    """
    base = path or Path.cwd()
    local_dir = base / ".rekall"

    # Create directory
    local_dir.mkdir(parents=True, exist_ok=True)

    # Create .gitignore
    gitignore_path = local_dir / ".gitignore"
    if not gitignore_path.exists():
        if exclude_db_from_git:
            gitignore_content = (
                "# Rekall local project\n"
                "# Database excluded from version control (local data only)\n"
                "knowledge.db\n"
                "\n"
                "# Always ignore cache\n"
                "cache/\n"
            )
        else:
            gitignore_content = (
                "# Rekall local project\n"
                "# Database versioned (team sharing)\n"
                "# Uncomment to exclude from version control:\n"
                "# knowledge.db\n"
                "\n"
                "# Always ignore cache\n"
                "cache/\n"
            )
        gitignore_path.write_text(gitignore_content)

    return local_dir
