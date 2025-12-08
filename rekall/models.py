"""Rekall data models."""

from __future__ import annotations

import secrets
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal, Optional

# Crockford Base32 alphabet (excludes I, L, O, U to avoid confusion)
ULID_ENCODING = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"

EntryType = Literal["bug", "pattern", "decision", "pitfall", "config", "reference"]
EntryStatus = Literal["active", "obsolete"]

VALID_TYPES = ("bug", "pattern", "decision", "pitfall", "config", "reference")


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

    def __post_init__(self):
        """Validate entry fields after initialization."""
        if self.type not in VALID_TYPES:
            raise ValueError(f"invalid type: {self.type}. Valid: {', '.join(VALID_TYPES)}")
        if not 0 <= self.confidence <= 5:
            raise ValueError("confidence must be 0-5")


@dataclass
class SearchResult:
    """A search result with ranking information."""

    entry: Entry
    rank: float  # BM25 score (lower = more relevant)
    snippet: str = ""  # Highlighted excerpt
