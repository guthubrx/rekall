# rekall/infra/db/access_tracking.py
"""
Repository for spaced repetition and access tracking.

NOTE: Ce module est un placeholder pour la future extraction.
Actuellement, toute la logique est dans rekall.db.Database.

Future extraction - méthodes à extraire:
    - _update_access_tracking(entry_id: str)
    - get_stale_entries(days: int) -> list[Entry]
    - get_due_entries() -> list[ReviewItem]
    - update_review_schedule(entry_id: str, quality: int)
"""

from __future__ import annotations

# Placeholder - la logique reste dans rekall.db.Database
__all__: list[str] = []
