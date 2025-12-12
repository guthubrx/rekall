# rekall/infra/db/context_repo.py
"""
Repository for context storage and compression.

NOTE: Ce module est un placeholder pour la future extraction.
Actuellement, toute la logique est dans rekall.db.Database.

Future extraction - méthodes à extraire:
    - store_context(entry_id, context) -> bool
    - get_context(entry_id) -> str | None
    - get_contexts_for_verification(entry_ids) -> dict[str, str]
    - get_context_sizes() -> list[tuple[str, int]]
    - store_structured_context(entry_id, context) -> bool
    - get_structured_context(entry_id) -> StructuredContext | None
    - search_by_keywords(keywords) -> list[Entry]
    - get_entries_with_structured_context() -> list[str]
    - migrate_to_compressed_context() -> int
    - count_entries_without_context_blob() -> int

Functions:
    - compress_context(text: str) -> bytes
    - decompress_context(data: bytes) -> str
"""

from __future__ import annotations

# Placeholder - la logique reste dans rekall.db.Database
__all__: list[str] = []
