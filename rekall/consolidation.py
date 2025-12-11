"""Consolidation utilities for Rekall.

Provides functions to analyze clusters of similar entries and extract
common patterns for knowledge consolidation.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from rekall.db import Database
    from rekall.models import Entry, StructuredContext


@dataclass
class ClusterAnalysis:
    """Analysis of a cluster of similar entries."""

    entries: list[Entry]
    common_keywords: list[str]
    keyword_frequency: dict[str, int]
    suggested_title: str
    suggested_keywords: list[str]
    consolidation_score: float


def analyze_cluster(
    entries: list[Entry],
    db: Database,
) -> ClusterAnalysis:
    """Analyze a cluster of similar entries for consolidation patterns.

    Extracts common keywords from structured contexts and suggests
    a consolidated entry.

    Args:
        entries: List of similar entries
        db: Database instance

    Returns:
        ClusterAnalysis with common patterns and suggestions
    """
    # Collect all keywords from structured contexts
    all_keywords: list[str] = []
    contexts: list[tuple[Entry, StructuredContext]] = []

    for entry in entries:
        ctx = db.get_structured_context(entry.id)
        if ctx and ctx.trigger_keywords:
            all_keywords.extend(ctx.trigger_keywords)
            contexts.append((entry, ctx))

    # Count keyword frequency
    keyword_freq = Counter(all_keywords)

    # Common keywords appear in at least 50% of entries
    min_freq = max(2, len(entries) // 2)
    common_keywords = [kw for kw, freq in keyword_freq.items() if freq >= min_freq]

    # Sort by frequency
    common_keywords.sort(key=lambda k: keyword_freq[k], reverse=True)

    # Generate suggested title from most common keywords
    suggested_title = _generate_title(common_keywords, entries)

    # Suggested keywords: top 5 most frequent
    suggested_keywords = common_keywords[:5] if common_keywords else []

    # Calculate consolidation score
    score = _calculate_consolidation_score(
        entries, contexts, common_keywords, keyword_freq
    )

    return ClusterAnalysis(
        entries=entries,
        common_keywords=common_keywords,
        keyword_frequency=dict(keyword_freq),
        suggested_title=suggested_title,
        suggested_keywords=suggested_keywords,
        consolidation_score=score,
    )


def _generate_title(keywords: list[str], entries: list[Entry]) -> str:
    """Generate a suggested title for consolidated entry.

    Args:
        keywords: Common keywords
        entries: Cluster entries

    Returns:
        Suggested title string
    """
    if keywords:
        # Use top 2-3 keywords
        key_terms = " ".join(keywords[:3])
        return f"Pattern: {key_terms}"

    # Fallback: extract common words from titles
    title_words = []
    for entry in entries:
        title_words.extend(entry.title.lower().split())

    word_freq = Counter(title_words)
    common_words = [w for w, _ in word_freq.most_common(3)]

    if common_words:
        return f"Pattern: {' '.join(common_words)}"

    return "Consolidated pattern"


def _calculate_consolidation_score(
    entries: list[Entry],
    contexts: list[tuple[Entry, StructuredContext]],
    common_keywords: list[str],
    keyword_freq: dict[str, int],
) -> float:
    """Calculate a score indicating how well the cluster can be consolidated.

    Higher scores indicate better consolidation potential.

    Args:
        entries: All entries in cluster
        contexts: Entries with structured context
        common_keywords: Keywords common across entries
        keyword_freq: Keyword frequency counts

    Returns:
        Score between 0.0 and 1.0
    """
    if not entries:
        return 0.0

    # Factor 1: Context coverage (how many entries have structured context)
    context_coverage = len(contexts) / len(entries)

    # Factor 2: Keyword overlap (how consistent are the keywords)
    if keyword_freq:
        avg_freq = sum(keyword_freq.values()) / len(keyword_freq)
        max_possible = len(entries)
        keyword_overlap = avg_freq / max_possible
    else:
        keyword_overlap = 0.0

    # Factor 3: Common keyword quality (enough common keywords)
    keyword_quality = min(1.0, len(common_keywords) / 3)

    # Weighted combination
    score = (
        0.4 * context_coverage
        + 0.4 * keyword_overlap
        + 0.2 * keyword_quality
    )

    return min(1.0, score)


def find_consolidation_opportunities(
    db: Database,
    min_cluster_size: int = 2,
    min_score: float = 0.5,
) -> list[ClusterAnalysis]:
    """Find opportunities to consolidate similar entries.

    Uses keyword overlap to find entries that share common patterns,
    even without embeddings.

    Args:
        db: Database instance
        min_cluster_size: Minimum entries for a cluster
        min_score: Minimum consolidation score

    Returns:
        List of cluster analyses, sorted by score descending
    """
    # Get all entries with structured context
    entries_with_ctx = db.get_entries_with_structured_context(limit=500)

    if len(entries_with_ctx) < min_cluster_size:
        return []

    # Build keyword -> entries index
    keyword_index: dict[str, list[tuple[Entry, StructuredContext]]] = {}
    for entry, ctx in entries_with_ctx:
        if ctx and ctx.trigger_keywords:
            for kw in ctx.trigger_keywords:
                kw_lower = kw.lower()
                if kw_lower not in keyword_index:
                    keyword_index[kw_lower] = []
                keyword_index[kw_lower].append((entry, ctx))

    # Find clusters by keyword overlap
    used_ids: set[str] = set()
    clusters: list[list[Entry]] = []

    # Process keywords by frequency (most connected first)
    sorted_keywords = sorted(
        keyword_index.items(),
        key=lambda x: len(x[1]),
        reverse=True,
    )

    for kw, entries_ctxs in sorted_keywords:
        # Filter out already used entries
        available = [
            (e, c) for e, c in entries_ctxs
            if e.id not in used_ids
        ]

        if len(available) < min_cluster_size:
            continue

        # Group entries that share multiple keywords
        cluster_entries = [e for e, _ in available]

        # Verify they share at least 2 keywords
        if _shares_multiple_keywords(cluster_entries, db, min_shared=2):
            clusters.append(cluster_entries)
            for e in cluster_entries:
                used_ids.add(e.id)

    # Analyze each cluster
    analyses = []
    for cluster in clusters:
        analysis = analyze_cluster(cluster, db)
        if analysis.consolidation_score >= min_score:
            analyses.append(analysis)

    # Sort by score
    analyses.sort(key=lambda a: a.consolidation_score, reverse=True)

    return analyses


def _shares_multiple_keywords(
    entries: list[Entry],
    db: Database,
    min_shared: int = 2,
) -> bool:
    """Check if entries share at least min_shared keywords.

    Args:
        entries: List of entries
        db: Database instance
        min_shared: Minimum shared keywords required

    Returns:
        True if entries share enough keywords
    """
    if len(entries) < 2:
        return False

    # Collect keywords from each entry
    entry_keywords: list[set[str]] = []
    for entry in entries:
        ctx = db.get_structured_context(entry.id)
        if ctx and ctx.trigger_keywords:
            entry_keywords.append(set(k.lower() for k in ctx.trigger_keywords))
        else:
            entry_keywords.append(set())

    # Find intersection
    if not entry_keywords:
        return False

    common = entry_keywords[0]
    for kws in entry_keywords[1:]:
        common = common & kws

    return len(common) >= min_shared


def generate_consolidation_summary(
    analysis: ClusterAnalysis,
    db: Database,
) -> str:
    """Generate a human-readable consolidation summary.

    Args:
        analysis: Cluster analysis result
        db: Database instance

    Returns:
        Formatted summary string
    """
    lines = [
        f"Consolidation Opportunity (score: {analysis.consolidation_score:.0%})",
        "=" * 50,
        f"Suggested Title: {analysis.suggested_title}",
        "",
        f"Common Keywords: {', '.join(analysis.common_keywords[:10])}",
        "",
        "Entries in cluster:",
    ]

    for entry in analysis.entries[:5]:
        ctx = db.get_structured_context(entry.id)
        kw_info = ""
        if ctx and ctx.trigger_keywords:
            kw_info = f" [{', '.join(ctx.trigger_keywords[:3])}]"
        lines.append(f"  - [{entry.id[:8]}] {entry.title[:40]}{kw_info}")

    if len(analysis.entries) > 5:
        lines.append(f"  ... and {len(analysis.entries) - 5} more")

    lines.extend([
        "",
        "Suggested consolidated keywords:",
        f"  {', '.join(analysis.suggested_keywords)}",
    ])

    return "\n".join(lines)
