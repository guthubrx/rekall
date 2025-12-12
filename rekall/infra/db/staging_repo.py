# rekall/infra/db/staging_repo.py
"""
Repository for staging (Silver layer) operations.

NOTE: Ce module est un placeholder pour la future extraction.
Actuellement, toute la logique est dans rekall.db.Database.

Future extraction - méthodes à extraire:
    - add_staging_entry(url, title, summary, ...) -> int
    - get_staging_by_url(url) -> StagingEntry | None
    - get_staging_entries(status, limit) -> list[StagingEntry]
    - get_staging_eligible_for_promotion(threshold) -> list[StagingEntry]
    - update_staging(id, **kwargs) -> bool
    - _row_to_staging_entry(row) -> StagingEntry
"""

from __future__ import annotations

# Placeholder - la logique reste dans rekall.db.Database
__all__: list[str] = []
