"""Context extraction utilities for Rekall.

Provides automatic extraction of keywords and validation of structured context.
"""

from __future__ import annotations

import re

# Common stopwords to exclude from keyword extraction
STOPWORDS = {
    # English
    "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "as", "is", "was", "are", "were", "been",
    "be", "have", "has", "had", "do", "does", "did", "will", "would",
    "could", "should", "may", "might", "must", "shall", "can", "need",
    "it", "its", "this", "that", "these", "those", "i", "you", "he",
    "she", "we", "they", "what", "which", "who", "whom", "when", "where",
    "why", "how", "all", "each", "every", "both", "few", "more", "most",
    "other", "some", "such", "no", "nor", "not", "only", "own", "same",
    "so", "than", "too", "very", "just", "also", "now", "here", "there",
    "if", "then", "else", "because", "about", "into", "through", "during",
    "before", "after", "above", "below", "between", "under", "again",
    "further", "once", "any", "being", "get", "got", "use", "used",
    # French (common in codebase)
    "le", "la", "les", "un", "une", "des", "du", "de", "et", "ou",
    "mais", "donc", "car", "ni", "dans", "sur", "pour", "avec", "par",
    "est", "sont", "ont", "fait", "faire", "ce", "cette", "ces",
    "il", "elle", "nous", "vous", "ils", "elles", "qui", "que", "quoi",
    "je", "tu", "mon", "ton", "son", "notre", "votre", "leur",
    # Programming common words
    "function", "method", "class", "def", "return", "import", "var", "let", "const", "new", "true", "false", "null", "none",
    "value", "data", "result", "output", "input", "file", "line",
}

# Minimum word length for keyword extraction
MIN_KEYWORD_LENGTH = 3

# Maximum keywords to extract automatically
MAX_AUTO_KEYWORDS = 10


def extract_keywords(
    title: str,
    content: str = "",
    min_length: int = MIN_KEYWORD_LENGTH,
    max_keywords: int = MAX_AUTO_KEYWORDS,
) -> list[str]:
    """Extract significant keywords from title and content.

    Uses simple word frequency analysis, excluding stopwords.
    Prioritizes technical terms (CamelCase, snake_case, numbers).

    Args:
        title: Entry title
        content: Entry content (optional)
        min_length: Minimum word length to consider
        max_keywords: Maximum keywords to return

    Returns:
        List of lowercase keywords, most significant first
    """
    # Combine title (weighted more) and content
    text = f"{title} {title} {title} {content}"

    # Extract words (including technical terms)
    words = _tokenize(text)

    # Count frequency, excluding stopwords
    freq: dict[str, int] = {}
    for word in words:
        word_lower = word.lower()
        if len(word_lower) >= min_length and word_lower not in STOPWORDS:
            freq[word_lower] = freq.get(word_lower, 0) + 1

    # Boost technical terms (contain numbers, underscores, or mixed case)
    scored: list[tuple[str, float]] = []
    for word, count in freq.items():
        score = float(count)
        # Boost if contains numbers (likely error codes, versions)
        if re.search(r"\d", word):
            score *= 2.0
        # Boost if contains underscore (likely code identifier)
        if "_" in word:
            score *= 1.5
        # Boost if appears in title
        if word in title.lower():
            score *= 2.0
        scored.append((word, score))

    # Sort by score descending
    scored.sort(key=lambda x: x[1], reverse=True)

    return [word for word, _ in scored[:max_keywords]]


def _tokenize(text: str) -> list[str]:
    """Tokenize text into words, handling technical terms.

    Splits on whitespace and punctuation, preserving:
    - snake_case identifiers
    - Numbers and error codes (504, 403, etc.)
    - Hyphenated terms (proxy-read-timeout)

    Args:
        text: Input text

    Returns:
        List of word tokens
    """
    # Split CamelCase into separate words first
    text = re.sub(r"([a-z])([A-Z])", r"\1 \2", text)

    # Replace common separators with spaces (except underscore and hyphen)
    text = re.sub(r"[/\\:;,\(\)\[\]\{\}<>\"'`]", " ", text)

    # Split on whitespace
    tokens = text.split()

    # Further split on dots (but keep version numbers together)
    result = []
    for token in tokens:
        # Check if it's a version number (e.g., 3.14.1)
        if re.match(r"^\d+\.\d+(\.\d+)?$", token):
            result.append(token)
        else:
            # Split on dots
            result.extend(token.split("."))

    return result


def validate_context(
    situation: str,
    solution: str,
    trigger_keywords: list[str],
) -> list[str]:
    """Validate structured context and return warnings/suggestions.

    Args:
        situation: The situation description
        solution: The solution description
        trigger_keywords: List of keywords

    Returns:
        List of warning messages (empty if all good)
    """
    warnings = []

    # Check situation length
    if len(situation.strip()) < 20:
        warnings.append(
            "Situation is short. Add more details about the initial problem."
        )

    # Check solution length
    if len(solution.strip()) < 20:
        warnings.append(
            "Solution is short. Add more details about how it was resolved."
        )

    # Check keywords count
    if len(trigger_keywords) < 2:
        warnings.append(
            "Only 1 keyword provided. Add 2-3 more for better searchability."
        )
    elif len(trigger_keywords) < 3:
        warnings.append(
            "Consider adding 1-2 more keywords for better searchability."
        )

    # Check for very short keywords
    short_kws = [k for k in trigger_keywords if len(k) < 3]
    if short_kws:
        warnings.append(
            f"Some keywords are very short: {', '.join(short_kws)}. "
            "Longer keywords are more specific."
        )

    # Check for very generic keywords
    generic = {"error", "bug", "fix", "issue", "problem", "solution"}
    generic_found = [k for k in trigger_keywords if k.lower() in generic]
    if generic_found:
        warnings.append(
            f"Generic keywords found: {', '.join(generic_found)}. "
            "Add more specific terms."
        )

    return warnings


def suggest_keywords(
    title: str,
    content: str = "",
    existing_keywords: list[str] | None = None,
    max_suggestions: int = 5,
) -> list[str]:
    """Suggest additional keywords based on title and content.

    Args:
        title: Entry title
        content: Entry content
        existing_keywords: Keywords already provided
        max_suggestions: Maximum suggestions to return

    Returns:
        List of suggested keywords not in existing_keywords
    """
    existing = set(k.lower() for k in (existing_keywords or []))

    # Extract keywords from text
    extracted = extract_keywords(title, content, max_keywords=max_suggestions + 10)

    # Filter out existing
    suggestions = [k for k in extracted if k not in existing]

    return suggestions[:max_suggestions]


def calculate_keyword_score(
    query_keywords: list[str],
    entry_keywords: list[str],
) -> float:
    """Calculate relevance score based on keyword overlap.

    Uses Jaccard-like scoring with partial matching bonus.

    Args:
        query_keywords: Keywords extracted from search query
        entry_keywords: Trigger keywords from entry's structured context

    Returns:
        Score between 0.0 and 1.0
    """
    if not query_keywords or not entry_keywords:
        return 0.0

    query_set = set(k.lower() for k in query_keywords)
    entry_set = set(k.lower() for k in entry_keywords)

    # Exact matches
    exact_matches = query_set & entry_set

    # Partial matches (substring matching)
    partial_matches = 0
    for qk in query_set:
        if qk in exact_matches:
            continue
        for ek in entry_set:
            if qk in ek or ek in qk:
                partial_matches += 0.5
                break

    # Score: exact matches count full, partial count half
    total_score = len(exact_matches) + partial_matches

    # Normalize by query size (how well does entry cover query?)
    query_coverage = total_score / len(query_set) if query_set else 0.0

    # Bonus for high entry keyword match (precision)
    entry_coverage = len(exact_matches) / len(entry_set) if entry_set else 0.0

    # Combined score (weighted towards query coverage)
    return 0.7 * query_coverage + 0.3 * entry_coverage


def get_matching_keywords(
    query_keywords: list[str],
    entry_keywords: list[str],
) -> list[str]:
    """Get keywords that match between query and entry.

    Args:
        query_keywords: Keywords from search query
        entry_keywords: Keywords from entry's structured context

    Returns:
        List of matched keywords (from entry)
    """
    if not query_keywords or not entry_keywords:
        return []

    query_set = set(k.lower() for k in query_keywords)
    matches = []

    for ek in entry_keywords:
        ek_lower = ek.lower()
        # Exact match
        if ek_lower in query_set:
            matches.append(ek)
            continue
        # Partial match
        for qk in query_set:
            if qk in ek_lower or ek_lower in qk:
                matches.append(ek)
                break

    return matches
