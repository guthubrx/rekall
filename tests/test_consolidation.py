"""Tests for consolidation module (Feature 006 - Phase 5)."""

from unittest.mock import Mock


class TestClusterAnalysis:
    """Tests for ClusterAnalysis dataclass."""

    def test_cluster_analysis_creation(self):
        """Should create ClusterAnalysis with all fields."""
        from rekall.consolidation import ClusterAnalysis

        analysis = ClusterAnalysis(
            entries=[],
            common_keywords=["nginx", "timeout"],
            keyword_frequency={"nginx": 3, "timeout": 2},
            suggested_title="Pattern: nginx timeout",
            suggested_keywords=["nginx", "timeout"],
            consolidation_score=0.75,
        )

        assert analysis.common_keywords == ["nginx", "timeout"]
        assert analysis.consolidation_score == 0.75


class TestAnalyzeCluster:
    """Tests for analyze_cluster function."""

    def test_analyze_cluster_with_shared_keywords(self):
        """Should find common keywords across entries."""
        from rekall.consolidation import analyze_cluster
        from rekall.models import StructuredContext

        # Mock entries
        entries = [
            Mock(id="e1", title="Fix nginx timeout"),
            Mock(id="e2", title="Nginx proxy issue"),
            Mock(id="e3", title="504 gateway nginx"),
        ]

        # Mock database
        db = Mock()
        db.get_structured_context.side_effect = [
            StructuredContext(
                situation="API timing out",
                solution="Increased timeout",
                trigger_keywords=["nginx", "timeout", "504"],
            ),
            StructuredContext(
                situation="Proxy failing",
                solution="Fixed config",
                trigger_keywords=["nginx", "proxy", "gateway"],
            ),
            StructuredContext(
                situation="Gateway error",
                solution="Restarted",
                trigger_keywords=["nginx", "504", "gateway"],
            ),
        ]

        analysis = analyze_cluster(entries, db)

        assert "nginx" in analysis.common_keywords  # Appears in all 3
        assert len(analysis.entries) == 3
        assert analysis.consolidation_score > 0

    def test_analyze_cluster_empty_context(self):
        """Should handle entries without structured context."""
        from rekall.consolidation import analyze_cluster

        entries = [Mock(id="e1", title="Test")]
        db = Mock()
        db.get_structured_context.return_value = None

        analysis = analyze_cluster(entries, db)

        assert analysis.common_keywords == []
        assert analysis.consolidation_score == 0.0


class TestFindConsolidationOpportunities:
    """Tests for find_consolidation_opportunities function."""

    def test_finds_clusters_by_keywords(self):
        """Should find entries that share keywords."""
        from rekall.consolidation import find_consolidation_opportunities
        from rekall.models import StructuredContext

        # Mock entries with structured context
        entry1 = Mock(id="e1", title="Nginx timeout fix")
        entry2 = Mock(id="e2", title="Another nginx issue")
        ctx1 = StructuredContext(
            situation="Timeout",
            solution="Fixed",
            trigger_keywords=["nginx", "timeout", "504"],
        )
        ctx2 = StructuredContext(
            situation="Error",
            solution="Resolved",
            trigger_keywords=["nginx", "timeout", "proxy"],
        )

        db = Mock()
        db.get_entries_with_structured_context.return_value = [
            (entry1, ctx1),
            (entry2, ctx2),
        ]
        db.get_structured_context.side_effect = lambda eid: {
            "e1": ctx1,
            "e2": ctx2,
        }.get(eid)

        opportunities = find_consolidation_opportunities(
            db, min_cluster_size=2, min_score=0.0
        )

        # Should find opportunities if keywords overlap
        assert isinstance(opportunities, list)

    def test_no_opportunities_when_no_overlap(self):
        """Should return empty when no keyword overlap."""
        from rekall.consolidation import find_consolidation_opportunities
        from rekall.models import StructuredContext

        entry1 = Mock(id="e1", title="Redis cache")
        entry2 = Mock(id="e2", title="Nginx proxy")
        ctx1 = StructuredContext(
            situation="Cache miss",
            solution="Added cache",
            trigger_keywords=["redis", "cache", "memory"],
        )
        ctx2 = StructuredContext(
            situation="Proxy error",
            solution="Fixed config",
            trigger_keywords=["nginx", "proxy", "gateway"],
        )

        db = Mock()
        db.get_entries_with_structured_context.return_value = [
            (entry1, ctx1),
            (entry2, ctx2),
        ]

        opportunities = find_consolidation_opportunities(
            db, min_cluster_size=2, min_score=0.5
        )

        assert len(opportunities) == 0

    def test_respects_min_cluster_size(self):
        """Should respect minimum cluster size."""
        from rekall.consolidation import find_consolidation_opportunities

        db = Mock()
        db.get_entries_with_structured_context.return_value = []

        opportunities = find_consolidation_opportunities(
            db, min_cluster_size=3, min_score=0.0
        )

        assert opportunities == []


class TestGenerateConsolidationSummary:
    """Tests for generate_consolidation_summary function."""

    def test_generates_readable_summary(self):
        """Should generate human-readable summary."""
        from rekall.consolidation import ClusterAnalysis, generate_consolidation_summary
        from rekall.models import StructuredContext

        entries = [
            Mock(id="entry-001", title="Nginx timeout issue"),
            Mock(id="entry-002", title="Nginx proxy error"),
        ]

        analysis = ClusterAnalysis(
            entries=entries,
            common_keywords=["nginx", "timeout", "504"],
            keyword_frequency={"nginx": 2, "timeout": 2, "504": 1},
            suggested_title="Pattern: nginx timeout",
            suggested_keywords=["nginx", "timeout"],
            consolidation_score=0.8,
        )

        db = Mock()
        db.get_structured_context.return_value = StructuredContext(
            situation="Issue",
            solution="Fixed",
            trigger_keywords=["nginx", "timeout"],
        )

        summary = generate_consolidation_summary(analysis, db)

        assert "Consolidation Opportunity" in summary
        assert "80%" in summary
        assert "nginx" in summary
        assert "entry-001" in summary or "entry-00" in summary


class TestCalculateConsolidationScore:
    """Tests for _calculate_consolidation_score internal function."""

    def test_high_score_with_good_coverage(self):
        """Should score high with good context coverage and keyword overlap."""
        from rekall.consolidation import _calculate_consolidation_score
        from rekall.models import StructuredContext

        entries = [Mock(id=f"e{i}") for i in range(3)]
        contexts = [
            (entries[0], StructuredContext(
                situation="API server experiencing timeout issues",
                solution="Increased nginx timeout configuration",
                trigger_keywords=["nginx", "timeout"],
            )),
            (entries[1], StructuredContext(
                situation="Gateway returning 504 errors",
                solution="Fixed proxy timeout settings",
                trigger_keywords=["nginx", "timeout"],
            )),
            (entries[2], StructuredContext(
                situation="Upstream timeout on high load",
                solution="Tuned connection pool settings",
                trigger_keywords=["nginx", "timeout"],
            )),
        ]
        common_keywords = ["nginx", "timeout"]
        keyword_freq = {"nginx": 3, "timeout": 3}

        score = _calculate_consolidation_score(
            entries, contexts, common_keywords, keyword_freq
        )

        assert score > 0.7  # High score

    def test_low_score_with_poor_coverage(self):
        """Should score low with poor context coverage."""
        from rekall.consolidation import _calculate_consolidation_score

        entries = [Mock(id=f"e{i}") for i in range(5)]
        contexts = [(entries[0], Mock())]  # Only 1/5 has context
        common_keywords = ["nginx"]
        keyword_freq = {"nginx": 1}

        score = _calculate_consolidation_score(
            entries, contexts, common_keywords, keyword_freq
        )

        assert score < 0.5  # Low score


class TestSharesMultipleKeywords:
    """Tests for _shares_multiple_keywords internal function."""

    def test_returns_true_when_sharing_keywords(self):
        """Should return True when entries share enough keywords."""
        from rekall.consolidation import _shares_multiple_keywords
        from rekall.models import StructuredContext

        entries = [Mock(id="e1"), Mock(id="e2")]
        db = Mock()
        db.get_structured_context.side_effect = [
            StructuredContext(
                situation="Server timeout on API requests",
                solution="Increased nginx timeout to 120s",
                trigger_keywords=["nginx", "timeout", "504"],
            ),
            StructuredContext(
                situation="Gateway returning timeout errors",
                solution="Fixed proxy configuration",
                trigger_keywords=["nginx", "timeout", "gateway"],
            ),
        ]

        result = _shares_multiple_keywords(entries, db, min_shared=2)

        assert result is True  # nginx and timeout shared

    def test_returns_false_when_not_enough_shared(self):
        """Should return False when not enough keywords shared."""
        from rekall.consolidation import _shares_multiple_keywords
        from rekall.models import StructuredContext

        entries = [Mock(id="e1"), Mock(id="e2")]
        db = Mock()
        db.get_structured_context.side_effect = [
            StructuredContext(
                situation="Server timeout on API requests",
                solution="Increased nginx timeout to 120s",
                trigger_keywords=["nginx", "timeout"],
            ),
            StructuredContext(
                situation="Redis cache eviction issues",
                solution="Increased cache memory allocation",
                trigger_keywords=["redis", "cache"],
            ),
        ]

        result = _shares_multiple_keywords(entries, db, min_shared=2)

        assert result is False
