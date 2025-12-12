# rekall/infra/__init__.py
"""
Infrastructure layer - Database and external services.

Usage:
    from rekall.infra.db import Database
"""

from __future__ import annotations

from rekall.infra.db import Database, DatabaseError, MigrationError

__all__ = [
    "Database",
    "DatabaseError",
    "MigrationError",
]
