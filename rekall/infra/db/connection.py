# rekall/infra/db/connection.py
"""
Database connection and migration utilities.

NOTE: Ce module est un placeholder pour la future extraction.
Actuellement, toute la logique est dans rekall.db.Database.

Future extraction:
    - create_connection(db_path: Path) -> sqlite3.Connection
    - get_schema_version(conn) -> int
    - migrate_schema(conn, target_version: int | None) -> None
    - MIGRATIONS dict
    - CURRENT_SCHEMA_VERSION constant
"""

from __future__ import annotations

# Pour l'instant, re-export depuis le module principal
from rekall.db import CURRENT_SCHEMA_VERSION, MIGRATIONS

__all__ = [
    "CURRENT_SCHEMA_VERSION",
    "MIGRATIONS",
]
