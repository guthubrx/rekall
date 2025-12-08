"""Rekall configuration."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from rekall.paths import PathResolver, ResolvedPaths


def _default_paths() -> ResolvedPaths:
    """Get default resolved paths."""
    return PathResolver.resolve()


@dataclass
class Config:
    """Rekall configuration settings."""

    paths: ResolvedPaths = field(default_factory=_default_paths)
    editor: Optional[str] = None
    default_project: Optional[str] = None
    embeddings_provider: Optional[str] = None  # ollama | openai
    embeddings_model: Optional[str] = None  # e.g., nomic-embed-text

    @property
    def db_path(self) -> Path:
        """Get the database path (backward compatibility)."""
        return self.paths.db_path

    @property
    def rekall_dir(self) -> Path:
        """Get the Rekall data directory."""
        return self.paths.data_dir

    @property
    def config_dir(self) -> Path:
        """Get the Rekall config directory."""
        return self.paths.config_dir


# Global config instance
_config: Optional[Config] = None


def get_config(
    cli_db_path: Optional[Path] = None,
    cli_config_path: Optional[Path] = None,
    force_global: bool = False,
) -> Config:
    """Get the global configuration instance.

    Args:
        cli_db_path: Database path from CLI argument
        cli_config_path: Config path from CLI argument
        force_global: If True, skip local project detection (--global flag)
    """
    global _config
    if _config is None:
        paths = PathResolver.resolve(
            cli_db_path=cli_db_path,
            cli_config_path=cli_config_path,
            force_global=force_global,
        )
        _config = Config(paths=paths)
    return _config


def set_config(config: Config) -> None:
    """Set the global configuration instance."""
    global _config
    _config = config


def reset_config() -> None:
    """Reset the global configuration instance."""
    global _config
    _config = None
