# rekall/infra/db/knowledge_graph.py
"""
Repository for knowledge graph (links) operations.

NOTE: Ce module est un placeholder pour la future extraction.
Actuellement, toute la logique est dans rekall.db.Database.

Future extraction - méthodes à extraire:
    - add_link(source_id, target_id, relation_type, reason) -> str
    - get_links(entry_id, direction) -> list[Link]
    - delete_link(source_id, target_id, relation_type) -> bool
    - count_links(entry_id) -> int
    - get_related_entries(entry_id) -> list[tuple[Entry, Link]]
    - count_links_by_direction(entry_id) -> tuple[int, int]
    - render_graph_ascii(entry_id) -> str
    - _render_subtree(...)
"""

from __future__ import annotations

# Placeholder - la logique reste dans rekall.db.Database
__all__: list[str] = []
