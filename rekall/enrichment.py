"""URL enrichment module for Sources Medallion.

This module handles the Bronze → Silver transformation:
- Fetches metadata from URLs (title, description)
- Classifies content type (documentation, repository, forum, etc.)
- Detects language
- Merges duplicate URLs into staging entries
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from rekall.db import Database
    from rekall.models import InboxEntry, StagingEntry


@dataclass
class EnrichmentResult:
    """Result of enriching a single URL."""

    success: bool
    staging_id: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    content_type: Optional[str] = None
    language: Optional[str] = None
    is_accessible: bool = True
    http_status: Optional[int] = None
    error: Optional[str] = None
    is_new: bool = True  # False if merged into existing staging entry


@dataclass
class BatchEnrichmentResult:
    """Result of batch enrichment."""

    total_processed: int = 0
    enriched: int = 0
    merged: int = 0
    failed: int = 0
    errors: list[str] = None

    def __post_init__(self):
        if self.errors is None:
            self.errors = []


# Domain patterns for content type classification
CONTENT_TYPE_PATTERNS = {
    "documentation": [
        r"docs\.",
        r"\.readthedocs\.",
        r"developer\.",
        r"devdocs\.",
        r"api\.",
        r"/docs/",
        r"/documentation/",
        r"/reference/",
        r"/guide/",
        r"/manual/",
    ],
    "repository": [
        r"github\.com",
        r"gitlab\.com",
        r"bitbucket\.org",
        r"codeberg\.org",
        r"sr\.ht",
        r"gitea\.",
    ],
    "forum": [
        r"stackoverflow\.com",
        r"stackexchange\.com",
        r"reddit\.com",
        r"news\.ycombinator\.com",
        r"discourse\.",
        r"discuss\.",
        r"/forum/",
        r"/community/",
    ],
    "blog": [
        r"medium\.com",
        r"dev\.to",
        r"hashnode\.dev",
        r"substack\.com",
        r"/blog/",
        r"/posts/",
        r"/articles/",
    ],
    "api": [
        r"/api/",
        r"/v1/",
        r"/v2/",
        r"/v3/",
        r"api\.",
        r"/swagger",
        r"/openapi",
    ],
    "paper": [
        r"arxiv\.org",
        r"papers\.nips\.cc",
        r"aclanthology\.org",
        r"semanticscholar\.org",
        r"\.pdf$",
        r"/paper/",
    ],
}


def classify_content_type(url: str, title: Optional[str] = None) -> str:
    """Classify URL content type based on URL patterns.

    Args:
        url: URL to classify
        title: Optional page title for additional hints

    Returns:
        Content type string (documentation, repository, forum, blog, api, paper, other)
    """
    url_lower = url.lower()

    for content_type, patterns in CONTENT_TYPE_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, url_lower):
                return content_type

    # Additional title-based hints
    if title:
        title_lower = title.lower()
        if any(word in title_lower for word in ["documentation", "docs", "reference", "guide"]):
            return "documentation"
        if any(word in title_lower for word in ["api", "endpoint"]):
            return "api"

    return "other"


def detect_language(html: str) -> Optional[str]:
    """Detect language from HTML lang attribute.

    Args:
        html: HTML content

    Returns:
        ISO 639-1 language code (e.g., 'en', 'fr') or None
    """
    # Look for lang attribute in html tag
    match = re.search(r'<html[^>]*\slang=["\']([a-zA-Z-]+)["\']', html, re.IGNORECASE)
    if match:
        lang = match.group(1).lower()
        # Normalize to 2-letter code
        return lang.split("-")[0]

    return None


async def fetch_metadata(
    url: str,
    timeout: float = 10.0,
) -> tuple[Optional[str], Optional[str], Optional[str], Optional[str], bool, Optional[int]]:
    """Fetch metadata from a URL.

    Args:
        url: URL to fetch
        timeout: Request timeout in seconds

    Returns:
        Tuple of (title, description, content_type, language, is_accessible, http_status)
    """
    try:
        import httpx
        from bs4 import BeautifulSoup
    except ImportError as e:
        raise ImportError(
            "httpx and beautifulsoup4 are required for enrichment. "
            "Install with: pip install httpx beautifulsoup4"
        ) from e

    title = None
    description = None
    content_type = None
    language = None
    is_accessible = True
    http_status = None

    try:
        async with httpx.AsyncClient(
            timeout=timeout,
            follow_redirects=True,
            headers={"User-Agent": "Rekall/1.0 (Knowledge Management)"},
        ) as client:
            response = await client.get(url)
            http_status = response.status_code

            if response.status_code >= 400:
                is_accessible = False
                content_type = classify_content_type(url)
                return title, description, content_type, language, is_accessible, http_status

            # Parse HTML
            html = response.text
            soup = BeautifulSoup(html, "html.parser")

            # Extract title
            if soup.title and soup.title.string:
                title = soup.title.string.strip()
            else:
                # Try og:title
                og_title = soup.find("meta", property="og:title")
                if og_title and og_title.get("content"):
                    title = og_title["content"].strip()

            # Extract description
            meta_desc = soup.find("meta", attrs={"name": "description"})
            if meta_desc and meta_desc.get("content"):
                description = meta_desc["content"].strip()
            else:
                # Try og:description
                og_desc = soup.find("meta", property="og:description")
                if og_desc and og_desc.get("content"):
                    description = og_desc["content"].strip()

            # Detect language
            language = detect_language(html)

            # Classify content type
            content_type = classify_content_type(url, title)

    except httpx.TimeoutException:
        is_accessible = False
        content_type = classify_content_type(url)
    except httpx.RequestError:
        is_accessible = False
        content_type = classify_content_type(url)
    except Exception:
        is_accessible = False
        content_type = classify_content_type(url)

    return title, description, content_type, language, is_accessible, http_status


def merge_into_staging(
    db: "Database",
    inbox_entry: "InboxEntry",
    title: Optional[str],
    description: Optional[str],
    content_type: Optional[str],
    language: Optional[str],
    is_accessible: bool,
    http_status: Optional[int],
) -> tuple["StagingEntry", bool]:
    """Merge inbox entry into staging, handling deduplication.

    If the URL already exists in staging, update counts and merge context.
    Otherwise, create a new staging entry.

    Args:
        db: Database instance
        inbox_entry: Source inbox entry
        title: Extracted title
        description: Extracted description
        content_type: Classified content type
        language: Detected language
        is_accessible: Whether URL was accessible
        http_status: HTTP status code

    Returns:
        Tuple of (StagingEntry, is_new) where is_new indicates if entry was created
    """
    from rekall.models import StagingEntry, generate_ulid

    existing = db.get_staging_by_url(inbox_entry.url)

    if existing:
        # Update existing entry
        existing.citation_count += 1
        existing.last_seen = datetime.now()

        # Add project to list if new
        if inbox_entry.project:
            projects = set(existing.projects_list.split(",") if existing.projects_list else [])
            if inbox_entry.project not in projects:
                projects.add(inbox_entry.project)
                existing.project_count = len(projects)
                existing.projects_list = ",".join(sorted(projects))

        # Update inbox_ids
        inbox_ids = set(existing.inbox_ids.split(",") if existing.inbox_ids else [])
        inbox_ids.add(inbox_entry.id)
        existing.inbox_ids = ",".join(sorted(inbox_ids))

        # Update metadata if better
        if title and not existing.title:
            existing.title = title
        if description and not existing.description:
            existing.description = description
        if content_type and existing.content_type == "other":
            existing.content_type = content_type
        if language and not existing.language:
            existing.language = language

        # Update accessibility
        existing.is_accessible = is_accessible
        existing.http_status = http_status
        existing.last_verified = datetime.now()

        db.update_staging(existing)
        return existing, False

    else:
        # Create new entry
        now = datetime.now()
        new_entry = StagingEntry(
            id=generate_ulid(),
            url=inbox_entry.url,
            domain=inbox_entry.domain,
            title=title,
            description=description,
            content_type=content_type or "other",
            language=language,
            last_verified=now,
            is_accessible=is_accessible,
            http_status=http_status,
            citation_count=1,
            project_count=1 if inbox_entry.project else 0,
            projects_list=inbox_entry.project or "",
            first_seen=inbox_entry.captured_at or now,
            last_seen=now,
            promotion_score=0.0,
            inbox_ids=inbox_entry.id,
            enriched_at=now,
        )
        db.add_staging_entry(new_entry)
        return new_entry, True


async def enrich_inbox_entry(
    db: "Database",
    inbox_entry: "InboxEntry",
    timeout: float = 10.0,
) -> EnrichmentResult:
    """Enrich a single inbox entry and move to staging.

    Args:
        db: Database instance
        inbox_entry: Inbox entry to enrich
        timeout: Request timeout

    Returns:
        EnrichmentResult with enrichment details
    """
    try:
        # Fetch metadata
        title, description, content_type, language, is_accessible, http_status = await fetch_metadata(
            inbox_entry.url, timeout
        )

        # Merge into staging
        staging_entry, is_new = merge_into_staging(
            db,
            inbox_entry,
            title,
            description,
            content_type,
            language,
            is_accessible,
            http_status,
        )

        # Mark inbox entry as enriched
        db.mark_inbox_enriched(inbox_entry.id)

        return EnrichmentResult(
            success=True,
            staging_id=staging_entry.id,
            title=title,
            description=description,
            content_type=content_type,
            language=language,
            is_accessible=is_accessible,
            http_status=http_status,
            is_new=is_new,
        )

    except Exception as e:
        return EnrichmentResult(
            success=False,
            error=str(e),
            is_accessible=False,
        )


async def enrich_inbox_entries(
    db: "Database",
    limit: int = 50,
    timeout: float = 10.0,
) -> BatchEnrichmentResult:
    """Enrich multiple inbox entries in batch.

    Args:
        db: Database instance
        limit: Maximum entries to process
        timeout: Request timeout per URL

    Returns:
        BatchEnrichmentResult with batch statistics
    """
    result = BatchEnrichmentResult()

    # Get pending entries
    entries = db.get_inbox_not_enriched(limit=limit)
    result.total_processed = len(entries)

    for entry in entries:
        enrichment = await enrich_inbox_entry(db, entry, timeout)

        if enrichment.success:
            if enrichment.is_new:
                result.enriched += 1
            else:
                result.merged += 1
        else:
            result.failed += 1
            if enrichment.error:
                result.errors.append(f"{entry.url}: {enrichment.error}")

    return result
