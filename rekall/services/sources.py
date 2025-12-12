# rekall/services/sources.py
"""
Source service - business logic for documentary sources.

NOTE: Ce module est un placeholder pour la future extraction.
La logique métier des sources est actuellement distribuée dans:
- rekall.db (Database class)
- rekall.cli_main (CLI commands)
- rekall.promotion (promotion logic)

Future extraction - logique à centraliser:
    class SourceService:
        - add_source(url, title, ...) -> Source
        - classify_source(id, classification) -> None
        - promote_source(id) -> None
        - demote_source(id) -> None
        - recalculate_scores() -> None
        - get_suggestions(theme) -> list[Source]
        - scan_connectors() -> list[NewSource]

Architecture:
    CLI/TUI -> SourceService -> Database
    (ne pas importer cli ou ui depuis ce module)
"""

from __future__ import annotations

# Placeholder - la logique sera extraite progressivement
__all__: list[str] = []
