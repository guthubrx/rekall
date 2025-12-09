"""Rekall data models."""

from __future__ import annotations

import math
import secrets
import time
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Literal, Optional

# Crockford Base32 alphabet (excludes I, L, O, U to avoid confusion)
ULID_ENCODING = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"

EntryType = Literal["bug", "pattern", "decision", "pitfall", "config", "reference"]
EntryStatus = Literal["active", "obsolete"]
MemoryType = Literal["episodic", "semantic"]
RelationType = Literal["related", "supersedes", "derived_from", "contradicts"]

VALID_TYPES = ("bug", "pattern", "decision", "pitfall", "config", "reference")
VALID_MEMORY_TYPES = ("episodic", "semantic")
VALID_RELATION_TYPES = ("related", "supersedes", "derived_from", "contradicts")


def generate_ulid() -> str:
    """Generate a ULID (Universally Unique Lexicographically Sortable Identifier).

    Returns a 26-character string that is:
    - Chronologically sortable (first 10 chars = timestamp)
    - Unique (last 16 chars = random)
    - Uses Crockford Base32 encoding
    """
    # Timestamp component: 10 characters encoding milliseconds since epoch
    timestamp = int(time.time() * 1000)
    time_part = ""
    for _ in range(10):
        time_part = ULID_ENCODING[timestamp % 32] + time_part
        timestamp //= 32

    # Random component: 16 characters
    random_part = "".join(secrets.choice(ULID_ENCODING) for _ in range(16))

    return time_part + random_part


@dataclass
class Entry:
    """A knowledge entry (bug, pattern, decision, etc.)."""

    id: str
    title: str
    type: EntryType
    content: str = ""
    project: Optional[str] = None
    tags: list[str] = field(default_factory=list)
    confidence: int = 2
    status: EntryStatus = "active"
    superseded_by: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    # Cognitive memory fields
    memory_type: MemoryType = "episodic"
    last_accessed: Optional[datetime] = None
    access_count: int = 0
    consolidation_score: float = 0.0
    next_review: Optional[date] = None
    review_interval: int = 1
    ease_factor: float = 2.5

    def __post_init__(self):
        """Validate entry fields after initialization."""
        if self.type not in VALID_TYPES:
            raise ValueError(f"invalid type: {self.type}. Valid: {', '.join(VALID_TYPES)}")
        if not 0 <= self.confidence <= 5:
            raise ValueError("confidence must be 0-5")
        if self.memory_type not in VALID_MEMORY_TYPES:
            raise ValueError(f"invalid memory_type: {self.memory_type}. Valid: {', '.join(VALID_MEMORY_TYPES)}")


@dataclass
class SearchResult:
    """A search result with ranking information."""

    entry: Entry
    rank: float  # BM25 score (lower = more relevant)
    snippet: str = ""  # Highlighted excerpt


@dataclass
class Link:
    """A connection between two entries in the knowledge graph."""

    id: str
    source_id: str
    target_id: str
    relation_type: RelationType
    created_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        """Validate link fields after initialization."""
        if self.relation_type not in VALID_RELATION_TYPES:
            raise ValueError(
                f"invalid relation_type: {self.relation_type}. "
                f"Valid: {', '.join(VALID_RELATION_TYPES)}"
            )
        if self.source_id == self.target_id:
            raise ValueError("cannot link entry to itself")


@dataclass
class ReviewItem:
    """An entry due for spaced repetition review."""

    entry: Entry
    days_overdue: int
    priority: float  # Higher = more urgent


def calculate_consolidation_score(access_count: int, days_since_access: int) -> float:
    """Calculate consolidation score based on access frequency and recency.

    Args:
        access_count: Total number of times the entry was accessed
        days_since_access: Days since last access

    Returns:
        Score between 0.0 and 1.0 (higher = more consolidated)
    """
    # Frequency factor (log scale to avoid explosion)
    frequency_factor = min(1.0, math.log(access_count + 1) / 5)
    # Freshness factor (exponential decay over 30 days)
    freshness_factor = math.exp(-days_since_access / 30)
    # Weighted combination: 60% frequency, 40% freshness
    return 0.6 * frequency_factor + 0.4 * freshness_factor


def calculate_next_interval(current_interval: int, quality: int) -> int:
    """Calculate next review interval using simplified SM-2 algorithm.

    Args:
        current_interval: Current interval in days
        quality: User rating 0-5 (0=forgot, 5=perfect)

    Returns:
        Next interval in days
    """
    if quality < 3:
        return 1  # Reset if failed recall
    ease_factor = max(1.3, 2.5 + 0.1 * (quality - 3))
    return max(1, int(current_interval * ease_factor))
