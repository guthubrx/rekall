"""Rekall configuration."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

# TOML support: use stdlib tomllib in Python 3.11+, fallback to tomli
try:
    import tomllib
except ImportError:
    import tomli as tomllib

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

    # Legacy embedding settings (external providers)
    embeddings_provider: Optional[str] = None  # ollama | openai
    embeddings_model: Optional[str] = None  # e.g., nomic-embed-text

    # Smart embeddings settings (local EmbeddingGemma)
    smart_embeddings_enabled: bool = False  # Enable semantic features
    smart_embeddings_model: str = "EmbeddingGemma-2B-v1"  # sentence-transformers model
    smart_embeddings_dimensions: int = 384  # Matryoshka: 128, 384, or 768
    smart_embeddings_similarity_threshold: float = 0.75  # Min similarity for suggestions
    smart_embeddings_context_mode: str = "required"  # required | recommended | optional (Feature 007)

    # Context size limit (Feature 007)
    max_context_size: int = 10240  # 10KB default, configurable in TUI Settings

    # UI settings
    ui_detail_panel_ratio: float = 1.0  # Detail panel height ratio (0.5 to 4.0)

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
        # Apply settings from config.toml
        _config = apply_toml_config(_config)
    return _config


def set_config(config: Config) -> None:
    """Set the global configuration instance."""
    global _config
    _config = config


def reset_config() -> None:
    """Reset the global configuration instance."""
    global _config
    _config = None


def load_config_from_toml(config_dir: Path) -> dict[str, Any]:
    """Load configuration from config.toml file.

    Args:
        config_dir: Directory containing config.toml

    Returns:
        Dict with configuration values (empty if file doesn't exist)
    """
    config_file = config_dir / "config.toml"
    if not config_file.exists():
        return {}

    try:
        with open(config_file, "rb") as f:
            return tomllib.load(f)
    except Exception:
        return {}


def save_config_to_toml(config_dir: Path, updates: dict[str, Any]) -> bool:
    """Save configuration updates to config.toml file.

    Merges updates with existing config (preserves existing values).

    Args:
        config_dir: Directory containing config.toml
        updates: Dict with values to update

    Returns:
        True if successful, False otherwise
    """
    config_file = config_dir / "config.toml"

    # Load existing config
    existing = load_config_from_toml(config_dir)

    # Merge updates (deep merge for nested dicts)
    for key, value in updates.items():
        if isinstance(value, dict) and isinstance(existing.get(key), dict):
            existing[key].update(value)
        else:
            existing[key] = value

    # Create directory if needed
    config_dir.mkdir(parents=True, exist_ok=True)

    # Write TOML manually (tomllib is read-only)
    try:
        lines = []
        for key, value in existing.items():
            if isinstance(value, dict):
                # Section header
                lines.append(f"\n[{key}]")
                for sub_key, sub_value in value.items():
                    lines.append(_format_toml_value(sub_key, sub_value))
            else:
                lines.append(_format_toml_value(key, value))

        config_file.write_text("\n".join(lines).strip() + "\n")
        return True
    except Exception:
        return False


def _format_toml_value(key: str, value: Any) -> str:
    """Format a key-value pair for TOML."""
    if isinstance(value, bool):
        return f"{key} = {str(value).lower()}"
    elif isinstance(value, (int, float)):
        return f"{key} = {value}"
    elif isinstance(value, str):
        return f'{key} = "{value}"'
    else:
        return f'{key} = "{value}"'


def apply_toml_config(config: Config) -> Config:
    """Apply settings from config.toml to Config instance.

    Args:
        config: Config instance to update

    Returns:
        Updated Config instance
    """
    toml_data = load_config_from_toml(config.config_dir)

    # Apply smart_embeddings settings if present
    embeddings = toml_data.get("smart_embeddings", {})
    if "enabled" in embeddings:
        config.smart_embeddings_enabled = embeddings["enabled"]
    if "model" in embeddings:
        config.smart_embeddings_model = embeddings["model"]
    if "dimensions" in embeddings:
        config.smart_embeddings_dimensions = embeddings["dimensions"]
    if "similarity_threshold" in embeddings:
        config.smart_embeddings_similarity_threshold = embeddings["similarity_threshold"]
    if "context_mode" in embeddings:
        mode = embeddings["context_mode"]
        if mode in ("required", "recommended", "optional"):
            config.smart_embeddings_context_mode = mode
    if "max_context_size" in embeddings:
        config.max_context_size = int(embeddings["max_context_size"])

    # Apply UI settings if present
    ui = toml_data.get("ui", {})
    if "detail_panel_ratio" in ui:
        ratio = float(ui["detail_panel_ratio"])
        if 0.5 <= ratio <= 4.0:
            config.ui_detail_panel_ratio = ratio

    return config
