"""Promotion scoring and logic for Sources Medallion.

This module handles the Silver → Gold transformation:
- Calculate promotion scores based on citation count, project diversity, and recency
- Determine promotion eligibility
- Execute promotions from staging to sources
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from rekall.db import Database
    from rekall.models import StagingEntry


@dataclass
class PromotionConfig:
    """Configuration for promotion scoring."""

    # Weight factors (should sum to ~1.0 for normalized scores)
    citation_weight: float = 0.4
    project_weight: float = 0.3
    recency_weight: float = 0.3

    # Thresholds
    promotion_threshold: float = 70.0  # Score needed for auto-promotion
    near_threshold_pct: float = 0.8  # 80% of threshold = "near"

    # Decay settings
    recency_half_life_days: float = 30.0  # Score halves every 30 days without activity

    # Caps for normalization
    max_citations: int = 10  # Citations above this don't add more score
    max_projects: int = 5  # Projects above this don't add more score


# Default configuration
DEFAULT_CONFIG = PromotionConfig()


def calculate_promotion_score(
    staging: "StagingEntry",
    config: Optional[PromotionConfig] = None,
    now: Optional[datetime] = None,
) -> float:
    """Calculate promotion score for a staging entry.

    The score is based on three factors:
    - Citation count: How many times the URL was captured
    - Project diversity: Number of different projects that used it
    - Recency: Time since last seen, with exponential decay

    Args:
        staging: The staging entry to score
        config: Scoring configuration (uses config from config.toml if None)
        now: Current time for recency calculation (uses datetime.now() if None)

    Returns:
        Score from 0.0 to 100.0
    """
    if config is None:
        # Use configuration from config.toml or defaults
        try:
            from rekall.config import get_promotion_config
            config = get_promotion_config()
        except Exception:
            config = DEFAULT_CONFIG
    if now is None:
        now = datetime.now()

    # Citation score (0-100)
    citation_score = min(staging.citation_count / config.max_citations, 1.0) * 100

    # Project diversity score (0-100)
    project_score = min(staging.project_count / config.max_projects, 1.0) * 100

    # Recency score with decay (0-100)
    if staging.last_seen:
        days_since = (now - staging.last_seen).total_seconds() / 86400
        # Exponential decay: score = 100 * 0.5^(days / half_life)
        decay_factor = 0.5 ** (days_since / config.recency_half_life_days)
        recency_score = decay_factor * 100
    else:
        recency_score = 0.0

    # Weighted sum
    total_score = (
        citation_score * config.citation_weight
        + project_score * config.project_weight
        + recency_score * config.recency_weight
    )

    return round(total_score, 2)


def is_eligible_for_promotion(
    staging: "StagingEntry",
    config: Optional[PromotionConfig] = None,
    score: Optional[float] = None,
) -> bool:
    """Check if a staging entry is eligible for promotion.

    Args:
        staging: The staging entry to check
        config: Scoring configuration
        score: Pre-calculated score (will calculate if None)

    Returns:
        True if eligible for promotion
    """
    if config is None:
        config = DEFAULT_CONFIG

    if score is None:
        score = calculate_promotion_score(staging, config)

    # Must be accessible
    if not staging.is_accessible:
        return False

    # Must not already be promoted
    if staging.promoted_at is not None:
        return False

    return score >= config.promotion_threshold


def is_near_promotion(
    staging: "StagingEntry",
    config: Optional[PromotionConfig] = None,
    score: Optional[float] = None,
) -> bool:
    """Check if a staging entry is near the promotion threshold.

    Args:
        staging: The staging entry to check
        config: Scoring configuration
        score: Pre-calculated score (will calculate if None)

    Returns:
        True if within 80% of promotion threshold
    """
    if config is None:
        config = DEFAULT_CONFIG

    if score is None:
        score = calculate_promotion_score(staging, config)

    near_threshold = config.promotion_threshold * config.near_threshold_pct
    return score >= near_threshold and score < config.promotion_threshold


def get_promotion_indicator(
    staging: "StagingEntry",
    config: Optional[PromotionConfig] = None,
    score: Optional[float] = None,
) -> str:
    """Get promotion status indicator for display.

    Args:
        staging: The staging entry
        config: Scoring configuration
        score: Pre-calculated score

    Returns:
        Indicator string: "⬆" (eligible), "→" (near), "✓" (promoted), or " "
    """
    if staging.promoted_at is not None:
        return "✓"

    if not staging.is_accessible:
        return "⚠"

    if is_eligible_for_promotion(staging, config, score):
        return "⬆"

    if is_near_promotion(staging, config, score):
        return "→"

    return " "


@dataclass
class PromotionResult:
    """Result of a promotion operation."""

    success: bool
    source_id: Optional[str] = None
    staging_id: Optional[str] = None
    error: Optional[str] = None


def promote_source(
    db: "Database",
    staging: "StagingEntry",
    notes: Optional[str] = None,
) -> PromotionResult:
    """Promote a staging entry to Gold (sources table).

    Creates a new Source from the staging entry and marks
    the staging entry as promoted.

    Args:
        db: Database instance
        staging: Staging entry to promote
        notes: Optional notes for the new source

    Returns:
        PromotionResult with success status and IDs
    """
    from rekall.models import Source, generate_ulid

    # Check if URL already exists in sources
    existing = db.get_source_by_url(staging.url)
    if existing:
        return PromotionResult(
            success=False,
            source_id=existing.id,
            staging_id=staging.id,
            error="URL already exists in sources",
        )

    # Create new source
    # Note: Source model uses url_pattern for full URL, and has limited fields
    now = datetime.now()
    source = Source(
        id=generate_ulid(),
        domain=staging.domain,
        url_pattern=staging.url,  # Store full URL as pattern
        personal_score=staging.promotion_score or 50.0,
        usage_count=staging.citation_count,
        last_used=staging.last_seen,
        status="active" if staging.is_accessible else "inaccessible",
        role="unclassified",
        is_promoted=True,
        promoted_at=now,
        created_at=now,
    )

    try:
        db.add_source(source)

        # Update staging entry
        staging.promoted_at = now
        staging.promoted_to = source.id
        db.update_staging(staging)

        return PromotionResult(
            success=True,
            source_id=source.id,
            staging_id=staging.id,
        )
    except Exception as e:
        return PromotionResult(
            success=False,
            staging_id=staging.id,
            error=str(e),
        )


def demote_source(
    db: "Database",
    source_id: str,
) -> PromotionResult:
    """Demote a source back to staging only.

    Removes the source from the sources table and resets
    the staging entry's promotion status.

    Args:
        db: Database instance
        source_id: ID of the source to demote

    Returns:
        PromotionResult with success status
    """
    # Find source
    source = db.get_source(source_id)
    if not source:
        return PromotionResult(
            success=False,
            source_id=source_id,
            error="Source not found",
        )

    # Validate: only promoted sources can be demoted
    if not source.is_promoted:
        return PromotionResult(
            success=False,
            source_id=source_id,
            error="Source was not promoted (is_promoted=False)",
        )

    # Find associated staging entry using url_pattern (Source model uses url_pattern, not url)
    staging = db.get_staging_by_url(source.url_pattern)
    if staging:
        # Reset promotion status
        staging.promoted_at = None
        staging.promoted_to = None
        db.update_staging(staging)

    # Delete source
    try:
        db.delete_source(source_id)
        return PromotionResult(
            success=True,
            source_id=source_id,
            staging_id=staging.id if staging else None,
        )
    except Exception as e:
        return PromotionResult(
            success=False,
            source_id=source_id,
            error=str(e),
        )


@dataclass
class BatchPromotionResult:
    """Result of batch promotion operation."""

    total_eligible: int = 0
    promoted: int = 0
    failed: int = 0
    already_promoted: int = 0
    errors: list[str] = None

    def __post_init__(self):
        if self.errors is None:
            self.errors = []


def auto_promote_eligible(
    db: "Database",
    config: Optional[PromotionConfig] = None,
    dry_run: bool = False,
) -> BatchPromotionResult:
    """Automatically promote all eligible staging entries.

    Args:
        db: Database instance
        config: Scoring configuration
        dry_run: If True, don't actually promote, just count

    Returns:
        BatchPromotionResult with statistics
    """
    if config is None:
        config = DEFAULT_CONFIG

    result = BatchPromotionResult()

    # Get all staging entries
    entries = db.get_staging_entries(limit=1000)

    for entry in entries:
        if entry.promoted_at is not None:
            result.already_promoted += 1
            continue

        score = calculate_promotion_score(entry, config)
        if not is_eligible_for_promotion(entry, config, score):
            continue

        result.total_eligible += 1

        if dry_run:
            continue

        # Update score before promotion
        entry.promotion_score = score
        db.update_staging(entry)

        # Promote
        promotion_result = promote_source(db, entry)
        if promotion_result.success:
            result.promoted += 1
        else:
            result.failed += 1
            if promotion_result.error:
                result.errors.append(f"{entry.url}: {promotion_result.error}")

    return result
