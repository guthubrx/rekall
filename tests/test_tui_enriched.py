"""Tests for Feature 023 - TUI Enriched Entries Tab.

Tests the database methods and TUI components for displaying
and managing AI-enriched sources.
"""

from datetime import datetime
from pathlib import Path

import pytest


class TestEnrichedSourcesDB:
    """Tests for enriched sources database methods."""

    def test_get_enriched_sources_empty(self, temp_db_path: Path):
        """Should return empty list when no enriched sources exist."""
        from rekall.db import Database

        db = Database(temp_db_path)
        db.init()

        result = list(db.get_enriched_sources())
        assert result == []
        db.close()

    def test_get_enriched_sources_returns_only_enriched(self, temp_db_path: Path):
        """Should only return sources with enrichment_status != 'none'."""
        from rekall.db import Database
        from rekall.models import Source, generate_ulid

        db = Database(temp_db_path)
        db.init()

        # Create a non-enriched source
        non_enriched = Source(
            id=generate_ulid(),
            domain="example.com",
            url_pattern="https://example.com/*",
            enrichment_status="none",
        )
        db.add_source(non_enriched)

        # Create an enriched source
        enriched = Source(
            id=generate_ulid(),
            domain="enriched.com",
            url_pattern="https://enriched.com/*",
            enrichment_status="proposed",
            ai_type="documentation",
            ai_tags=["python", "testing"],
            ai_summary="A test source",
            ai_confidence=0.85,
        )
        db.add_source(enriched)

        result = list(db.get_enriched_sources())
        assert len(result) == 1
        assert result[0].domain == "enriched.com"
        db.close()

    def test_get_enriched_sources_filter_by_status(self, temp_db_path: Path):
        """Should filter by enrichment status."""
        from rekall.db import Database
        from rekall.models import Source, generate_ulid

        db = Database(temp_db_path)
        db.init()

        # Create proposed source
        proposed = Source(
            id=generate_ulid(),
            domain="proposed.com",
            url_pattern="https://proposed.com/*",
            enrichment_status="proposed",
            ai_confidence=0.9,
        )
        db.add_source(proposed)

        # Create validated source
        validated = Source(
            id=generate_ulid(),
            domain="validated.com",
            url_pattern="https://validated.com/*",
            enrichment_status="validated",
            ai_confidence=0.95,
            enrichment_validated_at=datetime.now(),
            enrichment_validated_by="human",
        )
        db.add_source(validated)

        # Filter by proposed
        proposed_only = list(db.get_enriched_sources(status="proposed"))
        assert len(proposed_only) == 1
        assert proposed_only[0].domain == "proposed.com"

        # Filter by validated
        validated_only = list(db.get_enriched_sources(status="validated"))
        assert len(validated_only) == 1
        assert validated_only[0].domain == "validated.com"

        db.close()

    def test_get_enriched_sources_sorted_by_status_then_confidence(
        self, temp_db_path: Path
    ):
        """Should return proposed first, then validated, sorted by confidence."""
        from rekall.db import Database
        from rekall.models import Source, generate_ulid

        db = Database(temp_db_path)
        db.init()

        # Create sources in random order
        sources = [
            ("validated1.com", "validated", 0.95),
            ("proposed1.com", "proposed", 0.80),
            ("validated2.com", "validated", 0.70),
            ("proposed2.com", "proposed", 0.90),
        ]

        for domain, status, conf in sources:
            source = Source(
                id=generate_ulid(),
                domain=domain,
                url_pattern=f"https://{domain}/*",
                enrichment_status=status,
                ai_confidence=conf,
            )
            db.add_source(source)

        result = list(db.get_enriched_sources())

        # First two should be proposed (sorted by confidence DESC)
        assert result[0].domain == "proposed2.com"  # 0.90
        assert result[1].domain == "proposed1.com"  # 0.80

        # Last two should be validated (sorted by confidence DESC)
        assert result[2].domain == "validated1.com"  # 0.95
        assert result[3].domain == "validated2.com"  # 0.70

        db.close()


class TestValidateEnrichment:
    """Tests for validate_enrichment method."""

    def test_validate_enrichment_success(self, temp_db_path: Path):
        """Should change status from proposed to validated."""
        from rekall.db import Database
        from rekall.models import Source, generate_ulid

        db = Database(temp_db_path)
        db.init()

        source = Source(
            id=generate_ulid(),
            domain="test.com",
            url_pattern="https://test.com/*",
            enrichment_status="proposed",
            ai_confidence=0.9,
        )
        db.add_source(source)

        result = db.validate_enrichment(source.id)
        assert result is True

        # Verify status changed
        updated = db.get_source(source.id)
        assert updated.enrichment_status == "validated"
        assert updated.enrichment_validated_at is not None
        assert updated.enrichment_validated_by == "human"

        db.close()

    def test_validate_enrichment_not_proposed(self, temp_db_path: Path):
        """Should return False if source is not proposed."""
        from rekall.db import Database
        from rekall.models import Source, generate_ulid

        db = Database(temp_db_path)
        db.init()

        source = Source(
            id=generate_ulid(),
            domain="test.com",
            url_pattern="https://test.com/*",
            enrichment_status="validated",  # Already validated
            ai_confidence=0.9,
        )
        db.add_source(source)

        result = db.validate_enrichment(source.id)
        assert result is False

        db.close()

    def test_validate_enrichment_nonexistent(self, temp_db_path: Path):
        """Should return False for nonexistent source."""
        from rekall.db import Database

        db = Database(temp_db_path)
        db.init()

        result = db.validate_enrichment("nonexistent_id")
        assert result is False

        db.close()


class TestRejectEnrichment:
    """Tests for reject_enrichment method."""

    def test_reject_enrichment_success(self, temp_db_path: Path):
        """Should reset status from proposed to none."""
        from rekall.db import Database
        from rekall.models import Source, generate_ulid

        db = Database(temp_db_path)
        db.init()

        source = Source(
            id=generate_ulid(),
            domain="test.com",
            url_pattern="https://test.com/*",
            enrichment_status="proposed",
            ai_type="documentation",
            ai_tags=["python"],
            ai_summary="Test summary",
            ai_confidence=0.9,
        )
        db.add_source(source)

        result = db.reject_enrichment(source.id)
        assert result is True

        # Verify status reset to none
        updated = db.get_source(source.id)
        assert updated.enrichment_status == "none"
        # AI metadata should be preserved for re-enrichment
        assert updated.ai_type == "documentation"

        db.close()

    def test_reject_enrichment_not_proposed(self, temp_db_path: Path):
        """Should return False if source is not proposed."""
        from rekall.db import Database
        from rekall.models import Source, generate_ulid

        db = Database(temp_db_path)
        db.init()

        source = Source(
            id=generate_ulid(),
            domain="test.com",
            url_pattern="https://test.com/*",
            enrichment_status="none",  # Not proposed
        )
        db.add_source(source)

        result = db.reject_enrichment(source.id)
        assert result is False

        db.close()


class TestCountEnrichedSources:
    """Tests for count_enriched_sources method."""

    def test_count_enriched_sources_empty(self, temp_db_path: Path):
        """Should return zeros when no enriched sources exist."""
        from rekall.db import Database

        db = Database(temp_db_path)
        db.init()

        counts = db.count_enriched_sources()
        assert counts == {"total": 0, "proposed": 0, "validated": 0}

        db.close()

    def test_count_enriched_sources_mixed(self, temp_db_path: Path):
        """Should count proposed and validated separately."""
        from rekall.db import Database
        from rekall.models import Source, generate_ulid

        db = Database(temp_db_path)
        db.init()

        # Add 2 proposed
        for i in range(2):
            db.add_source(
                Source(
                    id=generate_ulid(),
                    domain=f"proposed{i}.com",
                    url_pattern=f"https://proposed{i}.com/*",
                    enrichment_status="proposed",
                )
            )

        # Add 3 validated
        for i in range(3):
            db.add_source(
                Source(
                    id=generate_ulid(),
                    domain=f"validated{i}.com",
                    url_pattern=f"https://validated{i}.com/*",
                    enrichment_status="validated",
                )
            )

        # Add 1 non-enriched (should not be counted)
        db.add_source(
            Source(
                id=generate_ulid(),
                domain="none.com",
                url_pattern="https://none.com/*",
                enrichment_status="none",
            )
        )

        counts = db.count_enriched_sources()
        assert counts == {"total": 5, "proposed": 2, "validated": 3}

        db.close()


class TestTUIEnrichedComponents:
    """Tests for TUI components (basic import/structure tests)."""

    def test_unified_sources_app_has_enriched_binding(self):
        """UnifiedSourcesApp should have 'n' binding for enriched tab."""
        from rekall.tui_main import UnifiedSourcesApp

        bindings = {b.key: b.action for b in UnifiedSourcesApp.BINDINGS}
        assert "n" in bindings
        assert bindings["n"] == "tab_enriched"

    def test_unified_sources_app_has_validate_binding(self):
        """UnifiedSourcesApp should have 'v' binding for quick validate."""
        from rekall.tui_main import UnifiedSourcesApp

        bindings = {b.key: b.action for b in UnifiedSourcesApp.BINDINGS}
        assert "v" in bindings
        assert bindings["v"] == "quick_validate"

    def test_unified_sources_app_has_enriched_methods(self):
        """UnifiedSourcesApp should have all required enriched methods."""
        from rekall.tui_main import UnifiedSourcesApp

        required_methods = [
            "_setup_enriched_table",
            "_populate_enriched_table",
            "_refresh_enriched",
            "_action_validate_enrichment",
            "_action_reject_enrichment",
            "action_quick_validate",
            "action_tab_enriched",
        ]

        for method in required_methods:
            assert hasattr(
                UnifiedSourcesApp, method
            ), f"Missing method: {method}"
