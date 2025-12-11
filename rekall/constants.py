"""Security and validation constants for Rekall.

This module centralizes all limits and security constants used throughout
the application to ensure consistent validation and protection.
"""

# =============================================================================
# Entry Limits
# =============================================================================
MAX_TITLE_LENGTH = 500
MAX_CONTENT_LENGTH = 1_000_000  # 1 MB
MAX_TAGS_COUNT = 50
MAX_TAG_LENGTH = 100

# =============================================================================
# Archive Security Limits
# =============================================================================
MAX_ARCHIVE_SIZE = 50 * 1024 * 1024  # 50 MB compressed
MAX_DECOMPRESSED_SIZE = 200 * 1024 * 1024  # 200 MB decompressed
MAX_COMPRESSION_RATIO = 100  # Max 100:1 ratio (zip bomb protection)
MAX_ENTRIES_COUNT = 100_000

# =============================================================================
# Config Limits
# =============================================================================
MAX_INTEGRATIONS = 10

# =============================================================================
# File Security
# =============================================================================
FILE_PERMISSIONS = 0o600  # rw-------
DIR_PERMISSIONS = 0o700   # rwx------

# =============================================================================
# Database
# =============================================================================
DB_FILENAME = ".rekall.db"
CONFIG_FILENAME = ".rekall.toml"
