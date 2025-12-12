# rekall/infra/db/inbox_repo.py
"""
Repository for inbox (Bronze layer) operations.

NOTE: Ce module est un placeholder pour la future extraction.
Actuellement, toute la logique est dans rekall.db.Database.

Future extraction - méthodes à extraire:
    - add_inbox_entry(url, title, source, ...) -> int
    - get_inbox_entries(status, source, limit) -> list[InboxEntry]
    - get_inbox_not_enriched(limit) -> list[InboxEntry]
    - mark_inbox_enriched(id) -> bool
    - delete_inbox_entry(id) -> bool
    - clear_inbox(status) -> int
    - get_inbox_stats() -> dict
    - _row_to_inbox_entry(row) -> InboxEntry
"""

from __future__ import annotations

# Placeholder - la logique reste dans rekall.db.Database
__all__: list[str] = []
