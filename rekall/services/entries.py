# rekall/services/entries.py
"""
Entry service - business logic for knowledge entries.

NOTE: Ce module est un placeholder pour la future extraction.
La logique métier des entrées est actuellement distribuée dans:
- rekall.db (Database class)
- rekall.cli_main (CLI commands)

Future extraction - logique à centraliser:
    class EntryService:
        - create_entry(title, url, ...) -> Entry
        - update_entry(id, ...) -> Entry
        - deprecate_entry(id, reason) -> None
        - search_entries(query, filters) -> list[Entry]
        - get_similar_entries(id, count) -> list[Entry]
        - generalize_entries(ids) -> Entry
        - validate_entry(entry) -> ValidationResult

Architecture:
    CLI/TUI -> EntryService -> Database
    (ne pas importer cli ou ui depuis ce module)
"""

from __future__ import annotations

# Placeholder - la logique sera extraite progressivement
__all__: list[str] = []
