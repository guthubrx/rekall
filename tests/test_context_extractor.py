"""Tests for context extraction utilities (Feature 006 - Phase 3)."""

import pytest


class TestExtractKeywords:
    """Tests for extract_keywords function."""

    def test_extract_from_title_only(self):
        """Should extract keywords from title."""
        from rekall.context_extractor import extract_keywords

        keywords = extract_keywords("Fix 504 Gateway Timeout nginx")
        assert "504" in keywords
        assert "gateway" in keywords
        assert "timeout" in keywords
        assert "nginx" in keywords

    def test_extract_from_title_and_content(self):
        """Should extract keywords from both title and content."""
        from rekall.context_extractor import extract_keywords

        keywords = extract_keywords(
            "Fix database connection",
            "The database was refusing connections due to max_connections limit",
        )
        assert "database" in keywords
        assert "max_connections" in keywords
        assert "connection" in keywords or "connections" in keywords

    def test_excludes_stopwords(self):
        """Should exclude common stopwords."""
        from rekall.context_extractor import extract_keywords

        keywords = extract_keywords("The fix for the bug in the code")
        assert "the" not in keywords
        assert "for" not in keywords
        assert "fix" in keywords  # Not a stopword
        assert "bug" in keywords
        assert "code" in keywords

    def test_respects_min_length(self):
        """Should respect minimum keyword length."""
        from rekall.context_extractor import extract_keywords

        keywords = extract_keywords("An API bug fix", min_length=4)
        assert "api" not in keywords  # 3 chars
        assert "bug" not in keywords  # 3 chars
        # Only words >= 4 chars should be included

    def test_respects_max_keywords(self):
        """Should limit number of keywords returned."""
        from rekall.context_extractor import extract_keywords

        keywords = extract_keywords(
            "nginx proxy timeout gateway connection database redis cache",
            max_keywords=3,
        )
        assert len(keywords) <= 3

    def test_boosts_technical_terms_with_numbers(self):
        """Should boost terms containing numbers."""
        from rekall.context_extractor import extract_keywords

        keywords = extract_keywords("Error code 504 and 403 in nginx")
        # 504 and 403 should appear early due to number boost
        assert "504" in keywords[:5]
        assert "403" in keywords[:5]

    def test_boosts_terms_in_title(self):
        """Should boost terms that appear in title."""
        from rekall.context_extractor import extract_keywords

        keywords = extract_keywords(
            "nginx configuration",
            "Many different words here about servers and databases and caching",
        )
        # nginx and configuration should be at top
        assert keywords[0] in ["nginx", "configuration"]

    def test_handles_snake_case(self):
        """Should preserve snake_case identifiers."""
        from rekall.context_extractor import extract_keywords

        keywords = extract_keywords("Fix proxy_read_timeout setting")
        assert "proxy_read_timeout" in keywords

    def test_handles_empty_content(self):
        """Should handle empty content."""
        from rekall.context_extractor import extract_keywords

        keywords = extract_keywords("Fix nginx timeout", "")
        assert len(keywords) > 0
        assert "nginx" in keywords

    def test_handles_empty_title(self):
        """Should handle empty title."""
        from rekall.context_extractor import extract_keywords

        keywords = extract_keywords("", "nginx proxy timeout issue")
        assert len(keywords) > 0


class TestValidateContext:
    """Tests for validate_context function."""

    def test_valid_context_no_warnings(self):
        """Should return no warnings for valid context."""
        from rekall.context_extractor import validate_context

        warnings = validate_context(
            situation="The API was timing out on long database queries exceeding 30 seconds",
            solution="Increased the nginx proxy_read_timeout from 30s to 120s",
            trigger_keywords=["nginx", "timeout", "504", "proxy"],
        )
        assert len(warnings) == 0

    def test_short_situation_warning(self):
        """Should warn about short situation."""
        from rekall.context_extractor import validate_context

        warnings = validate_context(
            situation="Bug",
            solution="Increased timeout from 30s to 120s in nginx configuration",
            trigger_keywords=["nginx", "timeout", "504"],
        )
        assert any("Situation is short" in w for w in warnings)

    def test_short_solution_warning(self):
        """Should warn about short solution."""
        from rekall.context_extractor import validate_context

        warnings = validate_context(
            situation="The API was timing out on long database queries",
            solution="Fixed it",
            trigger_keywords=["nginx", "timeout", "504"],
        )
        assert any("Solution is short" in w for w in warnings)

    def test_single_keyword_warning(self):
        """Should warn about single keyword."""
        from rekall.context_extractor import validate_context

        warnings = validate_context(
            situation="The API was timing out on long database queries",
            solution="Increased the nginx proxy_read_timeout to 120s",
            trigger_keywords=["nginx"],
        )
        assert any("Only 1 keyword" in w for w in warnings)

    def test_generic_keyword_warning(self):
        """Should warn about generic keywords."""
        from rekall.context_extractor import validate_context

        warnings = validate_context(
            situation="The API was timing out on long database queries",
            solution="Increased the nginx proxy_read_timeout to 120s",
            trigger_keywords=["bug", "fix", "error"],
        )
        assert any("Generic keywords" in w for w in warnings)

    def test_short_keyword_warning(self):
        """Should warn about very short keywords."""
        from rekall.context_extractor import validate_context

        warnings = validate_context(
            situation="The API was timing out on long database queries",
            solution="Increased the nginx proxy_read_timeout to 120s",
            trigger_keywords=["db", "api", "timeout"],
        )
        assert any("very short" in w for w in warnings)


class TestSuggestKeywords:
    """Tests for suggest_keywords function."""

    def test_suggests_keywords_from_text(self):
        """Should suggest keywords based on text."""
        from rekall.context_extractor import suggest_keywords

        suggestions = suggest_keywords(
            title="Fix nginx proxy timeout",
            content="The server was returning 504 errors",
        )
        assert len(suggestions) > 0

    def test_excludes_existing_keywords(self):
        """Should not suggest keywords already provided."""
        from rekall.context_extractor import suggest_keywords

        suggestions = suggest_keywords(
            title="Fix nginx timeout",
            content="nginx proxy timeout configuration",
            existing_keywords=["nginx", "timeout"],
        )
        assert "nginx" not in suggestions
        assert "timeout" not in suggestions

    def test_respects_max_suggestions(self):
        """Should limit number of suggestions."""
        from rekall.context_extractor import suggest_keywords

        suggestions = suggest_keywords(
            title="Many words here nginx proxy timeout redis cache database",
            content="Even more words to extract from",
            max_suggestions=3,
        )
        assert len(suggestions) <= 3

    def test_case_insensitive_existing(self):
        """Should handle case insensitivity for existing keywords."""
        from rekall.context_extractor import suggest_keywords

        suggestions = suggest_keywords(
            title="Fix NGINX timeout",
            content="nginx configuration",
            existing_keywords=["NGINX"],
        )
        assert "nginx" not in suggestions


class TestCalculateKeywordScore:
    """Tests for calculate_keyword_score function."""

    def test_exact_match_scores_high(self):
        """Should score high for exact keyword matches."""
        from rekall.context_extractor import calculate_keyword_score

        score = calculate_keyword_score(
            query_keywords=["nginx", "timeout", "504"],
            entry_keywords=["nginx", "timeout", "504", "gateway"],
        )
        assert score > 0.7  # High score for exact matches

    def test_no_match_scores_zero(self):
        """Should score zero when no keywords match."""
        from rekall.context_extractor import calculate_keyword_score

        score = calculate_keyword_score(
            query_keywords=["redis", "cache"],
            entry_keywords=["nginx", "timeout", "504"],
        )
        assert score == 0.0

    def test_partial_match_scores_medium(self):
        """Should score medium for partial matches."""
        from rekall.context_extractor import calculate_keyword_score

        score = calculate_keyword_score(
            query_keywords=["timeout"],
            entry_keywords=["proxy_read_timeout", "nginx"],
        )
        assert 0.3 < score < 0.8  # Medium score for partial match

    def test_empty_keywords_scores_zero(self):
        """Should handle empty keyword lists."""
        from rekall.context_extractor import calculate_keyword_score

        assert calculate_keyword_score([], ["nginx"]) == 0.0
        assert calculate_keyword_score(["nginx"], []) == 0.0
        assert calculate_keyword_score([], []) == 0.0

    def test_case_insensitive_matching(self):
        """Should match keywords case-insensitively."""
        from rekall.context_extractor import calculate_keyword_score

        score = calculate_keyword_score(
            query_keywords=["NGINX", "Timeout"],
            entry_keywords=["nginx", "timeout"],
        )
        assert score > 0.7


class TestGetMatchingKeywords:
    """Tests for get_matching_keywords function."""

    def test_returns_exact_matches(self):
        """Should return exact keyword matches."""
        from rekall.context_extractor import get_matching_keywords

        matches = get_matching_keywords(
            query_keywords=["nginx", "timeout"],
            entry_keywords=["nginx", "timeout", "gateway"],
        )
        assert "nginx" in matches
        assert "timeout" in matches
        assert "gateway" not in matches

    def test_returns_partial_matches(self):
        """Should return partial matches (substring)."""
        from rekall.context_extractor import get_matching_keywords

        matches = get_matching_keywords(
            query_keywords=["timeout"],
            entry_keywords=["proxy_read_timeout", "nginx"],
        )
        assert "proxy_read_timeout" in matches
        assert "nginx" not in matches

    def test_empty_inputs(self):
        """Should handle empty inputs."""
        from rekall.context_extractor import get_matching_keywords

        assert get_matching_keywords([], ["nginx"]) == []
        assert get_matching_keywords(["nginx"], []) == []

    def test_case_insensitive_matching(self):
        """Should match case-insensitively and return original case."""
        from rekall.context_extractor import get_matching_keywords

        matches = get_matching_keywords(
            query_keywords=["NGINX"],
            entry_keywords=["nginx", "Timeout"],
        )
        assert "nginx" in matches
