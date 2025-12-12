# rekall/infra/db/suggestions_repo.py
"""
Repository for AI suggestion operations.

NOTE: Ce module est un placeholder pour la future extraction.
Actuellement, toute la logique est dans rekall.db.Database.

Future extraction - méthodes à extraire:
    - add_suggestion(type, entry_ids, reason, score) -> str
    - get_suggestion(id) -> Suggestion | None
    - get_suggestions(type, status, limit) -> list[Suggestion]
    - update_suggestion_status(id, status) -> bool
    - suggestion_exists(type, entry_ids) -> bool
"""

from __future__ import annotations

# Placeholder - la logique reste dans rekall.db.Database
__all__: list[str] = []
