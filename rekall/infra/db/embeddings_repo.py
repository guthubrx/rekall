# rekall/infra/db/embeddings_repo.py
"""
Repository for embedding vector operations.

NOTE: Ce module est un placeholder pour la future extraction.
Actuellement, toute la logique est dans rekall.db.Database.

Future extraction - méthodes à extraire:
    - add_embedding(entry_id, embedding_type, vector, dimensions, model_name) -> str
    - get_embedding(entry_id, embedding_type) -> Embedding | None
    - get_embeddings(entry_id) -> list[Embedding]
    - delete_embedding(entry_id, embedding_type) -> bool
    - get_all_embeddings() -> list[Embedding]
    - count_embeddings() -> int
    - get_entries_without_embeddings(limit) -> list[str]
"""

from __future__ import annotations

# Placeholder - la logique reste dans rekall.db.Database
__all__: list[str] = []
