# rekall/services/__init__.py
"""
Business logic services layer.

This package provides business logic services that sit between the presentation
layer (CLI/TUI) and the infrastructure layer (Database).

Architecture:
    Presentation (cli, ui) -> Services -> Infrastructure (db)

Current Services:
    - promotion: Source promotion/demotion logic (existing)
    - embeddings: Embedding generation and similarity (existing)

Future Services (placeholders):
    - entries: Entry CRUD and search logic
    - sources: Source management logic

Usage:
    from rekall.services import PromotionService
    from rekall.services import EmbeddingsService
"""

from __future__ import annotations

# Re-export existing services from their current locations
from rekall.embeddings import EmbeddingService, get_embedding_service
from rekall.promotion import (
    PromotionConfig,
    PromotionResult,
    auto_promote_eligible,
    calculate_promotion_score,
    demote_source,
    promote_source,
)

__all__ = [
    # Embeddings
    "EmbeddingService",
    "get_embedding_service",
    # Promotion
    "PromotionConfig",
    "PromotionResult",
    "calculate_promotion_score",
    "promote_source",
    "demote_source",
    "auto_promote_eligible",
]
