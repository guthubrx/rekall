"""Rekall - Developer Knowledge Management System.

Capture and retrieve bugs, patterns, decisions.
"""

# Semantic Versioning: MAJOR.MINOR.PATCH
# - MAJOR: Incompatible API/DB changes
# - MINOR: New features (backward compatible)
# - PATCH: Bug fixes (backward compatible)
__version_info__ = (0, 2, 0)
__version__ = ".".join(map(str, __version_info__))

# Release date (YYYY-MM-DD)
__release_date__ = "2025-12-09"

__author__ = "Rekall Contributors"


def get_version_string() -> str:
    """Get full version string with optional dev info."""
    return f"Rekall v{__version__} ({__release_date__})"
