"""Rekall configuration."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import logging

# TOML support: use stdlib tomllib in Python 3.11+, fallback to tomli
try:
    import tomllib
except ImportError:
    import tomli as tomllib

import tomlkit

from rekall.paths import PathResolver, ResolvedPaths
from rekall.utils import secure_file_permissions

logger = logging.getLogger(__name__)


class ConfigError(Exception):
    """Raised when configuration file is invalid or cannot be loaded."""

    pass


def _default_paths() -> ResolvedPaths:
    """Get default resolved paths."""
    return PathResolver.resolve()


@dataclass
class Config:
    """Rekall configuration settings."""

    paths: ResolvedPaths = field(default_factory=_default_paths)
    editor: str | None = None
    default_project: str | None = None

    # Legacy embedding settings (external providers)
    embeddings_provider: str | None = None  # ollama | openai
    embeddings_model: str | None = None  # e.g., nomic-embed-text

    # Smart embeddings settings (local all-MiniLM-L6-v2)
    smart_embeddings_enabled: bool = False  # Enable semantic features
    smart_embeddings_model: str = "all-MiniLM-L6-v2"  # sentence-transformers model
    smart_embeddings_dimensions: int = 384  # Matryoshka: 128, 384, or 768
    smart_embeddings_similarity_threshold: float = 0.75  # Min similarity for suggestions
    smart_embeddings_context_mode: str = "required"  # required | recommended | optional (Feature 007)

    # Context size limit (Feature 007)
    max_context_size: int = 10240  # 10KB default, configurable in TUI Settings

    # UI settings
    ui_detail_panel_ratio: float = 1.0  # Detail panel height ratio (0.5 to 4.0)

    # Promotion settings (Feature 013)
    promotion_threshold: float = 70.0  # Score needed for auto-promotion
    promotion_near_threshold_pct: float = 0.8  # 80% of threshold = "near"
    promotion_citation_weight: float = 0.4  # Weight for citation count
    promotion_project_weight: float = 0.3  # Weight for project diversity
    promotion_recency_weight: float = 0.3  # Weight for recency
    promotion_recency_half_life_days: float = 30.0  # Score halves every N days
    promotion_max_citations: int = 10  # Citations cap
    promotion_max_projects: int = 5  # Projects cap

    # Auto-scan settings (Feature 013 extension)
    autoscan_enabled: bool = True  # Enable periodic auto-scan
    autoscan_interval_hours: float = 5.0  # Hours between auto-scans
    autoscan_connectors: str = "cursor"  # Comma-separated list of connectors to scan

    # Performance settings (Feature 020)
    perf_cache_max_size: int = 1000  # Max entries in embedding cache
    perf_cache_ttl_seconds: int = 600  # Cache TTL (10 min default)
    perf_model_idle_timeout_minutes: int = 10  # Unload model after N minutes idle
    perf_vector_backend: str = "auto"  # "auto", "sqlite-vec", "numpy"

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
_config: Config | None = None


def get_config(
    cli_db_path: Path | None = None,
    cli_config_path: Path | None = None,
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

    Raises:
        ConfigError: If the TOML file exists but is malformed
    """
    config_file = config_dir / "config.toml"
    if not config_file.exists():
        return {}

    try:
        with open(config_file, "rb") as f:
            return tomllib.load(f)
    except tomllib.TOMLDecodeError as e:
        logger.error("Invalid TOML in %s: %s", config_file, e)
        raise ConfigError(f"Configuration file is malformed: {config_file}\n{e}") from e
    except Exception as e:
        logger.error("Failed to load config from %s: %s", config_file, e)
        raise ConfigError(f"Failed to load configuration: {config_file}\n{e}") from e


def save_config_to_toml(config_dir: Path, updates: dict[str, Any]) -> bool:
    """Save configuration updates to config.toml file.

    Merges updates with existing config (preserves existing values).
    Uses tomlkit for proper TOML serialization.

    Args:
        config_dir: Directory containing config.toml
        updates: Dict with values to update

    Returns:
        True if successful, False otherwise
    """
    config_file = config_dir / "config.toml"

    # Load existing config (may raise ConfigError for malformed TOML)
    try:
        existing = load_config_from_toml(config_dir)
    except ConfigError:
        # If existing config is malformed, start fresh
        logger.warning("Existing config malformed, starting fresh: %s", config_file)
        existing = {}

    # Merge updates (deep merge for nested dicts)
    for key, value in updates.items():
        if isinstance(value, dict) and isinstance(existing.get(key), dict):
            existing[key].update(value)
        else:
            existing[key] = value

    # Create directory if needed
    config_dir.mkdir(parents=True, exist_ok=True)

    # Write TOML using tomlkit for proper serialization
    try:
        config_file.write_text(tomlkit.dumps(existing))
        # Secure file permissions (rw------- for sensitive config)
        secure_file_permissions(config_file)
        return True
    except Exception as e:
        logger.error("Failed to save config to %s: %s", config_file, e)
        return False


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

    # Apply promotion settings if present (Feature 013)
    promo = toml_data.get("promotion", {})
    if "threshold" in promo:
        config.promotion_threshold = float(promo["threshold"])
    if "near_threshold_pct" in promo:
        config.promotion_near_threshold_pct = float(promo["near_threshold_pct"])
    if "citation_weight" in promo:
        config.promotion_citation_weight = float(promo["citation_weight"])
    if "project_weight" in promo:
        config.promotion_project_weight = float(promo["project_weight"])
    if "recency_weight" in promo:
        config.promotion_recency_weight = float(promo["recency_weight"])
    if "recency_half_life_days" in promo:
        config.promotion_recency_half_life_days = float(promo["recency_half_life_days"])
    if "max_citations" in promo:
        config.promotion_max_citations = int(promo["max_citations"])
    if "max_projects" in promo:
        config.promotion_max_projects = int(promo["max_projects"])

    # Apply autoscan settings if present (Feature 013 extension)
    autoscan = toml_data.get("autoscan", {})
    if "enabled" in autoscan:
        config.autoscan_enabled = bool(autoscan["enabled"])
    if "interval_hours" in autoscan:
        config.autoscan_interval_hours = float(autoscan["interval_hours"])
    if "connectors" in autoscan:
        config.autoscan_connectors = str(autoscan["connectors"])

    # Apply performance settings if present (Feature 020)
    perf = toml_data.get("performance", {})
    if "cache_max_size" in perf:
        config.perf_cache_max_size = int(perf["cache_max_size"])
    if "cache_ttl_seconds" in perf:
        config.perf_cache_ttl_seconds = int(perf["cache_ttl_seconds"])
    if "model_idle_timeout_minutes" in perf:
        config.perf_model_idle_timeout_minutes = int(perf["model_idle_timeout_minutes"])
    if "vector_backend" in perf:
        backend = perf["vector_backend"]
        if backend in ("auto", "sqlite-vec", "numpy"):
            config.perf_vector_backend = backend

    return config


def get_promotion_config() -> "PromotionConfig":
    """Get promotion configuration from global config.

    Returns:
        PromotionConfig instance with current settings
    """
    from rekall.promotion import PromotionConfig

    config = get_config()
    return PromotionConfig(
        citation_weight=config.promotion_citation_weight,
        project_weight=config.promotion_project_weight,
        recency_weight=config.promotion_recency_weight,
        promotion_threshold=config.promotion_threshold,
        near_threshold_pct=config.promotion_near_threshold_pct,
        recency_half_life_days=config.promotion_recency_half_life_days,
        max_citations=config.promotion_max_citations,
        max_projects=config.promotion_max_projects,
    )


def set_promotion_config(
    threshold: float | None = None,
    citation_weight: float | None = None,
    project_weight: float | None = None,
    recency_weight: float | None = None,
    recency_half_life_days: float | None = None,
    max_citations: int | None = None,
    max_projects: int | None = None,
) -> bool:
    """Update promotion configuration and persist to config.toml.

    Args:
        threshold: Promotion threshold score (0-100)
        citation_weight: Weight for citation count (0-1)
        project_weight: Weight for project diversity (0-1)
        recency_weight: Weight for recency (0-1)
        recency_half_life_days: Half-life in days for recency decay
        max_citations: Maximum citations for normalization
        max_projects: Maximum projects for normalization

    Returns:
        True if successful, False otherwise
    """
    config = get_config()
    updates = {}

    if threshold is not None:
        updates["threshold"] = threshold
        config.promotion_threshold = threshold

    if citation_weight is not None:
        updates["citation_weight"] = citation_weight
        config.promotion_citation_weight = citation_weight

    if project_weight is not None:
        updates["project_weight"] = project_weight
        config.promotion_project_weight = project_weight

    if recency_weight is not None:
        updates["recency_weight"] = recency_weight
        config.promotion_recency_weight = recency_weight

    if recency_half_life_days is not None:
        updates["recency_half_life_days"] = recency_half_life_days
        config.promotion_recency_half_life_days = recency_half_life_days

    if max_citations is not None:
        updates["max_citations"] = max_citations
        config.promotion_max_citations = max_citations

    if max_projects is not None:
        updates["max_projects"] = max_projects
        config.promotion_max_projects = max_projects

    if updates:
        return save_config_to_toml(config.config_dir, {"promotion": updates})

    return True


@dataclass
class AutoscanConfig:
    """Configuration for periodic auto-scanning."""

    enabled: bool = True
    interval_hours: float = 5.0
    connectors: list[str] = field(default_factory=lambda: ["cursor"])


def get_autoscan_config() -> AutoscanConfig:
    """Get autoscan configuration from global config.

    Returns:
        AutoscanConfig instance with current settings
    """
    config = get_config()
    connectors = [c.strip() for c in config.autoscan_connectors.split(",") if c.strip()]
    return AutoscanConfig(
        enabled=config.autoscan_enabled,
        interval_hours=config.autoscan_interval_hours,
        connectors=connectors,
    )


def set_autoscan_config(
    enabled: bool | None = None,
    interval_hours: float | None = None,
    connectors: list[str] | None = None,
) -> bool:
    """Update autoscan configuration and persist to config.toml.

    Args:
        enabled: Enable/disable auto-scan
        interval_hours: Hours between auto-scans
        connectors: List of connector names to scan

    Returns:
        True if successful, False otherwise
    """
    config = get_config()
    updates = {}

    if enabled is not None:
        updates["enabled"] = enabled
        config.autoscan_enabled = enabled

    if interval_hours is not None:
        updates["interval_hours"] = interval_hours
        config.autoscan_interval_hours = interval_hours

    if connectors is not None:
        connectors_str = ",".join(connectors)
        updates["connectors"] = connectors_str
        config.autoscan_connectors = connectors_str

    if updates:
        return save_config_to_toml(config.config_dir, {"autoscan": updates})

    return True
