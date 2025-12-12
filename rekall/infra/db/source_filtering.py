# rekall/infra/db/source_filtering.py
"""
Advanced source filtering and search.

NOTE: Ce module est un placeholder pour la future extraction.
Actuellement, toute la logique est dans rekall.db.Database.

Future extraction - méthodes à extraire:
    - get_top_sources(limit) -> list[Source]
    - list_sources(limit, offset, order_by) -> list[Source]
    - get_prioritized_sources_for_theme(theme) -> list[Source]
    - get_sources_for_domain_boost() -> dict[str, Source]
    - get_dormant_sources(days) -> list[Source]
    - get_emerging_sources(days) -> list[Source]
    - get_source_statistics() -> dict
    - get_sources_to_verify(days) -> list[Source]
    - get_inaccessible_sources() -> list[Source]
    - search_sources_advanced(**kwargs) -> list[Source]
"""

from __future__ import annotations

# Placeholder - la logique reste dans rekall.db.Database
__all__: list[str] = []
