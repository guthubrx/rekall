# rekall/infra/db/__init__.py
"""
Database layer - Façade vers rekall.db.

Cette structure modulaire prépare la transition progressive vers des repositories séparés.
Pour l'instant, toutes les opérations sont déléguées à la classe Database existante.

Usage:
    from rekall.infra.db import Database
    db = Database()

    # Toutes les méthodes existantes fonctionnent:
    db.add(title="Test", url="https://example.com")
    db.search("query")
    db.get_source(1)
"""

from __future__ import annotations

# Import direct depuis le module original
from rekall.db import Database


# Exceptions (à créer si besoin, pour l'instant compatibilité)
class DatabaseError(Exception):
    """Base exception for database errors."""
    pass


class MigrationError(DatabaseError):
    """Exception raised during schema migrations."""
    pass


# Exports publics
__all__ = [
    "Database",
    "DatabaseError",
    "MigrationError",
]
