"""Embedding service for semantic similarity in Rekall.

This module handles:
- Loading and managing the embedding model (sentence-transformers)
- Calculating embeddings for entries (summary and context)
- Finding similar entries via cosine similarity
- Graceful degradation when embeddings are not configured

The embedding model is loaded lazily on first use to avoid startup overhead.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    import numpy as np

    from rekall.db import Database
    from rekall.models import Entry

logger = logging.getLogger(__name__)

# Maximum context length before truncation (model limit ~2K tokens ≈ 8K chars)
MAX_CONTEXT_CHARS = 8000

# Valid Matryoshka dimensions
VALID_DIMENSIONS = (128, 384, 768)


class EmbeddingModelNotAvailable(Exception):
    """Raised when the embedding model cannot be loaded."""

    pass


class EmbeddingService:
    """Service for managing embeddings and semantic similarity.

    Implements lazy loading of the embedding model and graceful degradation
    when the model is not available.
    """

    def __init__(
        self,
        model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
        dimensions: int = 384,
        similarity_threshold: float = 0.75,
    ):
        """Initialize the embedding service.

        Args:
            model_name: Name of the sentence-transformers model to use
            dimensions: Embedding dimensions (128, 384, or 768 for Matryoshka)
            similarity_threshold: Minimum cosine similarity for suggestions
        """
        self.model_name = model_name
        self.dimensions = dimensions
        self.similarity_threshold = similarity_threshold
        self._model = None
        self._available: Optional[bool] = None
        self._model_dimensions: Optional[int] = None

    @property
    def available(self) -> bool:
        """Check if embeddings are available (dependencies installed)."""
        if self._available is None:
            self._available = self._check_availability()
        return self._available

    def _check_availability(self) -> bool:
        """Check if required dependencies are available.

        Returns:
            True if sentence-transformers and numpy are available
        """
        try:
            import numpy  # noqa: F401
            import sentence_transformers  # noqa: F401

            return True
        except ImportError:
            return False

    def _load_model(self) -> None:
        """Load the embedding model lazily.

        Raises:
            EmbeddingModelNotAvailable: If dependencies are not available
        """
        if self._model is not None:
            return

        if not self.available:
            raise EmbeddingModelNotAvailable(
                "Embedding dependencies not available. "
                "Install with: pip install sentence-transformers numpy"
            )

        try:
            from sentence_transformers import SentenceTransformer

            logger.info(f"Loading embedding model: {self.model_name}")
            self._model = SentenceTransformer(self.model_name)
            self._model_dimensions = self._model.get_sentence_embedding_dimension()
            logger.info(
                f"Model loaded. Native dimensions: {self._model_dimensions}, "
                f"using: {self.dimensions}"
            )
        except Exception as e:
            raise EmbeddingModelNotAvailable(
                f"Failed to load embedding model '{self.model_name}': {e}"
            ) from e

    def get_model_status(self) -> dict:
        """Get status information about the embedding model.

        Returns:
            Dict with availability, model name, dimensions, etc.
        """
        status = {
            "available": self.available,
            "model_name": self.model_name,
            "target_dimensions": self.dimensions,
            "model_loaded": self._model is not None,
            "native_dimensions": self._model_dimensions,
        }

        if not self.available:
            status["install_instructions"] = (
                "pip install sentence-transformers numpy"
            )

        return status

    def _truncate_text(self, text: str, max_chars: int = MAX_CONTEXT_CHARS) -> str:
        """Truncate text to maximum length.

        Args:
            text: Text to truncate
            max_chars: Maximum characters

        Returns:
            Truncated text
        """
        if len(text) <= max_chars:
            return text

        logger.info(
            f"Truncating text from {len(text)} to {max_chars} characters"
        )
        return text[:max_chars]

    def _apply_matryoshka(self, vector: "np.ndarray") -> "np.ndarray":
        """Apply Matryoshka dimension reduction and re-normalize.

        Args:
            vector: Full embedding vector

        Returns:
            Truncated and normalized vector
        """
        import numpy as np

        if len(vector) <= self.dimensions:
            return vector

        # Truncate to target dimensions
        truncated = vector[: self.dimensions]

        # Re-normalize after truncation
        norm = np.linalg.norm(truncated)
        if norm > 0:
            truncated = truncated / norm

        return truncated

    def calculate(self, text: str) -> Optional["np.ndarray"]:
        """Calculate embedding vector for text.

        Args:
            text: Text to embed

        Returns:
            numpy array of shape (dimensions,), or None if unavailable

        Note:
            Returns None instead of raising if model not available,
            for graceful degradation.
        """
        if not text or not text.strip():
            return None

        try:
            self._load_model()
        except EmbeddingModelNotAvailable as e:
            logger.warning(f"Embedding not available: {e}")
            return None

        import numpy as np

        # Truncate long text
        text = self._truncate_text(text)

        # Calculate embedding
        vector = self._model.encode(text, convert_to_numpy=True)

        # Ensure float32
        vector = vector.astype(np.float32)

        # Apply Matryoshka dimension reduction if needed
        vector = self._apply_matryoshka(vector)

        # Normalize
        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = vector / norm

        return vector

    def calculate_for_entry(
        self,
        entry: "Entry",
        context: Optional[str] = None,
    ) -> dict[str, Optional["np.ndarray"]]:
        """Calculate embeddings for an entry (summary and optional context).

        Args:
            entry: Entry to calculate embeddings for
            context: Optional conversation context

        Returns:
            Dict with "summary" and "context" vectors (context may be None)
        """
        # Build summary text: title + content + tags
        summary_parts = [entry.title]
        if entry.content:
            summary_parts.append(entry.content)
        if entry.tags:
            summary_parts.append(" ".join(entry.tags))

        summary_text = " ".join(summary_parts)
        summary_vec = self.calculate(summary_text)

        # Calculate context embedding if provided
        context_vec = None
        if context:
            context_vec = self.calculate(context)

        return {
            "summary": summary_vec,
            "context": context_vec,
        }

    def find_similar(
        self,
        entry_id: str,
        db: "Database",
        threshold: Optional[float] = None,
        limit: int = 10,
    ) -> list[tuple["Entry", float]]:
        """Find entries similar to the given entry.

        Args:
            entry_id: ID of the entry to find similar entries for
            db: Database instance
            threshold: Minimum similarity score (default: self.similarity_threshold)
            limit: Maximum number of results

        Returns:
            List of (Entry, similarity_score) tuples, sorted by score descending
        """
        if threshold is None:
            threshold = self.similarity_threshold

        # Get the target entry's embedding
        target_emb = db.get_embedding(entry_id, "summary")
        if target_emb is None:
            logger.warning(f"No embedding found for entry {entry_id}")
            return []

        target_vec = target_emb.to_numpy()

        # Get all summary embeddings
        all_embeddings = db.get_all_embeddings("summary")

        # Calculate similarities
        results: list[tuple[str, float]] = []
        for emb in all_embeddings:
            # Skip the target entry itself
            if emb.entry_id == entry_id:
                continue

            other_vec = emb.to_numpy()
            score = cosine_similarity(target_vec, other_vec)

            if score >= threshold:
                results.append((emb.entry_id, score))

        # Sort by score descending
        results.sort(key=lambda x: x[1], reverse=True)

        # Limit results
        results = results[:limit]

        # Fetch full entries
        similar_entries: list[tuple["Entry", float]] = []
        for eid, score in results:
            entry = db.get(eid, update_access=False)
            if entry:
                similar_entries.append((entry, score))

        return similar_entries

    def semantic_search(
        self,
        query: str,
        db: "Database",
        context: Optional[str] = None,
        threshold: float = 0.0,
        limit: int = 20,
    ) -> list[tuple["Entry", float]]:
        """Search entries by semantic similarity to query.

        Args:
            query: Search query text
            db: Database instance
            context: Optional conversation context for better matching
            threshold: Minimum similarity score
            limit: Maximum number of results

        Returns:
            List of (Entry, similarity_score) tuples, sorted by score descending
        """
        # Calculate query embedding
        search_text = query
        if context:
            search_text = f"{context}\n\n{query}"

        query_vec = self.calculate(search_text)
        if query_vec is None:
            logger.warning("Could not calculate query embedding")
            return []

        # Get all summary embeddings
        all_embeddings = db.get_all_embeddings("summary")

        # Calculate similarities
        results: list[tuple[str, float]] = []
        for emb in all_embeddings:
            other_vec = emb.to_numpy()
            score = cosine_similarity(query_vec, other_vec)

            if score >= threshold:
                results.append((emb.entry_id, score))

        # Sort by score descending
        results.sort(key=lambda x: x[1], reverse=True)

        # Limit results
        results = results[:limit]

        # Fetch full entries
        similar_entries: list[tuple["Entry", float]] = []
        for eid, score in results:
            entry = db.get(eid, update_access=False)
            if entry:
                similar_entries.append((entry, score))

        return similar_entries

    def hybrid_search(
        self,
        query: str,
        db: "Database",
        context: Optional[str] = None,
        limit: int = 20,
        fts_weight: float = 0.5,
        semantic_weight: float = 0.3,
        keyword_weight: float = 0.2,
        entry_type: Optional[str] = None,
        project: Optional[str] = None,
        memory_type: Optional[str] = None,
    ) -> list[tuple["Entry", float, Optional[float], list[str]]]:
        """Hybrid search combining FTS, semantic similarity, and keyword matching.

        Uses three scoring components:
        1. FTS (Full-Text Search) - traditional text matching
        2. Semantic - embedding cosine similarity
        3. Keywords - structured context trigger_keywords matching

        Args:
            query: Search query text
            db: Database instance
            context: Optional conversation context
            limit: Maximum number of results
            fts_weight: Weight for FTS score (default 0.5)
            semantic_weight: Weight for semantic score (default 0.3)
            keyword_weight: Weight for keyword score (default 0.2)
            entry_type: Filter by type
            project: Filter by project
            memory_type: Filter by memory type

        Returns:
            List of (Entry, combined_score, semantic_score, matched_keywords) tuples
        """
        from rekall.context_extractor import (
            calculate_keyword_score,
            extract_keywords,
            get_matching_keywords,
        )

        # Extract keywords from query for matching
        query_keywords = extract_keywords(query, context or "", max_keywords=10)

        # Get FTS results
        fts_results = db.search(
            query,
            entry_type=entry_type,
            project=project,
            memory_type=memory_type,
            limit=limit * 2,  # Get more for merging
        )

        # Normalize FTS scores (rank to 0-1 score)
        fts_scores: dict[str, float] = {}
        for result in fts_results:
            # BM25 rank: lower = better, normalize to 0-1
            normalized = 1.0 / (1.0 + (result.rank or 0))
            fts_scores[result.entry.id] = normalized

        # Get semantic results if available
        semantic_scores: dict[str, float] = {}
        if self.available:
            semantic_results = self.semantic_search(
                query, db, context=context, limit=limit * 2
            )
            for entry, score in semantic_results:
                semantic_scores[entry.id] = score

        # Get keyword scores from structured context
        keyword_scores: dict[str, float] = {}
        matched_keywords_map: dict[str, list[str]] = {}

        # Get all entries with structured context
        entries_with_context = db.get_entries_with_structured_context(limit=500)
        for entry, structured_ctx in entries_with_context:
            if structured_ctx and structured_ctx.trigger_keywords:
                kw_score = calculate_keyword_score(
                    query_keywords, structured_ctx.trigger_keywords
                )
                if kw_score > 0:
                    keyword_scores[entry.id] = kw_score
                    matched_keywords_map[entry.id] = get_matching_keywords(
                        query_keywords, structured_ctx.trigger_keywords
                    )

        # Combine scores from all sources
        all_entry_ids = (
            set(fts_scores.keys())
            | set(semantic_scores.keys())
            | set(keyword_scores.keys())
        )
        combined: list[tuple[str, float, Optional[float], list[str]]] = []

        for entry_id in all_entry_ids:
            fts_score = fts_scores.get(entry_id, 0.0)
            sem_score = semantic_scores.get(entry_id)
            kw_score = keyword_scores.get(entry_id, 0.0)
            matched_kws = matched_keywords_map.get(entry_id, [])

            # Calculate combined score
            if sem_score is not None:
                final_score = (
                    fts_weight * fts_score
                    + semantic_weight * sem_score
                    + keyword_weight * kw_score
                )
            else:
                # No semantic score - redistribute weight to FTS and keywords
                adjusted_fts = fts_weight + semantic_weight * 0.6
                adjusted_kw = keyword_weight + semantic_weight * 0.4
                final_score = adjusted_fts * fts_score + adjusted_kw * kw_score

            combined.append((entry_id, final_score, sem_score, matched_kws))

        # Sort by combined score descending
        combined.sort(key=lambda x: x[1], reverse=True)

        # Limit and fetch entries
        results: list[tuple["Entry", float, Optional[float], list[str]]] = []
        for entry_id, final_score, sem_score, matched_kws in combined[:limit]:
            # Check filters if entry came from semantic only
            entry = db.get(entry_id, update_access=False)
            if entry:
                # Apply filters for semantic-only results
                if entry_id not in fts_scores:
                    if entry_type and entry.type != entry_type:
                        continue
                    if project and entry.project != project:
                        continue
                    if memory_type and entry.memory_type != memory_type:
                        continue
                results.append((entry, final_score, sem_score, matched_kws))

        return results

    def find_generalization_candidates(
        self,
        db: "Database",
        min_cluster_size: int = 3,
        similarity_threshold: float = 0.80,
    ) -> list[list["Entry"]]:
        """Find clusters of similar episodic entries for potential generalization.

        Args:
            db: Database instance
            min_cluster_size: Minimum entries needed to form a cluster
            similarity_threshold: Minimum similarity for clustering

        Returns:
            List of clusters (each cluster is a list of Entry objects)
        """
        # Get all episodic entries with embeddings
        all_embeddings = db.get_all_embeddings("summary")

        # Filter to episodic entries only
        episodic_embeddings = []
        for emb in all_embeddings:
            entry = db.get(emb.entry_id, update_access=False)
            if entry and entry.memory_type == "episodic":
                episodic_embeddings.append((entry, emb.to_numpy()))

        if len(episodic_embeddings) < min_cluster_size:
            return []

        # Greedy clustering
        clusters: list[list["Entry"]] = []
        used_ids: set[str] = set()

        for i, (entry_i, vec_i) in enumerate(episodic_embeddings):
            if entry_i.id in used_ids:
                continue

            # Find similar entries
            cluster = [entry_i]
            for j, (entry_j, vec_j) in enumerate(episodic_embeddings):
                if i == j or entry_j.id in used_ids:
                    continue

                score = cosine_similarity(vec_i, vec_j)
                if score >= similarity_threshold:
                    cluster.append(entry_j)

            # Only keep clusters with enough entries
            if len(cluster) >= min_cluster_size:
                clusters.append(cluster)
                for entry in cluster:
                    used_ids.add(entry.id)

        return clusters


def cosine_similarity(vec1: "np.ndarray", vec2: "np.ndarray") -> float:
    """Calculate cosine similarity between two vectors.

    Args:
        vec1: First vector
        vec2: Second vector

    Returns:
        Cosine similarity score between -1.0 and 1.0
    """
    import numpy as np

    dot = np.dot(vec1, vec2)
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return float(dot / (norm1 * norm2))


# Singleton instance for convenience
_embedding_service: Optional[EmbeddingService] = None


def get_embedding_service(
    model_name: Optional[str] = None,
    dimensions: Optional[int] = None,
    similarity_threshold: Optional[float] = None,
) -> EmbeddingService:
    """Get the global embedding service instance.

    Args:
        model_name: Override default model name
        dimensions: Override default dimensions
        similarity_threshold: Override default threshold

    Returns:
        EmbeddingService singleton (or new instance if params differ)
    """
    global _embedding_service

    # Create new instance if params specified or none exists
    if _embedding_service is None or any([model_name, dimensions, similarity_threshold]):
        kwargs = {}
        if model_name:
            kwargs["model_name"] = model_name
        if dimensions:
            kwargs["dimensions"] = dimensions
        if similarity_threshold:
            kwargs["similarity_threshold"] = similarity_threshold

        _embedding_service = EmbeddingService(**kwargs)

    return _embedding_service


def reset_embedding_service() -> None:
    """Reset the global embedding service (for testing)."""
    global _embedding_service
    _embedding_service = None
