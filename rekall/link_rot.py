"""Link rot detection for Rekall sources (Feature 009 - US6)."""

from __future__ import annotations

import http.client
import socket
from datetime import datetime
from typing import TYPE_CHECKING
from urllib.parse import urlparse

if TYPE_CHECKING:
    from rekall.db import Database


class LinkRotChecker:
    """Checks URL accessibility for sources."""

    def __init__(self, timeout: int = 10):
        """Initialize the checker.

        Args:
            timeout: HTTP request timeout in seconds
        """
        self.timeout = timeout

    def check_url_accessibility(self, url: str) -> tuple[bool, str]:
        """Check if a URL is accessible using HTTP HEAD request.

        Uses stdlib only - no external dependencies.

        Args:
            url: URL to check

        Returns:
            Tuple of (is_accessible, status_message)
        """
        try:
            # Parse URL
            parsed = urlparse(url)
            if not parsed.netloc:
                return False, "Invalid URL: no host"

            # Choose connection type
            port = parsed.port
            if parsed.scheme == "https":
                conn = http.client.HTTPSConnection(
                    parsed.netloc,
                    port=port or 443,
                    timeout=self.timeout,
                )
            else:
                conn = http.client.HTTPConnection(
                    parsed.netloc,
                    port=port or 80,
                    timeout=self.timeout,
                )

            # Build path
            path = parsed.path or "/"
            if parsed.query:
                path += f"?{parsed.query}"

            try:
                # Send HEAD request (lightweight, no body download)
                conn.request(
                    "HEAD",
                    path,
                    headers={
                        "User-Agent": "Rekall-LinkChecker/1.0",
                        "Accept": "*/*",
                    },
                )
                response = conn.getresponse()

                # Check status code
                status = response.status

                if 200 <= status < 400:
                    return True, f"OK ({status})"
                elif status == 403:
                    # Some sites block HEAD requests but are accessible
                    return True, f"Forbidden but likely OK ({status})"
                elif status == 404:
                    return False, f"Not Found ({status})"
                elif status == 410:
                    return False, f"Gone ({status})"
                elif 500 <= status < 600:
                    return False, f"Server Error ({status})"
                else:
                    return False, f"HTTP {status}"

            finally:
                conn.close()

        except socket.timeout:
            return False, "Timeout"
        except socket.gaierror as e:
            return False, f"DNS Error: {e}"
        except http.client.HTTPException as e:
            return False, f"HTTP Error: {e}"
        except OSError as e:
            return False, f"Connection Error: {e}"
        except Exception as e:
            return False, f"Unknown Error: {e}"

    def check_source(self, url_pattern: str, domain: str) -> tuple[bool, str]:
        """Check if a source's base URL is accessible.

        Constructs a test URL from domain and optional pattern.

        Args:
            url_pattern: URL pattern (e.g., "/questions/*")
            domain: Domain (e.g., "stackoverflow.com")

        Returns:
            Tuple of (is_accessible, status_message)
        """
        # Build test URL
        if url_pattern:
            # Use pattern prefix for checking
            # e.g., "/questions/*" -> "/questions/"
            path = url_pattern.rstrip("*").rstrip("/") + "/"
        else:
            path = "/"

        url = f"https://{domain}{path}"
        return self.check_url_accessibility(url)


<<<<<<< HEAD
def verify_sources(db: Database, limit: int = 100) -> dict:
=======
def verify_sources(
    db: "Database",
    limit: int = 100,
    on_progress: callable | None = None,
    days_since_check: int = 1,
) -> dict:
>>>>>>> 015-mcp-tools-expansion
    """Verify accessibility of sources and update their status.

    Args:
        db: Database instance
        limit: Maximum sources to verify in one run
        on_progress: Optional callback(current, total, domain) for progress updates
        days_since_check: Minimum days since last check (0 = force re-check all)

    Returns:
        Dictionary with verification results
    """
    checker = LinkRotChecker()

    # Get sources to verify
    sources = db.get_sources_to_verify(days_since_check=days_since_check, limit=limit)
    total = len(sources)

    results = {
        "verified": 0,
        "accessible": 0,
        "inaccessible": 0,
        "errors": [],
    }

    for i, source in enumerate(sources):
        # Only check URL-based sources
        if not source.domain:
            if on_progress:
                on_progress(i + 1, total, "(skipped)")
            continue

        # Progress callback before check
        if on_progress:
            on_progress(i + 1, total, source.domain)

        is_accessible, message = checker.check_source(
            source.url_pattern or "",
            source.domain,
        )

        # Update status
        new_status = "active" if is_accessible else "inaccessible"
        db.update_source_status(
            source.id,
            status=new_status,
            last_verified=datetime.now(),
        )

        results["verified"] += 1
        if is_accessible:
            results["accessible"] += 1
        else:
            results["inaccessible"] += 1
            results["errors"].append({
                "source_id": source.id,
                "domain": source.domain,
                "message": message,
            })

    return results
