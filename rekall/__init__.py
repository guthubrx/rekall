"""Rekall - Developer Knowledge Management System.

Capture and retrieve bugs, patterns, decisions.
"""

# Suppress noisy warnings from dependencies
import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", message=".*urllib3.*OpenSSL.*")
warnings.filterwarnings("ignore", message=".*NotOpenSSLWarning.*")

# Semantic Versioning: MAJOR.MINOR.PATCH
# - MAJOR: Incompatible API/DB changes
# - MINOR: New features (backward compatible)
# - PATCH: Bug fixes (backward compatible)
__version_info__ = (0, 3, 0)
__version__ = ".".join(map(str, __version_info__))

# Release date (YYYY-MM-DD)
__release_date__ = "2025-12-10"

__author__ = "Rekall Contributors"


def get_version_string() -> str:
    """Get full version string with optional dev info."""
    return f"Rekall v{__version__} ({__release_date__})"


# =============================================================================
# Open Core: Auto-register default backends
# =============================================================================
# This ensures that importing rekall automatically sets up the default
# database and cache backends. Custom backends can override these by
# calling register_backend() after import.

def _init_backends() -> None:
    """Initialize default backends (called once on import)."""
    try:
        from rekall.infra.defaults import register_defaults

        register_defaults()
    except ImportError:
        # Infra module not available (partial install)
        pass


_init_backends()
