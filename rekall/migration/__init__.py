"""Rekall migration module for importing sources from external systems.

This module handles migration of sources from:
- Speckit research files (~/.speckit/research/*.md)
- Other potential source formats in the future
"""

from rekall.migration.speckit_parser import (
    extract_theme_from_filename,
    parse_research_file,
    scan_research_directory,
)

__all__ = [
    "parse_research_file",
    "extract_theme_from_filename",
    "scan_research_directory",
]
