# rekall/infra/db/source_promotion.py
"""
Source promotion and classification logic.

NOTE: Ce module est un placeholder pour la future extraction.
Actuellement, toute la logique est dans rekall.db.Database.

Future extraction - méthodes à extraire:
    Promotion:
    - check_promotion_criteria(source_id) -> tuple[bool, str]
    - promote_source(source_id) -> bool
    - demote_source(source_id) -> bool
    - get_promoted_sources() -> list[Source]
    - recalculate_all_promotions() -> tuple[int, int]

    Classification:
    - classify_source_auto(source_id) -> str
    - classify_source_manual(source_id, classification) -> bool

    Themes:
    - add_source_theme(source_id, theme) -> bool
    - get_source_themes(source_id) -> list[str]
    - remove_source_theme(source_id, theme) -> bool

    Seeds:
    - update_source_as_seed(source_id, is_seed) -> bool
    - get_seed_sources() -> list[Source]

    Known Domains:
    - get_known_domain(domain) -> dict | None
    - add_known_domain(domain, classification, ...) -> bool
"""

from __future__ import annotations

# Placeholder - la logique reste dans rekall.db.Database
__all__: list[str] = []
