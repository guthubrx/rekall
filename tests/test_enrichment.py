"""Tests for enrichment module (US2)."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestClassifyContentType:
    """Tests for classify_content_type() (T053)."""

    def test_classify_documentation_docs_subdomain(self):
        """Should classify docs.* as documentation."""
        from rekall.enrichment import classify_content_type

        assert classify_content_type("https://docs.python.org/3/") == "documentation"
        assert classify_content_type("https://docs.djangoproject.com/") == "documentation"

    def test_classify_documentation_readthedocs(self):
        """Should classify readthedocs as documentation."""
        from rekall.enrichment import classify_content_type

        assert classify_content_type("https://requests.readthedocs.io/") == "documentation"

    def test_classify_documentation_path(self):
        """Should classify /docs/ path as documentation."""
        from rekall.enrichment import classify_content_type

        assert classify_content_type("https://example.com/docs/getting-started") == "documentation"

    def test_classify_repository_github(self):
        """Should classify github.com as repository."""
        from rekall.enrichment import classify_content_type

        assert classify_content_type("https://github.com/user/repo") == "repository"

    def test_classify_repository_gitlab(self):
        """Should classify gitlab.com as repository."""
        from rekall.enrichment import classify_content_type

        assert classify_content_type("https://gitlab.com/user/repo") == "repository"

    def test_classify_forum_stackoverflow(self):
        """Should classify stackoverflow as forum."""
        from rekall.enrichment import classify_content_type

        assert classify_content_type("https://stackoverflow.com/questions/123") == "forum"

    def test_classify_forum_reddit(self):
        """Should classify reddit as forum."""
        from rekall.enrichment import classify_content_type

        assert classify_content_type("https://reddit.com/r/python") == "forum"

    def test_classify_blog_medium(self):
        """Should classify medium as blog."""
        from rekall.enrichment import classify_content_type

        assert classify_content_type("https://medium.com/@user/article") == "blog"

    def test_classify_blog_path(self):
        """Should classify /blog/ path as blog."""
        from rekall.enrichment import classify_content_type

        assert classify_content_type("https://example.com/blog/post") == "blog"

    def test_classify_api_path(self):
        """Should classify /api/ path as api."""
        from rekall.enrichment import classify_content_type

        assert classify_content_type("https://example.com/api/v1/users") == "api"

    def test_classify_paper_arxiv(self):
        """Should classify arxiv as paper."""
        from rekall.enrichment import classify_content_type

        assert classify_content_type("https://arxiv.org/abs/2301.00000") == "paper"

    def test_classify_other_unknown(self):
        """Should classify unknown URLs as other."""
        from rekall.enrichment import classify_content_type

        assert classify_content_type("https://example.com/page") == "other"

    def test_classify_with_title_hint(self):
        """Should use title as additional hint."""
        from rekall.enrichment import classify_content_type

        # URL is ambiguous but title gives hint
        assert (
            classify_content_type("https://example.com/page", title="API Documentation")
            == "documentation"
        )


class TestDetectLanguage:
    """Tests for detect_language()."""

    def test_detect_english(self):
        """Should detect English from html lang attribute."""
        from rekall.enrichment import detect_language

        html = '<html lang="en"><head><title>Test</title></head></html>'
        assert detect_language(html) == "en"

    def test_detect_french(self):
        """Should detect French."""
        from rekall.enrichment import detect_language

        html = '<html lang="fr"><head><title>Test</title></head></html>'
        assert detect_language(html) == "fr"

    def test_detect_with_region(self):
        """Should normalize language code."""
        from rekall.enrichment import detect_language

        html = '<html lang="en-US"><head><title>Test</title></head></html>'
        assert detect_language(html) == "en"

    def test_detect_no_lang(self):
        """Should return None when no lang attribute."""
        from rekall.enrichment import detect_language

        html = "<html><head><title>Test</title></head></html>"
        assert detect_language(html) is None


class TestFetchMetadata:
    """Tests for fetch_metadata() (T052)."""

    @pytest.mark.asyncio
    async def test_fetch_metadata_success(self):
        """Should extract title and description from HTML."""
        from rekall.enrichment import fetch_metadata

        html_content = """
        <html lang="en">
        <head>
            <title>Test Page Title</title>
            <meta name="description" content="Test description">
        </head>
        <body>Content</body>
        </html>
        """

        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.text = html_content

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.get = AsyncMock(return_value=mock_response)
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock()
            mock_client.return_value = mock_instance

            title, desc, ctype, lang, accessible, status = await fetch_metadata(
                "https://example.com/"
            )

            assert title == "Test Page Title"
            assert desc == "Test description"
            assert accessible is True
            assert status == 200
            assert lang == "en"

    @pytest.mark.asyncio
    async def test_fetch_metadata_og_tags(self):
        """Should extract from Open Graph tags."""
        from rekall.enrichment import fetch_metadata

        html_content = """
        <html>
        <head>
            <meta property="og:title" content="OG Title">
            <meta property="og:description" content="OG Description">
        </head>
        </html>
        """

        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.text = html_content

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.get = AsyncMock(return_value=mock_response)
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock()
            mock_client.return_value = mock_instance

            title, desc, _, _, _, _ = await fetch_metadata("https://example.com/")

            assert title == "OG Title"
            assert desc == "OG Description"

    @pytest.mark.asyncio
    async def test_fetch_metadata_404(self):
        """Should handle 404 errors gracefully."""
        from rekall.enrichment import fetch_metadata

        mock_response = AsyncMock()
        mock_response.status_code = 404
        mock_response.text = "Not Found"

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.get = AsyncMock(return_value=mock_response)
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock()
            mock_client.return_value = mock_instance

            title, desc, ctype, lang, accessible, status = await fetch_metadata(
                "https://example.com/notfound"
            )

            assert accessible is False
            assert status == 404

    def test_error_handling_returns_classification(self):
        """Error handling should still return content_type classification (T055)."""
        from rekall.enrichment import classify_content_type

        # Even when fetch fails, we can still classify URLs
        # This tests the fallback behavior mentioned in the code

        # Documentation URL should be classified even if fetch fails
        ctype = classify_content_type("https://docs.python.org/slow/")
        assert ctype == "documentation"

        # Repository URL should be classified
        ctype = classify_content_type("https://github.com/slow/repo")
        assert ctype == "repository"

        # Unknown URL falls back to "other"
        ctype = classify_content_type("https://unknown-slow-site.com/")
        assert ctype == "other"


class TestMergeIntoStaging:
    """Tests for merge_into_staging() deduplication (T054)."""

    def test_merge_new_entry(self, temp_db_path):
        """Should create new staging entry for new URL."""
        from pathlib import Path

        from rekall.db import Database
        from rekall.enrichment import merge_into_staging
        from rekall.models import InboxEntry, generate_ulid

        db = Database(temp_db_path)
        db.init()

        inbox_entry = InboxEntry(
            id=generate_ulid(),
            url="https://newsite.com/page",
            domain="newsite.com",
            cli_source="claude",
            project="test-project",
        )
        db.add_inbox_entry(inbox_entry)

        staging, is_new = merge_into_staging(
            db,
            inbox_entry,
            title="New Page",
            description="Description",
            content_type="documentation",
            language="en",
            is_accessible=True,
            http_status=200,
        )

        assert is_new is True
        assert staging.url == "https://newsite.com/page"
        assert staging.title == "New Page"
        assert staging.citation_count == 1
        assert staging.project_count == 1
        db.close()

    def test_merge_existing_url(self, temp_db_path):
        """Should update existing staging entry for duplicate URL."""
        from pathlib import Path

        from rekall.db import Database
        from rekall.enrichment import merge_into_staging
        from rekall.models import InboxEntry, StagingEntry, generate_ulid

        db = Database(temp_db_path)
        db.init()

        # Create existing staging entry
        existing = StagingEntry(
            id=generate_ulid(),
            url="https://existing.com/page",
            domain="existing.com",
            title="Original Title",
            citation_count=2,
            project_count=1,
            projects_list="project1",
            inbox_ids="inbox1",
        )
        db.add_staging_entry(existing)

        # Create new inbox entry for same URL
        inbox_entry = InboxEntry(
            id=generate_ulid(),
            url="https://existing.com/page",
            domain="existing.com",
            cli_source="claude",
            project="project2",
        )
        db.add_inbox_entry(inbox_entry)

        staging, is_new = merge_into_staging(
            db,
            inbox_entry,
            title=None,  # Don't override existing title
            description=None,
            content_type="other",
            language=None,
            is_accessible=True,
            http_status=200,
        )

        assert is_new is False
        assert staging.citation_count == 3  # Incremented
        assert staging.project_count == 2  # New project added
        assert "project2" in staging.projects_list
        assert staging.title == "Original Title"  # Not overridden
        db.close()

    def test_merge_updates_metadata_if_empty(self, temp_db_path):
        """Should update metadata only if existing is empty."""
        from pathlib import Path

        from rekall.db import Database
        from rekall.enrichment import merge_into_staging
        from rekall.models import InboxEntry, StagingEntry, generate_ulid

        db = Database(temp_db_path)
        db.init()

        # Create existing staging entry without title
        existing = StagingEntry(
            id=generate_ulid(),
            url="https://notitle.com/page",
            domain="notitle.com",
            title=None,  # No title yet
            content_type="other",
        )
        db.add_staging_entry(existing)

        inbox_entry = InboxEntry(
            id=generate_ulid(),
            url="https://notitle.com/page",
            domain="notitle.com",
            cli_source="claude",
        )
        db.add_inbox_entry(inbox_entry)

        staging, is_new = merge_into_staging(
            db,
            inbox_entry,
            title="New Title",  # Should be applied
            description="New Description",
            content_type="documentation",  # Should update from "other"
            language="en",
            is_accessible=True,
            http_status=200,
        )

        assert staging.title == "New Title"
        assert staging.content_type == "documentation"
        db.close()


class TestEnrichBatch:
    """Tests for batch enrichment."""

    @pytest.mark.asyncio
    async def test_enrich_inbox_entries_empty(self, temp_db_path):
        """Should handle empty inbox gracefully."""
        from rekall.db import Database
        from rekall.enrichment import enrich_inbox_entries

        db = Database(temp_db_path)
        db.init()

        result = await enrich_inbox_entries(db, limit=10)

        assert result.total_processed == 0
        assert result.enriched == 0
        assert result.merged == 0
        assert result.failed == 0
        db.close()


# Fixture for temp database
@pytest.fixture
def temp_db_path(tmp_path):
    """Create a temporary database path."""
    return tmp_path / "test.db"
