# rekall/infra/db/sources_repo.py
"""
Repository for source CRUD and backlinks.

NOTE: Ce module est un placeholder pour la future extraction.
Actuellement, toute la logique est dans rekall.db.Database.

Future extraction - méthodes à extraire:
    CRUD:
    - add_source(url, title, domain, ...) -> int
    - get_source(id) -> Source | None
    - get_source_by_domain(domain, url_pattern) -> Source | None
    - get_source_by_url(url) -> Source | None
    - update_source(id, **kwargs) -> bool
    - delete_source(id) -> bool
    - _row_to_source(row) -> Source

    Backlinks:
    - link_entry_to_source(entry_id, source_id) -> bool
    - get_entry_sources(entry_id) -> list[Source]
    - unlink_entry_from_source(entry_id, source_id) -> bool
    - get_source_backlinks(source_id) -> list[Entry]
    - count_source_backlinks(source_id) -> int
    - get_backlinks_by_domain(domain) -> list[dict]
"""

from __future__ import annotations

# Placeholder - la logique reste dans rekall.db.Database
__all__: list[str] = []
