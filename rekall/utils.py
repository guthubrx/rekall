"""Utility functions for Rekall (Feature 009 - Sources Integration)."""

from __future__ import annotations

from urllib.parse import urlparse


def extract_domain(url: str) -> str:
    """Extract domain from a URL.

    Handles various URL formats and normalizes the result.

    Args:
        url: URL to extract domain from (can be with or without scheme)

    Returns:
        Normalized domain (e.g., "stackoverflow.com")

    Examples:
        >>> extract_domain("https://stackoverflow.com/questions/123")
        'stackoverflow.com'
        >>> extract_domain("docs.python.org/3/library/")
        'docs.python.org'
        >>> extract_domain("http://www.example.com:8080/path")
        'www.example.com'
    """
    # Handle URLs without scheme
    if not url.startswith(("http://", "https://", "//")):
        url = "https://" + url

    parsed = urlparse(url)

    # Get hostname (without port)
    domain = parsed.netloc or parsed.path.split("/")[0]

    # Remove port if present
    if ":" in domain:
        domain = domain.split(":")[0]

    # Remove leading www. for consistency (optional, configurable)
    # Note: We keep www. to distinguish www.example.com from api.example.com
    # If you want to strip www., uncomment:
    # if domain.startswith("www."):
    #     domain = domain[4:]

    return domain.lower()


def normalize_url(url: str) -> str:
    """Normalize a URL for consistent storage and comparison.

    Performs the following normalizations:
    - Ensures https:// scheme (upgrades http://)
    - Lowercases domain
    - Removes trailing slashes from path
    - Removes common tracking parameters
    - Keeps path and essential query parameters

    Args:
        url: URL to normalize

    Returns:
        Normalized URL string

    Examples:
        >>> normalize_url("http://Example.com/Path/")
        'https://example.com/Path'
        >>> normalize_url("stackoverflow.com/questions/123")
        'https://stackoverflow.com/questions/123'
    """
    # Handle URLs without scheme
    if not url.startswith(("http://", "https://", "//")):
        url = "https://" + url
    elif url.startswith("//"):
        url = "https:" + url
    elif url.startswith("http://"):
        # Upgrade to https
        url = "https://" + url[7:]

    parsed = urlparse(url)

    # Normalize domain (lowercase)
    domain = parsed.netloc.lower()

    # Remove port if it's default (443 for https, 80 for http)
    if domain.endswith(":443"):
        domain = domain[:-4]
    elif domain.endswith(":80"):
        domain = domain[:-3]

    # Normalize path - remove trailing slash but keep root /
    path = parsed.path
    if path != "/" and path.endswith("/"):
        path = path.rstrip("/")

    # Keep query parameters but filter out common trackers
    tracking_params = {
        "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
        "fbclid", "gclid", "ref", "source", "mc_cid", "mc_eid",
    }

    query = parsed.query
    if query:
        # Parse and filter query parameters
        params = []
        for param in query.split("&"):
            if "=" in param:
                key = param.split("=")[0]
                if key.lower() not in tracking_params:
                    params.append(param)
            else:
                params.append(param)
        query = "&".join(params)

    # Reconstruct URL
    result = f"https://{domain}{path}"
    if query:
        result += f"?{query}"

    return result


def is_valid_url(url: str) -> bool:
    """Check if a string is a valid URL.

    Args:
        url: String to check

    Returns:
        True if valid URL, False otherwise

    Examples:
        >>> is_valid_url("https://example.com")
        True
        >>> is_valid_url("not a url")
        False
        >>> is_valid_url("example.com/path")
        True
    """
    # Add scheme if missing for validation
    test_url = url
    if not test_url.startswith(("http://", "https://", "//")):
        test_url = "https://" + test_url

    try:
        parsed = urlparse(test_url)
        # Must have netloc (domain) and it must contain a dot
        return bool(parsed.netloc) and "." in parsed.netloc
    except Exception:
        return False


def extract_url_pattern(url: str) -> str | None:
    """Extract a URL pattern from a specific URL.

    Used to group similar URLs under the same source.
    For example, all Stack Overflow questions can share one source.

    Args:
        url: Specific URL

    Returns:
        Pattern string or None if no pattern detected

    Examples:
        >>> extract_url_pattern("https://stackoverflow.com/questions/12345/title")
        '/questions/*'
        >>> extract_url_pattern("https://docs.python.org/3/library/json.html")
        '/3/library/*'
        >>> extract_url_pattern("https://example.com/")
        None
    """
    parsed = urlparse(normalize_url(url))
    path = parsed.path

    # Skip if no meaningful path
    if not path or path == "/":
        return None

    # Common patterns for popular sites
    patterns = {
        "stackoverflow.com": _extract_so_pattern,
        "github.com": _extract_github_pattern,
        "docs.python.org": _extract_python_docs_pattern,
        "developer.mozilla.org": _extract_mdn_pattern,
    }

    domain = parsed.netloc
    if domain in patterns:
        return patterns[domain](path)

    # Generic pattern: keep first 2 path segments, wildcard the rest
    segments = [s for s in path.split("/") if s]
    if len(segments) > 2:
        return "/" + "/".join(segments[:2]) + "/*"

    return None


def _extract_so_pattern(path: str) -> str | None:
    """Extract Stack Overflow URL pattern."""
    # /questions/123/title -> /questions/*
    if path.startswith("/questions/"):
        return "/questions/*"
    # /a/123 -> /a/*
    if path.startswith("/a/"):
        return "/a/*"
    return None


def _extract_github_pattern(path: str) -> str | None:
    """Extract GitHub URL pattern."""
    segments = [s for s in path.split("/") if s]
    if len(segments) >= 2:
        # /owner/repo/... -> /owner/repo/*
        return f"/{segments[0]}/{segments[1]}/*"
    return None


def _extract_python_docs_pattern(path: str) -> str | None:
    """Extract Python docs URL pattern."""
    segments = [s for s in path.split("/") if s]
    if len(segments) >= 2:
        # /3/library/json.html -> /3/library/*
        return f"/{segments[0]}/{segments[1]}/*"
    return None


def _extract_mdn_pattern(path: str) -> str | None:
    """Extract MDN URL pattern."""
    # /en-US/docs/Web/JavaScript/Reference/... -> /en-US/docs/*
    if "/docs/" in path:
        idx = path.index("/docs/")
        lang = path[:idx]
        return f"{lang}/docs/*"
    return None
