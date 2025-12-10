"""Rekall data models."""

from __future__ import annotations

import math
import secrets
import time
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import TYPE_CHECKING, Literal, Optional

if TYPE_CHECKING:
    import numpy as np

# Crockford Base32 alphabet (excludes I, L, O, U to avoid confusion)
ULID_ENCODING = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"

EntryType = Literal["bug", "pattern", "decision", "pitfall", "config", "reference"]
EntryStatus = Literal["active", "obsolete"]
MemoryType = Literal["episodic", "semantic"]
RelationType = Literal["related", "supersedes", "derived_from", "contradicts"]

# Embedding types for smart embeddings feature (v3)
EmbeddingType = Literal["summary", "context"]
SuggestionType = Literal["link", "generalize"]
SuggestionStatus = Literal["pending", "accepted", "rejected"]

VALID_TYPES = ("bug", "pattern", "decision", "pitfall", "config", "reference")
VALID_MEMORY_TYPES = ("episodic", "semantic")
VALID_RELATION_TYPES = ("related", "supersedes", "derived_from", "contradicts")
VALID_EMBEDDING_TYPES = ("summary", "context")
VALID_SUGGESTION_TYPES = ("link", "generalize")
VALID_SUGGESTION_STATUSES = ("pending", "accepted", "rejected")
VALID_EMBEDDING_DIMENSIONS = (128, 384, 768)


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
    reason: Optional[str] = None  # Justification for the link (helps AI understand intent)

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


@dataclass
class Embedding:
    """Vector representation of an entry for semantic similarity.

    Supports Matryoshka dimensions (768, 384, 128) for storage optimization.
    Two types: 'summary' (title+content+tags) and 'context' (full conversation).
    """

    id: str
    entry_id: str
    embedding_type: EmbeddingType
    vector: bytes  # numpy array serialized via tobytes()
    dimensions: int
    model_name: str
    created_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        """Validate embedding fields after initialization."""
        if self.embedding_type not in VALID_EMBEDDING_TYPES:
            raise ValueError(
                f"invalid embedding_type: {self.embedding_type}. "
                f"Valid: {', '.join(VALID_EMBEDDING_TYPES)}"
            )
        if self.dimensions not in VALID_EMBEDDING_DIMENSIONS:
            raise ValueError(
                f"invalid dimensions: {self.dimensions}. "
                f"Valid: {VALID_EMBEDDING_DIMENSIONS}"
            )

    def to_numpy(self) -> "np.ndarray":
        """Deserialize vector bytes to numpy array.

        Returns:
            numpy float32 array of shape (dimensions,)
        """
        import numpy as np

        return np.frombuffer(self.vector, dtype=np.float32)

    @classmethod
    def from_numpy(
        cls,
        entry_id: str,
        embedding_type: EmbeddingType,
        array: "np.ndarray",
        model_name: str,
    ) -> "Embedding":
        """Create Embedding from numpy array.

        Args:
            entry_id: ID of the entry this embedding belongs to
            embedding_type: 'summary' or 'context'
            array: numpy array of float32 values
            model_name: name of the model used to generate embedding

        Returns:
            Embedding instance with serialized vector
        """
        import numpy as np

        return cls(
            id=generate_ulid(),
            entry_id=entry_id,
            embedding_type=embedding_type,
            vector=array.astype(np.float32).tobytes(),
            dimensions=len(array),
            model_name=model_name,
        )


@dataclass
class Suggestion:
    """A proposed action detected by the system (link or generalization).

    Link suggestions connect 2 similar entries.
    Generalization suggestions group 3+ episodic entries into a semantic pattern.
    """

    id: str
    suggestion_type: SuggestionType
    entry_ids: list[str]
    score: float  # Similarity score 0.0-1.0
    reason: str = ""
    status: SuggestionStatus = "pending"
    created_at: datetime = field(default_factory=datetime.now)
    resolved_at: Optional[datetime] = None

    def __post_init__(self):
        """Validate suggestion fields after initialization."""
        if self.suggestion_type not in VALID_SUGGESTION_TYPES:
            raise ValueError(
                f"invalid suggestion_type: {self.suggestion_type}. "
                f"Valid: {', '.join(VALID_SUGGESTION_TYPES)}"
            )
        if self.status not in VALID_SUGGESTION_STATUSES:
            raise ValueError(
                f"invalid status: {self.status}. "
                f"Valid: {', '.join(VALID_SUGGESTION_STATUSES)}"
            )
        if not 0.0 <= self.score <= 1.0:
            raise ValueError(f"score must be 0.0-1.0, got: {self.score}")
        if self.suggestion_type == "link" and len(self.entry_ids) != 2:
            raise ValueError("link suggestion must have exactly 2 entry_ids")
        if self.suggestion_type == "generalize" and len(self.entry_ids) < 3:
            raise ValueError("generalize suggestion must have 3+ entry_ids")

    def entry_ids_json(self) -> str:
        """Serialize entry_ids for SQLite storage.

        Returns:
            JSON string array of entry IDs
        """
        import json

        return json.dumps(self.entry_ids)

    @classmethod
    def from_row(cls, row: dict) -> "Suggestion":
        """Create Suggestion from database row.

        Args:
            row: dict with keys matching Suggestion fields,
                 entry_ids as JSON string

        Returns:
            Suggestion instance
        """
        import json

        return cls(
            id=row["id"],
            suggestion_type=row["suggestion_type"],
            entry_ids=json.loads(row["entry_ids"]),
            score=row["score"],
            reason=row.get("reason", ""),
            status=row["status"],
            created_at=datetime.fromisoformat(row["created_at"]),
            resolved_at=(
                datetime.fromisoformat(row["resolved_at"])
                if row.get("resolved_at")
                else None
            ),
        )


# Structured context types for v6 (Feature 006)
ContextExtractionMethod = Literal["manual", "auto", "hybrid"]


@dataclass
class StructuredContext:
    """Contexte structuré pour désambiguïsation des entrées.

    Permet de capturer le contexte riche d'une découverte/solution
    pour faciliter la recherche et éviter les faux positifs sur
    des embeddings similaires.
    """

    # Champs obligatoires
    situation: str  # Quel était le problème initial ?
    solution: str  # Comment l'as-tu résolu ?
    trigger_keywords: list[str]  # Mots-clés pour retrouver

    # Champs optionnels
    what_failed: Optional[str] = None  # Ce qui n'a pas marché
    conversation_excerpt: Optional[str] = None  # Extrait conversation
    files_modified: Optional[list[str]] = None  # Fichiers touchés
    error_messages: Optional[list[str]] = None  # Erreurs rencontrées

    # Méta
    created_at: datetime = field(default_factory=datetime.now)
    extraction_method: ContextExtractionMethod = "manual"

    def __post_init__(self):
        """Valider les champs obligatoires."""
        if not self.situation or len(self.situation.strip()) < 5:
            raise ValueError("situation must be at least 5 characters")
        if not self.solution or len(self.solution.strip()) < 5:
            raise ValueError("solution must be at least 5 characters")
        if not self.trigger_keywords or len(self.trigger_keywords) < 1:
            raise ValueError("at least 1 trigger keyword required")
        # Nettoyer les keywords
        self.trigger_keywords = [k.strip().lower() for k in self.trigger_keywords if k.strip()]
        if not self.trigger_keywords:
            raise ValueError("at least 1 non-empty trigger keyword required")

    def to_dict(self) -> dict:
        """Convertir en dictionnaire pour sérialisation."""
        return {
            "situation": self.situation,
            "solution": self.solution,
            "trigger_keywords": self.trigger_keywords,
            "what_failed": self.what_failed,
            "conversation_excerpt": self.conversation_excerpt,
            "files_modified": self.files_modified,
            "error_messages": self.error_messages,
            "created_at": self.created_at.isoformat(),
            "extraction_method": self.extraction_method,
        }

    def to_json(self) -> str:
        """Sérialiser en JSON."""
        import json

        return json.dumps(self.to_dict())

    @classmethod
    def from_dict(cls, data: dict) -> "StructuredContext":
        """Créer depuis un dictionnaire."""
        return cls(
            situation=data["situation"],
            solution=data["solution"],
            trigger_keywords=data["trigger_keywords"],
            what_failed=data.get("what_failed"),
            conversation_excerpt=data.get("conversation_excerpt"),
            files_modified=data.get("files_modified"),
            error_messages=data.get("error_messages"),
            created_at=(
                datetime.fromisoformat(data["created_at"])
                if data.get("created_at")
                else datetime.now()
            ),
            extraction_method=data.get("extraction_method", "manual"),
        )

    @classmethod
    def from_json(cls, data: str | dict) -> "StructuredContext":
        """Désérialiser depuis JSON."""
        import json

        if isinstance(data, str):
            data = json.loads(data)
        return cls.from_dict(data)
