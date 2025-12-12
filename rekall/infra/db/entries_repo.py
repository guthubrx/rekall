# rekall/infra/db/entries_repo.py
"""
Repository for entry CRUD operations.

NOTE: Ce module est un placeholder pour la future extraction.
Actuellement, toute la logique est dans rekall.db.Database.

Future extraction - méthodes à extraire:
    - add() -> int
    - get(id: int) -> Entry | None
    - update(id: int, **kwargs) -> bool
    - delete(id: int) -> bool
    - search(query: str, limit: int) -> list[Entry]
    - list_all(limit: int, offset: int) -> list[Entry]
    - _refresh_fts(entry_id: str)
    - _row_to_entry(row, tags) -> Entry
"""

from __future__ import annotations

# Placeholder - la logique reste dans rekall.db.Database
__all__: list[str] = []
