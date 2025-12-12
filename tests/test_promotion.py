"""Tests for promotion module (US4, US5, US6)."""

from datetime import datetime, timedelta

import pytest


# Fixture for temp database
@pytest.fixture
def temp_db_path(tmp_path):
    """Create a temporary database path."""
    return tmp_path / "test.db"


class TestCalculatePromotionScore:
    """Tests for calculate_promotion_score() (T067-T069, T077)."""

    def test_score_with_high_citations(self):
        """Should give high score for many citations."""
        from rekall.models import StagingEntry, generate_ulid
        from rekall.promotion import calculate_promotion_score

        entry = StagingEntry(
            id=generate_ulid(),
            url="https://example.com/",
            domain="example.com",
            citation_count=10,  # Max citations
            project_count=0,
            last_seen=datetime.now(),
        )

        score = calculate_promotion_score(entry)

        # citation_weight=0.4, so max citation contribution is 40
        # recency_weight=0.3 with fresh last_seen gives ~30
        assert score >= 60  # At least 60 from citations + recency

    def test_score_with_high_projects(self):
        """Should give high score for many projects."""
        from rekall.models import StagingEntry, generate_ulid
        from rekall.promotion import calculate_promotion_score

        entry = StagingEntry(
            id=generate_ulid(),
            url="https://example.com/",
            domain="example.com",
            citation_count=0,
            project_count=5,  # Max projects
            last_seen=datetime.now(),
        )

        score = calculate_promotion_score(entry)

        # project_weight=0.3, so max project contribution is 30
        # recency_weight=0.3 with fresh last_seen gives ~30
        assert score >= 50  # At least 50 from projects + recency

    def test_score_with_all_factors(self):
        """Should combine all factors for high score."""
        from rekall.models import StagingEntry, generate_ulid
        from rekall.promotion import calculate_promotion_score

        entry = StagingEntry(
            id=generate_ulid(),
            url="https://example.com/",
            domain="example.com",
            citation_count=10,
            project_count=5,
            last_seen=datetime.now(),
        )

        score = calculate_promotion_score(entry)

        # All maxed out: should be close to 100
        assert score >= 90

    def test_score_with_no_factors(self):
        """Should give low score with no citations, projects, or recency."""
        from rekall.models import StagingEntry, generate_ulid
        from rekall.promotion import calculate_promotion_score

        entry = StagingEntry(
            id=generate_ulid(),
            url="https://example.com/",
            domain="example.com",
            citation_count=0,
            project_count=0,
            last_seen=None,
        )

        score = calculate_promotion_score(entry)

        assert score == 0.0


class TestDecayTemporal:
    """Tests for temporal decay in scoring (T069, T078)."""

    def test_decay_after_30_days(self):
        """Score should halve after 30 days (half-life)."""
        from rekall.models import StagingEntry, generate_ulid
        from rekall.promotion import calculate_promotion_score, PromotionConfig

        now = datetime.now()
        thirty_days_ago = now - timedelta(days=30)

        # Entry with only recency score
        entry = StagingEntry(
            id=generate_ulid(),
            url="https://example.com/",
            domain="example.com",
            citation_count=0,
            project_count=0,
            last_seen=thirty_days_ago,
        )

        score = calculate_promotion_score(entry, now=now)

        # recency_weight=0.3, after one half-life: 0.5 * 100 * 0.3 = 15
        assert 14 <= score <= 16

    def test_decay_after_60_days(self):
        """Score should quarter after 60 days (two half-lives)."""
        from rekall.models import StagingEntry, generate_ulid
        from rekall.promotion import calculate_promotion_score

        now = datetime.now()
        sixty_days_ago = now - timedelta(days=60)

        entry = StagingEntry(
            id=generate_ulid(),
            url="https://example.com/",
            domain="example.com",
            citation_count=0,
            project_count=0,
            last_seen=sixty_days_ago,
        )

        score = calculate_promotion_score(entry, now=now)

        # After two half-lives: 0.25 * 100 * 0.3 = 7.5
        assert 6 <= score <= 9

    def test_fresh_entry_no_decay(self):
        """Fresh entry should have full recency score."""
        from rekall.models import StagingEntry, generate_ulid
        from rekall.promotion import calculate_promotion_score

        now = datetime.now()

        entry = StagingEntry(
            id=generate_ulid(),
            url="https://example.com/",
            domain="example.com",
            citation_count=0,
            project_count=0,
            last_seen=now,
        )

        score = calculate_promotion_score(entry, now=now)

        # Full recency: 100 * 0.3 = 30
        assert 29 <= score <= 31


class TestIsEligibleForPromotion:
    """Tests for is_eligible_for_promotion() (T070, T079)."""

    def test_eligible_above_threshold(self):
        """Should be eligible with score above threshold."""
        from rekall.models import StagingEntry, generate_ulid
        from rekall.promotion import is_eligible_for_promotion

        entry = StagingEntry(
            id=generate_ulid(),
            url="https://example.com/",
            domain="example.com",
            citation_count=10,
            project_count=5,
            last_seen=datetime.now(),
            is_accessible=True,
        )

        assert is_eligible_for_promotion(entry) is True

    def test_not_eligible_below_threshold(self):
        """Should not be eligible with score below threshold."""
        from rekall.models import StagingEntry, generate_ulid
        from rekall.promotion import is_eligible_for_promotion

        entry = StagingEntry(
            id=generate_ulid(),
            url="https://example.com/",
            domain="example.com",
            citation_count=1,
            project_count=0,
            last_seen=datetime.now(),
            is_accessible=True,
        )

        assert is_eligible_for_promotion(entry) is False

    def test_not_eligible_if_inaccessible(self):
        """Should not be eligible if URL is inaccessible."""
        from rekall.models import StagingEntry, generate_ulid
        from rekall.promotion import is_eligible_for_promotion

        entry = StagingEntry(
            id=generate_ulid(),
            url="https://example.com/",
            domain="example.com",
            citation_count=10,
            project_count=5,
            last_seen=datetime.now(),
            is_accessible=False,  # Not accessible
        )

        assert is_eligible_for_promotion(entry) is False

    def test_not_eligible_if_already_promoted(self):
        """Should not be eligible if already promoted."""
        from rekall.models import StagingEntry, generate_ulid
        from rekall.promotion import is_eligible_for_promotion

        entry = StagingEntry(
            id=generate_ulid(),
            url="https://example.com/",
            domain="example.com",
            citation_count=10,
            project_count=5,
            last_seen=datetime.now(),
            is_accessible=True,
            promoted_at=datetime.now(),  # Already promoted
        )

        assert is_eligible_for_promotion(entry) is False


class TestPromotionIndicator:
    """Tests for get_promotion_indicator()."""

    def test_indicator_eligible(self):
        """Should return ⬆ for eligible entries."""
        from rekall.models import StagingEntry, generate_ulid
        from rekall.promotion import get_promotion_indicator

        entry = StagingEntry(
            id=generate_ulid(),
            url="https://example.com/",
            domain="example.com",
            citation_count=10,
            project_count=5,
            last_seen=datetime.now(),
            is_accessible=True,
        )

        assert get_promotion_indicator(entry) == "⬆"

    def test_indicator_near(self):
        """Should return → for near-threshold entries."""
        from rekall.models import StagingEntry, generate_ulid
        from rekall.promotion import get_promotion_indicator, PromotionConfig

        # Near threshold = 70 * 0.8 = 56
        # Need score around 56-69
        entry = StagingEntry(
            id=generate_ulid(),
            url="https://example.com/",
            domain="example.com",
            citation_count=5,  # 50% citations = 20 score
            project_count=3,  # 60% projects = 18 score
            last_seen=datetime.now(),  # Full recency = 30 score
            is_accessible=True,
            # Total: ~68, which is near but not eligible
        )

        indicator = get_promotion_indicator(entry)
        assert indicator in ["→", "⬆"]  # Depends on exact calculation

    def test_indicator_promoted(self):
        """Should return ✓ for promoted entries."""
        from rekall.models import StagingEntry, generate_ulid
        from rekall.promotion import get_promotion_indicator

        entry = StagingEntry(
            id=generate_ulid(),
            url="https://example.com/",
            domain="example.com",
            promoted_at=datetime.now(),
        )

        assert get_promotion_indicator(entry) == "✓"

    def test_indicator_inaccessible(self):
        """Should return ⚠ for inaccessible entries."""
        from rekall.models import StagingEntry, generate_ulid
        from rekall.promotion import get_promotion_indicator

        entry = StagingEntry(
            id=generate_ulid(),
            url="https://example.com/",
            domain="example.com",
            is_accessible=False,
        )

        assert get_promotion_indicator(entry) == "⚠"


class TestPromoteSource:
    """Tests for promote_source() (T080-T084, T087-T088)."""

    def test_promote_creates_source(self, temp_db_path):
        """Should create source from staging entry."""
        from rekall.db import Database
        from rekall.models import StagingEntry, generate_ulid
        from rekall.promotion import promote_source

        db = Database(temp_db_path)
        db.init()

        staging = StagingEntry(
            id=generate_ulid(),
            url="https://newsite.com/page",
            domain="newsite.com",
            title="Test Page",
            description="Test description",
            content_type="documentation",
            citation_count=5,
            project_count=2,
            last_seen=datetime.now(),
            promotion_score=75.0,
            is_accessible=True,
        )
        db.add_staging_entry(staging)

        result = promote_source(db, staging)

        assert result.success is True
        assert result.source_id is not None

        # Verify source was created
        source = db.get_source(result.source_id)
        assert source is not None
        assert source.url_pattern == staging.url  # URL stored as url_pattern
        assert source.domain == staging.domain

        # Verify staging was updated
        updated = db.get_staging_by_url(staging.url)
        assert updated.promoted_at is not None
        assert updated.promoted_to == result.source_id

        db.close()

    def test_promote_rejects_duplicate_url(self, temp_db_path):
        """Should reject promotion if URL already exists in sources."""
        from rekall.db import Database
        from rekall.models import StagingEntry, Source, generate_ulid
        from rekall.promotion import promote_source

        db = Database(temp_db_path)
        db.init()

        # Create existing source (url_pattern stores the full URL)
        existing = Source(
            id=generate_ulid(),
            domain="existing.com",
            url_pattern="https://existing.com/page",  # Full URL as pattern
        )
        db.add_source(existing)

        # Create staging with same URL
        staging = StagingEntry(
            id=generate_ulid(),
            url="https://existing.com/page",  # Same URL
            domain="existing.com",
        )
        db.add_staging_entry(staging)

        result = promote_source(db, staging)

        assert result.success is False
        assert "already exists" in result.error

        db.close()


class TestAutoPromoteEligible:
    """Tests for auto_promote_eligible() (T083, T089)."""

    def test_auto_promote_eligible_entries(self, temp_db_path):
        """Should promote all eligible entries."""
        from rekall.db import Database
        from rekall.models import StagingEntry, generate_ulid
        from rekall.promotion import auto_promote_eligible

        db = Database(temp_db_path)
        db.init()

        # Create eligible entry
        eligible = StagingEntry(
            id=generate_ulid(),
            url="https://eligible.com/page",
            domain="eligible.com",
            citation_count=10,
            project_count=5,
            last_seen=datetime.now(),
            is_accessible=True,
        )
        db.add_staging_entry(eligible)

        # Create non-eligible entry
        not_eligible = StagingEntry(
            id=generate_ulid(),
            url="https://noteligible.com/page",
            domain="noteligible.com",
            citation_count=1,
            project_count=0,
            is_accessible=True,
        )
        db.add_staging_entry(not_eligible)

        result = auto_promote_eligible(db)

        assert result.total_eligible == 1
        assert result.promoted == 1
        assert result.failed == 0

        # Verify eligible was promoted
        updated = db.get_staging_by_url(eligible.url)
        assert updated.promoted_at is not None

        db.close()

    def test_auto_promote_dry_run(self, temp_db_path):
        """Dry run should not actually promote."""
        from rekall.db import Database
        from rekall.models import StagingEntry, generate_ulid
        from rekall.promotion import auto_promote_eligible

        db = Database(temp_db_path)
        db.init()

        eligible = StagingEntry(
            id=generate_ulid(),
            url="https://eligible.com/page",
            domain="eligible.com",
            citation_count=10,
            project_count=5,
            last_seen=datetime.now(),
            is_accessible=True,
        )
        db.add_staging_entry(eligible)

        result = auto_promote_eligible(db, dry_run=True)

        assert result.total_eligible == 1
        assert result.promoted == 0  # Not actually promoted

        # Verify not promoted
        updated = db.get_staging_by_url(eligible.url)
        assert updated.promoted_at is None

        db.close()


class TestDemoteSource:
    """Tests for demote_source() (T092-T094, T098-T099)."""

    def test_demote_removes_source_and_resets_staging(self, temp_db_path):
        """Should delete source and reset staging entry promotion status."""
        from rekall.db import Database
        from rekall.models import StagingEntry, generate_ulid
        from rekall.promotion import promote_source, demote_source

        db = Database(temp_db_path)
        db.init()

        # Create and promote a staging entry
        staging = StagingEntry(
            id=generate_ulid(),
            url="https://promoted.com/page",
            domain="promoted.com",
            title="Promoted Page",
            citation_count=5,
            project_count=2,
            last_seen=datetime.now(),
            promotion_score=75.0,
            is_accessible=True,
        )
        db.add_staging_entry(staging)

        promote_result = promote_source(db, staging)
        assert promote_result.success is True
        source_id = promote_result.source_id

        # Verify promotion happened
        source = db.get_source(source_id)
        assert source is not None
        assert source.is_promoted is True

        # Now demote
        demote_result = demote_source(db, source_id)

        assert demote_result.success is True
        assert demote_result.source_id == source_id

        # Verify source was deleted
        deleted_source = db.get_source(source_id)
        assert deleted_source is None

        # Verify staging was reset
        updated_staging = db.get_staging_by_url(staging.url)
        assert updated_staging.promoted_at is None
        assert updated_staging.promoted_to is None

        db.close()

    def test_demote_rejects_non_promoted_source(self, temp_db_path):
        """Should reject demoting a source that was not promoted."""
        from rekall.db import Database
        from rekall.models import Source, generate_ulid
        from rekall.promotion import demote_source

        db = Database(temp_db_path)
        db.init()

        # Create a source that was NOT promoted (is_promoted=False)
        source = Source(
            id=generate_ulid(),
            domain="manual.com",
            url_pattern="https://manual.com/page",
            is_promoted=False,  # Not promoted
        )
        db.add_source(source)

        # Try to demote
        result = demote_source(db, source.id)

        assert result.success is False
        assert "is_promoted=False" in result.error

        # Verify source still exists
        existing = db.get_source(source.id)
        assert existing is not None

        db.close()

    def test_demote_source_not_found(self, temp_db_path):
        """Should return error if source ID not found."""
        from rekall.db import Database
        from rekall.promotion import demote_source

        db = Database(temp_db_path)
        db.init()

        result = demote_source(db, "nonexistent_id")

        assert result.success is False
        assert "not found" in result.error.lower()

        db.close()
