"""Integration tests for Feature 009 - Sources Integration.

End-to-end tests verifying the complete sources workflow:
- Source creation and linking to entries
- Scoring system (usage × recency × reliability)
- Backlinks and cross-references
- Statistics and analytics
- Link rot detection
"""

from datetime import datetime, timedelta
from unittest.mock import patch

from rekall.models import Entry, Source, generate_ulid


class TestSourcesE2EWorkflow:
    """End-to-end tests for the complete sources workflow."""

    def test_complete_workflow_add_source_to_entry(self, memory_db):
        """Test full workflow: create entry, add source, verify linking."""
        db = memory_db

        # 1. Create an entry
        entry = Entry(
            id=generate_ulid(),
            title="How to use Python asyncio",
            content="Asyncio is a library for async programming...",
            type="pattern",
            project="python-studies",
        )
        db.add(entry)
        assert entry.id

        # 2. Create a source
        source = Source(
            domain="docs.python.org",
            url_pattern="/library/asyncio*",
            reliability="A",
            decay_rate="slow",
        )
        created_source = db.add_source(source)
        assert created_source.id

        # 3. Link source to entry
        link = db.link_entry_to_source(
            entry_id=entry.id,
            source_type="url",
            source_ref="https://docs.python.org/3/library/asyncio.html",
            source_id=created_source.id,
            note="Official Python docs",
        )
        assert link.id
        assert link.entry_id == entry.id
        assert link.source_id == created_source.id

        # 4. Verify entry sources
        sources = db.get_entry_sources(entry.id)
        assert len(sources) == 1
        assert sources[0].source_ref == "https://docs.python.org/3/library/asyncio.html"
        assert sources[0].note == "Official Python docs"

        # 5. Verify backlinks from source
        backlinks = db.get_source_backlinks(created_source.id)
        assert len(backlinks) == 1
        entry_from_backlink, _ = backlinks[0]
        assert entry_from_backlink.id == entry.id

        # 6. Verify source usage was incremented
        updated_source = db.get_source(created_source.id)
        assert updated_source.usage_count == 1
        assert updated_source.last_used is not None

    def test_workflow_multiple_entries_same_source(self, memory_db):
        """Test linking multiple entries to the same source."""
        db = memory_db

        # Create source
        source = Source(
            domain="stackoverflow.com",
            url_pattern="/questions/*",
            reliability="B",
        )
        created_source = db.add_source(source)

        # Create multiple entries and link them
        for i in range(5):
            entry = Entry(
                id=generate_ulid(),
                title=f"Question {i}",
                content=f"Content about question {i}",
                type="pattern",
            )
            db.add(entry)
            db.link_entry_to_source(
                entry_id=entry.id,
                source_type="url",
                source_ref=f"https://stackoverflow.com/questions/{1000 + i}",
                source_id=created_source.id,
            )

        # Verify backlinks count
        backlinks_count = db.count_source_backlinks(created_source.id)
        assert backlinks_count == 5

        # Verify usage count
        updated_source = db.get_source(created_source.id)
        assert updated_source.usage_count == 5

    def test_workflow_entry_multiple_sources(self, memory_db):
        """Test linking multiple sources to the same entry."""
        db = memory_db

        # Create entry
        entry = Entry(
            id=generate_ulid(),
            title="Comprehensive Python Guide",
            content="Multiple sources for learning Python",
            type="pattern",
        )
        db.add(entry)

        # Create and link multiple sources
        sources_data = [
            ("python.org", "/docs/*", "A"),
            ("realpython.com", "/tutorials/*", "B"),
            ("stackoverflow.com", "/questions/*", "B"),
        ]

        for domain, pattern, reliability in sources_data:
            source = Source(
                domain=domain,
                url_pattern=pattern,
                reliability=reliability,
            )
            created_source = db.add_source(source)
            db.link_entry_to_source(
                entry_id=entry.id,
                source_type="url",
                source_ref=f"https://{domain}/example",
                source_id=created_source.id,
            )

        # Verify entry has all sources
        entry_sources = db.get_entry_sources(entry.id)
        assert len(entry_sources) == 3


class TestScoringSystemE2E:
    """End-to-end tests for the scoring system."""

    def test_score_increases_with_usage(self, memory_db):
        """Test that source score increases with repeated usage."""
        db = memory_db

        # Create source with known initial state
        source = Source(
            domain="example.com",
            reliability="B",
            decay_rate="medium",
        )
        created_source = db.add_source(source)
        initial_score = db.calculate_source_score(created_source)

        # Use source multiple times
        for i in range(10):
            entry = Entry(
                id=generate_ulid(),
                title=f"Entry {i}",
                content="...",
                type="pattern",
            )
            db.add(entry)
            db.link_entry_to_source(
                entry_id=entry.id,
                source_type="url",
                source_ref=f"https://example.com/page{i}",
                source_id=created_source.id,
            )

        # Recalculate score
        updated_source = db.get_source(created_source.id)
        final_score = db.calculate_source_score(updated_source)

        # Score should increase (more usage = higher score)
        assert final_score > initial_score

    def test_reliability_affects_score(self, memory_db):
        """Test that reliability rating affects the score."""
        db = memory_db

        # Create sources with different reliability
        sources = []
        for reliability in ["A", "B", "C"]:
            source = Source(
                domain=f"{reliability.lower()}-source.com",
                reliability=reliability,
                usage_count=10,
                last_used=datetime.now(),
            )
            created_source = db.add_source(source)
            sources.append(created_source)

        # Calculate scores
        scores = [db.calculate_source_score(s) for s in sources]

        # A > B > C
        assert scores[0] > scores[1] > scores[2]

    def test_decay_rate_affects_score_over_time(self, memory_db):
        """Test that decay rate affects score degradation."""
        db = memory_db

        old_date = datetime.now() - timedelta(days=180)  # 6 months ago

        # Create sources with different decay rates
        fast_source = Source(
            domain="fast.com",
            decay_rate="fast",
            usage_count=10,
            last_used=old_date,
            reliability="B",
        )
        slow_source = Source(
            domain="slow.com",
            decay_rate="slow",
            usage_count=10,
            last_used=old_date,
            reliability="B",
        )

        fast_created = db.add_source(fast_source)
        slow_created = db.add_source(slow_source)

        fast_score = db.calculate_source_score(fast_created)
        slow_score = db.calculate_source_score(slow_created)

        # Slow decay should retain more score
        assert slow_score > fast_score

    def test_top_sources_ranking(self, memory_db):
        """Test that get_top_sources returns correctly ranked sources."""
        db = memory_db

        # Create sources with varying scores
        for i in range(5):
            source = Source(
                domain=f"source{i}.com",
                reliability="A" if i > 2 else "B",
                usage_count=i * 5,
                last_used=datetime.now() if i > 1 else None,
            )
            db.add_source(source)

        # Get top sources
        top = db.get_top_sources(limit=3)

        # Should be ordered by score descending
        scores = [s.personal_score for s in top]
        assert scores == sorted(scores, reverse=True)


class TestBacklinksE2E:
    """End-to-end tests for backlinks functionality."""

    def test_backlinks_pagination(self, memory_db):
        """Test backlinks pagination with large datasets."""
        db = memory_db

        # Create source
        source = Source(domain="example.com")
        created_source = db.add_source(source)

        # Create many entries linked to source
        for i in range(25):
            entry = Entry(
                id=generate_ulid(),
                title=f"Entry {i}",
                content="...",
                type="pattern",
            )
            db.add(entry)
            db.link_entry_to_source(
                entry_id=entry.id,
                source_type="url",
                source_ref=f"https://example.com/{i}",
                source_id=created_source.id,
            )

        # Test pagination
        page1 = db.get_source_backlinks(created_source.id, limit=10, offset=0)
        page2 = db.get_source_backlinks(created_source.id, limit=10, offset=10)
        page3 = db.get_source_backlinks(created_source.id, limit=10, offset=20)

        assert len(page1) == 10
        assert len(page2) == 10
        assert len(page3) == 5  # Only 5 remaining

        # Ensure no duplicates
        all_ids = [e.id for e, _ in page1 + page2 + page3]
        assert len(all_ids) == len(set(all_ids))

    def test_backlinks_by_domain(self, memory_db):
        """Test getting backlinks by domain pattern."""
        db = memory_db

        # Create sources for same domain with different patterns
        source1 = Source(domain="github.com", url_pattern="/user/repo1/*")
        source2 = Source(domain="github.com", url_pattern="/user/repo2/*")
        source3 = Source(domain="gitlab.com", url_pattern="/*")

        s1 = db.add_source(source1)
        s2 = db.add_source(source2)
        s3 = db.add_source(source3)

        # Link entries
        for source in [s1, s2, s3]:
            entry = Entry(
                id=generate_ulid(),
                title=f"Entry for {source.domain}",
                content="...",
                type="pattern",
            )
            db.add(entry)
            db.link_entry_to_source(
                entry_id=entry.id,
                source_type="url",
                source_ref=f"https://{source.domain}/test",
                source_id=source.id,
            )

        # Get backlinks by domain
        github_backlinks = db.get_backlinks_by_domain("github.com")
        assert len(github_backlinks) == 2

        gitlab_backlinks = db.get_backlinks_by_domain("gitlab.com")
        assert len(gitlab_backlinks) == 1


class TestStatisticsE2E:
    """End-to-end tests for source statistics."""

    def test_comprehensive_statistics(self, memory_db):
        """Test that statistics reflect the actual data state."""
        db = memory_db

        # Create varied dataset
        # Active sources
        for i in range(3):
            source = Source(
                domain=f"active{i}.com",
                status="active",
                reliability=["A", "B", "C"][i],
                usage_count=10 - i,
                last_used=datetime.now(),
            )
            db.add_source(source)

        # Inaccessible source
        inaccessible = Source(
            domain="dead.com",
            status="inaccessible",
        )
        db.add_source(inaccessible)

        # Get statistics
        stats = db.get_source_statistics()

        # Use actual keys from get_source_statistics()
        assert stats["total"] == 4
        assert stats["by_status"]["active"] == 3
        assert stats["by_status"]["inaccessible"] == 1


class TestLinkRotE2E:
    """End-to-end tests for link rot detection."""

    def test_sources_to_verify_selection(self, memory_db):
        """Test that sources are correctly selected for verification."""
        db = memory_db

        now = datetime.now()
        old_date = now - timedelta(days=10)

        # Source verified recently (should not be selected)
        recent = Source(
            domain="recent.com",
            status="active",
            last_verified=now,
        )
        db.add_source(recent)

        # Source not verified recently (should be selected)
        old = Source(
            domain="old.com",
            status="active",
            last_verified=old_date,
        )
        db.add_source(old)

        # Source never verified (should be selected)
        never = Source(
            domain="never.com",
            status="active",
            last_verified=None,
        )
        db.add_source(never)

        # Get sources to verify
        to_verify = db.get_sources_to_verify(days_since_check=1)

        domains = [s.domain for s in to_verify]
        assert "recent.com" not in domains
        assert "old.com" in domains
        assert "never.com" in domains

    def test_status_update_after_verification(self, memory_db):
        """Test that source status updates correctly after verification."""
        db = memory_db

        source = Source(
            domain="example.com",
            status="active",
        )
        created = db.add_source(source)

        # Update to inaccessible
        db.update_source_status(
            created.id,
            status="inaccessible",
            last_verified=datetime.now(),
        )

        updated = db.get_source(created.id)
        assert updated.status == "inaccessible"
        assert updated.last_verified is not None

    @patch("rekall.link_rot.LinkRotChecker.check_url_accessibility")
    def test_verify_sources_integration(self, mock_check, memory_db):
        """Test the full verify_sources workflow."""
        from rekall.link_rot import verify_sources

        db = memory_db

        # Create sources
        good = Source(domain="good.com", status="active")
        bad = Source(domain="bad.com", status="active")
        db.add_source(good)
        db.add_source(bad)

        # Mock accessibility checks
        def check_side_effect(url):
            if "good.com" in url:
                return (True, "OK (200)")
            return (False, "Not Found (404)")

        mock_check.side_effect = check_side_effect

        # Run verification
        results = verify_sources(db, limit=10)

        assert results["verified"] == 2
        assert results["accessible"] == 1
        assert results["inaccessible"] == 1


class TestUnlinkingE2E:
    """End-to-end tests for unlinking sources from entries."""

    def test_unlink_decreases_usage(self, memory_db):
        """Test that unlinking properly affects source statistics."""
        db = memory_db

        # Setup
        source = Source(domain="example.com")
        created_source = db.add_source(source)

        entry = Entry(
            id=generate_ulid(),
            title="Test",
            content="...",
            type="pattern",
        )
        db.add(entry)

        link = db.link_entry_to_source(
            entry_id=entry.id,
            source_type="url",
            source_ref="https://example.com/test",
            source_id=created_source.id,
        )

        # Verify initial state
        assert db.count_source_backlinks(created_source.id) == 1

        # Unlink
        db.unlink_entry_from_source(link.id)

        # Verify after unlink
        assert db.count_source_backlinks(created_source.id) == 0
        entry_sources = db.get_entry_sources(entry.id)
        assert len(entry_sources) == 0

    def test_delete_source_sets_null(self, memory_db):
        """Test that deleting a source sets source_id to NULL (not cascade delete)."""
        db = memory_db

        # Setup
        source = Source(domain="example.com")
        created_source = db.add_source(source)

        entries = []
        for i in range(3):
            entry = Entry(
                id=generate_ulid(),
                title=f"Entry {i}",
                content="...",
                type="pattern",
            )
            db.add(entry)
            entries.append(entry)
            db.link_entry_to_source(
                entry_id=entry.id,
                source_type="url",
                source_ref=f"https://example.com/{i}",
                source_id=created_source.id,
            )

        # Delete source
        db.delete_source(created_source.id)

        # Verify source is gone
        assert db.get_source(created_source.id) is None

        # Verify links remain but source_id is NULL (ON DELETE SET NULL behavior)
        for entry in entries:
            entry_sources = db.get_entry_sources(entry.id)
            assert len(entry_sources) == 1  # Links still exist
            assert entry_sources[0].source_id is None  # But source_id is NULL


class TestThemeAndFileSourcesE2E:
    """End-to-end tests for non-URL source types."""

    def test_theme_source_workflow(self, memory_db):
        """Test workflow for theme-based sources."""
        db = memory_db

        entry = Entry(
            id=generate_ulid(),
            title="Learning from mentor",
            content="Key insights from code review session",
            type="pattern",
        )
        db.add(entry)

        # Link theme source (no curated Source needed)
        link = db.link_entry_to_source(
            entry_id=entry.id,
            source_type="theme",
            source_ref="Code Review Sessions",
            note="Weekly mentor sessions",
        )

        assert link.source_type == "theme"
        assert link.source_id is None  # No curated source
        assert link.note == "Weekly mentor sessions"

        # Verify retrieval
        sources = db.get_entry_sources(entry.id)
        assert len(sources) == 1
        assert sources[0].source_type == "theme"

    def test_file_source_workflow(self, memory_db):
        """Test workflow for file-based sources."""
        db = memory_db

        entry = Entry(
            id=generate_ulid(),
            title="Notes from book",
            content="Key concepts from Clean Code",
            type="pattern",
        )
        db.add(entry)

        # Link file source
        link = db.link_entry_to_source(
            entry_id=entry.id,
            source_type="file",
            source_ref="/path/to/clean-code.pdf",
            note="Chapter 3: Functions",
        )

        assert link.source_type == "file"
        assert "/path/to/clean-code.pdf" in link.source_ref

    def test_mixed_source_types_on_entry(self, memory_db):
        """Test entry with multiple source types."""
        db = memory_db

        entry = Entry(
            id=generate_ulid(),
            title="Comprehensive study",
            content="Multiple sources",
            type="pattern",
        )
        db.add(entry)

        # URL source with curated Source
        url_source = Source(domain="example.com", reliability="A")
        created_url_source = db.add_source(url_source)
        db.link_entry_to_source(
            entry_id=entry.id,
            source_type="url",
            source_ref="https://example.com/article",
            source_id=created_url_source.id,
        )

        # Theme source
        db.link_entry_to_source(
            entry_id=entry.id,
            source_type="theme",
            source_ref="Research Project",
        )

        # File source
        db.link_entry_to_source(
            entry_id=entry.id,
            source_type="file",
            source_ref="/docs/paper.pdf",
        )

        # Verify all sources
        sources = db.get_entry_sources(entry.id)
        assert len(sources) == 3
        types = {s.source_type for s in sources}
        assert types == {"url", "theme", "file"}
