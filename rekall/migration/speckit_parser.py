"""Parser for Speckit research files.

Extracts URLs and domains from markdown files in ~/.speckit/research/
and prepares them for import as seed sources.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse


@dataclass
class ParsedSource:
    """A source extracted from a speckit research file."""

    domain: str
    url: Optional[str] = None
    url_pattern: Optional[str] = None
    theme: str = ""
    origin_file: str = ""
    line_number: int = 0


@dataclass
class ParseResult:
    """Result of parsing a research file."""

    file_path: str
    theme: str
    sources: list[ParsedSource] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


# Regex patterns for URL extraction
URL_PATTERN = re.compile(
    r"https?://[^\s\)\]\>\"\'\,]+",
    re.IGNORECASE
)

# Pattern to extract domain from URL
DOMAIN_PATTERN = re.compile(
    r"^(?:https?://)?(?:www\.)?([^/\s]+)",
    re.IGNORECASE
)


def extract_domain(url: str) -> Optional[str]:
    """Extract domain from a URL.

    Args:
        url: Full URL string

    Returns:
        Domain without www prefix, or None if invalid
    """
    try:
        parsed = urlparse(url)
        domain = parsed.netloc or parsed.path.split("/")[0]
        # Remove www. prefix
        if domain.startswith("www."):
            domain = domain[4:]
        # Basic validation
        if "." in domain and len(domain) > 3:
            return domain.lower()
    except Exception:
        pass
    return None


def extract_url_pattern(url: str) -> Optional[str]:
    """Extract a URL pattern from a full URL.

    Converts specific URLs to patterns with wildcards.
    Example: https://docs.python.org/3/library/re.html -> /3/library/*

    Args:
        url: Full URL string

    Returns:
        URL pattern or None
    """
    try:
        parsed = urlparse(url)
        path = parsed.path
        if path and path != "/":
            # Simplify path: keep first 2 segments, wildcard the rest
            segments = [s for s in path.split("/") if s]
            if len(segments) >= 2:
                return f"/{segments[0]}/{segments[1]}/*"
            elif segments:
                return f"/{segments[0]}/*"
        return None
    except Exception:
        return None


def extract_theme_from_filename(filename: str) -> str:
    """Extract theme name from a speckit research filename.

    Speckit files follow pattern: NN-theme-name.md
    Example: 01-ai-agents.md -> ai-agents
             06-security.md -> security

    Args:
        filename: Name of the file (with or without path)

    Returns:
        Theme name in kebab-case
    """
    # Get just the filename
    name = Path(filename).stem

    # Remove leading number prefix (e.g., "01-", "06-")
    # Pattern: digits followed by dash or underscore
    theme = re.sub(r"^\d+[-_]", "", name)

    # Normalize: replace underscores with dashes, lowercase
    theme = theme.replace("_", "-").lower()

    # Remove any remaining non-kebab characters
    theme = re.sub(r"[^a-z0-9-]", "", theme)

    return theme or "uncategorized"


def parse_research_file(file_path: Path) -> ParseResult:
    """Parse a speckit research markdown file for URLs and domains.

    Extracts all URLs from the file content and deduplicates by domain.

    Args:
        file_path: Path to the markdown file

    Returns:
        ParseResult with extracted sources and any errors
    """
    result = ParseResult(
        file_path=str(file_path),
        theme=extract_theme_from_filename(file_path.name),
    )

    if not file_path.exists():
        result.errors.append(f"File not found: {file_path}")
        return result

    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception as e:
        result.errors.append(f"Error reading file: {e}")
        return result

    # Track domains to deduplicate
    seen_domains: dict[str, ParsedSource] = {}

    for line_num, line in enumerate(content.split("\n"), start=1):
        # Find all URLs in this line
        urls = URL_PATTERN.findall(line)

        for url in urls:
            # Clean URL (remove trailing punctuation)
            url = url.rstrip(".,;:!?)")

            domain = extract_domain(url)
            if not domain:
                continue

            # Skip if we already have this domain
            if domain in seen_domains:
                continue

            pattern = extract_url_pattern(url)

            source = ParsedSource(
                domain=domain,
                url=url,
                url_pattern=pattern,
                theme=result.theme,
                origin_file=str(file_path),
                line_number=line_num,
            )
            seen_domains[domain] = source

    result.sources = list(seen_domains.values())
    return result


def scan_research_directory(
    directory: Optional[Path] = None,
    pattern: str = "*.md"
) -> list[ParseResult]:
    """Scan a directory for research markdown files and parse them.

    Args:
        directory: Path to research directory (default: ~/.speckit/research/)
        pattern: Glob pattern for files (default: *.md)

    Returns:
        List of ParseResult for each file found
    """
    if directory is None:
        directory = Path.home() / ".speckit" / "research"

    if not directory.exists():
        return []

    results = []
    for file_path in sorted(directory.glob(pattern)):
        if file_path.is_file():
            result = parse_research_file(file_path)
            results.append(result)

    return results
