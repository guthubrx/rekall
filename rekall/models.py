"""Rekall data models."""

from __future__ import annotations

import math
import secrets
import time
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import TYPE_CHECKING, Literal

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
    project: str | None = None
    tags: list[str] = field(default_factory=list)
    confidence: int = 2
    status: EntryStatus = "active"
    superseded_by: str | None = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    # Cognitive memory fields
    memory_type: MemoryType = "episodic"
    last_accessed: datetime | None = None
    access_count: int = 0
    consolidation_score: float = 0.0
    next_review: date | None = None
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
    reason: str | None = None  # Justification for the link (helps AI understand intent)

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

    def to_numpy(self) -> np.ndarray:
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
        array: np.ndarray,
        model_name: str,
    ) -> Embedding:
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
    resolved_at: datetime | None = None

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
    def from_row(cls, row: dict) -> Suggestion:
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

# Source types for v8 (Feature 009 - Sources Integration)
SourceType = Literal["theme", "url", "file"]
SourceReliability = Literal["A", "B", "C"]
SourceDecayRate = Literal["fast", "medium", "slow"]
SourceStatus = Literal["active", "inaccessible", "archived"]

VALID_SOURCE_TYPES = ("theme", "url", "file")
VALID_SOURCE_RELIABILITY = ("A", "B", "C")
VALID_SOURCE_DECAY_RATES = ("fast", "medium", "slow")
VALID_SOURCE_STATUSES = ("active", "inaccessible", "archived")

# Decay rate half-lives in days
DECAY_RATE_HALF_LIVES = {
    "fast": 90,    # 3 months
    "medium": 180,  # 6 months
    "slow": 365,   # 12 months
}

# Source role types for v9 (Feature 010 - Sources Autonomes)
SourceRole = Literal["hub", "authority", "unclassified"]
PromotionStatus = Literal["seed", "promoted", "normal"]

VALID_SOURCE_ROLES = ("hub", "authority", "unclassified")
VALID_PROMOTION_STATUSES = ("seed", "promoted", "normal")

# Promotion thresholds for automatic source promotion (Feature 010)
PROMOTION_THRESHOLDS = {
    "min_usage_count": 3,      # Minimum citations to qualify
    "min_score": 30.0,         # Minimum personal score
    "max_days_inactive": 180,  # Maximum days since last use
}

# Role bonus multipliers for scoring (Feature 010)
ROLE_BONUS = {
    "authority": 1.2,   # Official docs get 20% bonus
    "hub": 1.0,         # Aggregators get no bonus
    "unclassified": 1.0,  # Default no bonus
}

# Seed bonus for migrated sources (Feature 010)
SEED_BONUS = 1.2  # 20% bonus for seed sources

# AI Enrichment types for v12 (Feature 021/023 - AI Source Enrichment)
EnrichmentStatus = Literal["none", "proposed", "validated"]
SourceAIType = Literal["documentation", "blog", "research", "tool", "reference", "tutorial"]
ValidatedBy = Literal["auto", "human"]

VALID_ENRICHMENT_STATUSES = ("none", "proposed", "validated")
VALID_SOURCE_AI_TYPES = ("documentation", "blog", "research", "tool", "reference", "tutorial")
VALID_VALIDATED_BY = ("auto", "human")


@dataclass
class Source:
    """A curated documentary source with adaptive scoring.

    Sources track usage patterns and calculate a personal score
    based on frequency, recency, and reliability.

    Feature 010 adds:
    - is_seed: True if migrated from speckit research files
    - is_promoted: True if automatically promoted based on usage
    - role: hub/authority/unclassified (HITS-inspired classification)
    - citation_quality_factor: PR-Index inspired quality score

    Feature 021/023 adds AI enrichment fields:
    - ai_type: Classification of the source (documentation, blog, etc.)
    - ai_tags: AI-suggested tags for categorization
    - ai_summary: AI-generated summary (max 500 chars)
    - ai_confidence: Confidence score for the enrichment (0.0-1.0)
    - enrichment_status: Workflow status (none, proposed, validated)
    """

    id: str = ""
    domain: str = ""  # Normalized domain (e.g., "pinecone.io")
    url_pattern: str | None = None  # URL pattern (e.g., "https://pinecone.io/*")
    usage_count: int = 0
    last_used: datetime | None = None
    personal_score: float = 50.0  # Score 0-100
    reliability: SourceReliability = "B"  # A/B/C (Admiralty simplified)
    decay_rate: SourceDecayRate = "medium"  # fast/medium/slow
    last_verified: datetime | None = None  # Link rot check
    status: SourceStatus = "active"  # active/inaccessible/archived
    created_at: datetime = field(default_factory=datetime.now)
    # Feature 010 - Sources Autonomes fields
    is_seed: bool = False  # Migrated from speckit research files
    is_promoted: bool = False  # Automatically promoted based on usage
    promoted_at: datetime | None = None  # Timestamp of promotion
    role: SourceRole = "unclassified"  # hub/authority/unclassified
    seed_origin: str | None = None  # Path to speckit file (if seed)
    citation_quality_factor: float = 0.0  # PR-Index inspired quality (0.0-1.0)
    # Feature 021/023 - AI Source Enrichment fields
    ai_type: SourceAIType | None = None  # documentation, blog, research, tool, reference, tutorial
    ai_tags: list[str] | None = None  # AI-suggested tags
    ai_summary: str | None = None  # AI-generated summary (max 500 chars)
    ai_confidence: float | None = None  # Confidence score 0.0-1.0
    enrichment_status: EnrichmentStatus = "none"  # none, proposed, validated
    enrichment_validated_at: datetime | None = None  # Timestamp of validation
    enrichment_validated_by: ValidatedBy | None = None  # 'auto' or 'human'

    def __post_init__(self):
        """Validate source fields after initialization."""
        if self.id and not isinstance(self.id, str):
            raise ValueError("id must be a string")
        if self.reliability not in VALID_SOURCE_RELIABILITY:
            raise ValueError(
                f"invalid reliability: {self.reliability}. "
                f"Valid: {', '.join(VALID_SOURCE_RELIABILITY)}"
            )
        if self.decay_rate not in VALID_SOURCE_DECAY_RATES:
            raise ValueError(
                f"invalid decay_rate: {self.decay_rate}. "
                f"Valid: {', '.join(VALID_SOURCE_DECAY_RATES)}"
            )
        if self.status not in VALID_SOURCE_STATUSES:
            raise ValueError(
                f"invalid status: {self.status}. "
                f"Valid: {', '.join(VALID_SOURCE_STATUSES)}"
            )
        if not 0 <= self.personal_score <= 100:
            raise ValueError(f"personal_score must be 0-100, got: {self.personal_score}")
        # Feature 010 validations
        if self.role not in VALID_SOURCE_ROLES:
            raise ValueError(
                f"invalid role: {self.role}. "
                f"Valid: {', '.join(VALID_SOURCE_ROLES)}"
            )
        if not 0.0 <= self.citation_quality_factor <= 1.0:
            raise ValueError(
                f"citation_quality_factor must be 0.0-1.0, got: {self.citation_quality_factor}"
            )
        # Feature 021/023 validations - AI enrichment fields
        if self.ai_type is not None and self.ai_type not in VALID_SOURCE_AI_TYPES:
            raise ValueError(
                f"invalid ai_type: {self.ai_type}. "
                f"Valid: {', '.join(VALID_SOURCE_AI_TYPES)}"
            )
        if self.ai_confidence is not None and not 0.0 <= self.ai_confidence <= 1.0:
            raise ValueError(
                f"ai_confidence must be 0.0-1.0, got: {self.ai_confidence}"
            )
        if self.enrichment_status not in VALID_ENRICHMENT_STATUSES:
            raise ValueError(
                f"invalid enrichment_status: {self.enrichment_status}. "
                f"Valid: {', '.join(VALID_ENRICHMENT_STATUSES)}"
            )
        if self.enrichment_validated_by is not None and self.enrichment_validated_by not in VALID_VALIDATED_BY:
            raise ValueError(
                f"invalid enrichment_validated_by: {self.enrichment_validated_by}. "
                f"Valid: {', '.join(VALID_VALIDATED_BY)}"
            )


@dataclass
class EntrySource:
    """A link between an entry (souvenir) and a source.

    Tracks which sources were used to create or inform an entry,
    enabling bidirectional backlinks and usage tracking.
    """

    id: str = ""
    entry_id: str = ""
    source_id: str | None = None  # NULL if URL not curated
    source_type: SourceType = "url"  # theme/url/file
    source_ref: str = ""  # Actual reference (theme name, URL, file path)
    note: str | None = None  # Contextual note (e.g., "Section on chunking")
    created_at: datetime = field(default_factory=datetime.now)

    # Joined data (not persisted)
    source: Source | None = None

    def __post_init__(self):
        """Validate entry_source fields after initialization."""
        if self.source_type not in VALID_SOURCE_TYPES:
            raise ValueError(
                f"invalid source_type: {self.source_type}. "
                f"Valid: {', '.join(VALID_SOURCE_TYPES)}"
            )


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
    what_failed: str | None = None  # Ce qui n'a pas marché
    conversation_excerpt: str | None = None  # Extrait conversation
    files_modified: list[str] | None = None  # Fichiers touchés
    error_messages: list[str] | None = None  # Erreurs rencontrées

    # Feature 018: Temporal markers (auto-generated or manual override)
    time_of_day: str | None = None  # morning, afternoon, evening, night
    day_of_week: str | None = None  # monday, tuesday, ...

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
            "time_of_day": self.time_of_day,
            "day_of_week": self.day_of_week,
            "created_at": self.created_at.isoformat(),
            "extraction_method": self.extraction_method,
        }

    def to_json(self) -> str:
        """Sérialiser en JSON."""
        import json

        return json.dumps(self.to_dict())

    @classmethod
    def from_dict(cls, data: dict) -> StructuredContext:
        """Créer depuis un dictionnaire."""
        return cls(
            situation=data["situation"],
            solution=data["solution"],
            trigger_keywords=data["trigger_keywords"],
            what_failed=data.get("what_failed"),
            conversation_excerpt=data.get("conversation_excerpt"),
            files_modified=data.get("files_modified"),
            error_messages=data.get("error_messages"),
            time_of_day=data.get("time_of_day"),
            day_of_week=data.get("day_of_week"),
            created_at=(
                datetime.fromisoformat(data["created_at"])
                if data.get("created_at")
                else datetime.now()
            ),
            extraction_method=data.get("extraction_method", "manual"),
        )

    @classmethod
    def from_json(cls, data: str | dict) -> StructuredContext:
        """Désérialiser depuis JSON."""
        import json

        if isinstance(data, str):
            data = json.loads(data)
        return cls.from_dict(data)


# =============================================================================
# Saved Filters (Feature 012 - Sources Organisation)
# =============================================================================


@dataclass
class SavedFilter:
    """Filtre sauvegardé pour réutiliser des combinaisons de critères.

    Permet de sauvegarder et réappliquer des filtres multi-critères
    sur les sources documentaires.
    """

    id: int | None = None
    name: str = ""
    filter_json: str = "{}"
    created_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        """Valider les champs."""
        if self.name and not self.name.strip():
            raise ValueError("name cannot be empty if provided")

    def get_filters(self) -> dict:
        """Désérialiser les filtres depuis JSON."""
        import json

        return json.loads(self.filter_json)

    @classmethod
    def from_dict(cls, data: dict) -> "SavedFilter":
        """Créer depuis un dictionnaire."""
        return cls(
            id=data.get("id"),
            name=data["name"],
            filter_json=data["filter_json"],
            created_at=(
                datetime.fromisoformat(data["created_at"])
                if data.get("created_at")
                else datetime.now()
            ),
        )


# =============================================================================
# Validation Functions for Sources (Feature 009)
# =============================================================================


def validate_source(source: Source) -> list[str]:
    """Validate a Source object and return list of errors.

    Args:
        source: Source object to validate

    Returns:
        List of error messages (empty if valid)
    """
    errors = []

    if not source.domain:
        errors.append("domain is required")

    if source.reliability not in VALID_SOURCE_RELIABILITY:
        errors.append(
            f"reliability must be one of {VALID_SOURCE_RELIABILITY}, "
            f"got {source.reliability}"
        )

    if source.decay_rate not in VALID_SOURCE_DECAY_RATES:
        errors.append(
            f"decay_rate must be one of {VALID_SOURCE_DECAY_RATES}, "
            f"got {source.decay_rate}"
        )

    if source.status not in VALID_SOURCE_STATUSES:
        errors.append(
            f"status must be one of {VALID_SOURCE_STATUSES}, "
            f"got {source.status}"
        )

    if not 0 <= source.personal_score <= 100:
        errors.append(f"personal_score must be 0-100, got {source.personal_score}")

    if source.usage_count < 0:
        errors.append(f"usage_count cannot be negative, got {source.usage_count}")

    return errors


def validate_entry_source(entry_source: EntrySource) -> list[str]:
    """Validate an EntrySource object and return list of errors.

    Args:
        entry_source: EntrySource object to validate

    Returns:
        List of error messages (empty if valid)
    """
    errors = []

    if not entry_source.entry_id:
        errors.append("entry_id is required")

    if entry_source.source_type not in VALID_SOURCE_TYPES:
        errors.append(
            f"source_type must be one of {VALID_SOURCE_TYPES}, "
            f"got {entry_source.source_type}"
        )

    if not entry_source.source_ref:
        errors.append("source_ref is required")

    # Type-specific validation
    if entry_source.source_type == "theme":
        # Theme should reference a .md file
        if not entry_source.source_ref.endswith(".md"):
            errors.append("theme source_ref should be a .md filename")
    elif entry_source.source_type == "url":
        # URL should start with http:// or https://
        if not entry_source.source_ref.startswith(("http://", "https://")):
            errors.append("url source_ref must start with http:// or https://")
    # file type: no specific validation (local paths vary)

    return errors


# =============================================================================
# Sources Medallion (Feature 013)
# =============================================================================

# Content types for URL classification
ContentType = Literal["documentation", "repository", "forum", "blog", "api", "paper", "other"]
VALID_CONTENT_TYPES = ("documentation", "repository", "forum", "blog", "api", "paper", "other")

# Import source types
ImportSource = Literal["realtime", "history_import"]
VALID_IMPORT_SOURCES = ("realtime", "history_import")


@dataclass
class InboxEntry:
    """URL capturée depuis un CLI IA (Bronze layer).

    Représente une URL brute avec tout le contexte de capture.
    """

    id: str
    url: str
    domain: str | None = None
    cli_source: str = ""
    project: str | None = None
    conversation_id: str | None = None
    user_query: str | None = None
    assistant_snippet: str | None = None
    surrounding_text: str | None = None
    captured_at: datetime = field(default_factory=datetime.now)
    import_source: str = "history_import"
    raw_json: str | None = None
    is_valid: bool = True
    validation_error: str | None = None
    enriched_at: datetime | None = None

    def __post_init__(self):
        """Valider les champs requis."""
        if not self.url:
            raise ValueError("url is required")
        if not self.cli_source:
            raise ValueError("cli_source is required")


@dataclass
class StagingEntry:
    """URL enrichie avec métadonnées (Silver layer).

    Représente une URL dédupliquée et enrichie, prête pour promotion.
    """

    id: str
    url: str
    domain: str
    title: str | None = None
    description: str | None = None
    content_type: str | None = None
    language: str | None = None
    last_verified: datetime | None = None
    is_accessible: bool = True
    http_status: int | None = None
    citation_count: int = 1
    project_count: int = 1
    projects_list: str | None = None  # JSON array
    first_seen: datetime | None = None
    last_seen: datetime | None = None
    promotion_score: float = 0.0
    inbox_ids: str | None = None  # JSON array
    enriched_at: datetime | None = None
    promoted_at: datetime | None = None
    promoted_to: str | None = None

    def __post_init__(self):
        """Valider les champs requis."""
        if not self.url:
            raise ValueError("url is required")
        if not self.domain:
            raise ValueError("domain is required")
        if self.content_type and self.content_type not in VALID_CONTENT_TYPES:
            raise ValueError(
                f"content_type must be one of {VALID_CONTENT_TYPES}, got {self.content_type}"
            )


@dataclass
class ConnectorImport:
    """Tracking des imports par connecteur pour CDC.

    Permet l'import incrémental (Change Data Capture).
    """

    connector: str
    last_import: datetime | None = None
    last_file_marker: str | None = None
    entries_imported: int = 0
    errors_count: int = 0

    def __post_init__(self):
        """Valider les champs requis."""
        if not self.connector:
            raise ValueError("connector is required")
