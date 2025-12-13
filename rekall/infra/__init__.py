# rekall/infra/__init__.py
"""
Infrastructure layer - Database, caching, and backend interfaces.

This module provides:
- Abstract interfaces for pluggable backends (Open Core architecture)
- Default implementations for Home users
- Service container for backend registration

Usage:
    # Existing API (unchanged)
    from rekall.infra.db import Database

    # New interfaces for custom backends
    from rekall.infra import DatabaseBackend, CacheBackend
    from rekall.infra import get_database, get_cache, register_backend
"""

from __future__ import annotations

# Existing exports (backward compatible)
from rekall.infra.db import Database, DatabaseError, MigrationError

# New interfaces (Open Core)
from rekall.infra.interfaces import CacheBackend, DatabaseBackend

# Service container helpers
from rekall.infra.container import (
    ServiceContainer,
    get_cache,
    get_database,
    has_backend,
    register_backend,
)

# Default implementations
from rekall.infra.defaults import (
    DefaultCacheBackend,
    DefaultDatabaseBackend,
    register_defaults,
)

__all__ = [
    # Existing (backward compatible)
    "Database",
    "DatabaseError",
    "MigrationError",
    # Interfaces (ABC)
    "DatabaseBackend",
    "CacheBackend",
    # Container
    "ServiceContainer",
    "get_database",
    "get_cache",
    "register_backend",
    "has_backend",
    # Default implementations
    "DefaultDatabaseBackend",
    "DefaultCacheBackend",
    "register_defaults",
]
