# rekall/tui.py
"""
TUI facade for backward compatibility.

This module re-exports from rekall.tui_main to maintain backward compatibility
with existing imports like `from rekall.tui import run_tui`.

Architecture:
    - rekall.tui (this file): Compatibility facade
    - rekall.tui_main: Original monolithic TUI implementation
    - rekall.ui: New modular TUI package (future structure)

Usage (all equivalent):
    from rekall.tui import run_tui  # Legacy import (this facade)
    from rekall.ui import run_tui   # New import (recommended)
"""

from __future__ import annotations

# Re-export everything from tui_main for backward compatibility
from rekall.tui_main import (
    BrowseApp,
    InboxBrowseApp,
    MCPConfigApp,
    MigrationOverlayApp,
    RekallMenuApp,
    ResearchApp,
    SourcesBrowseApp,
    StagingBrowseApp,
    apply_migration_from_tui,
    check_migration_needed,
    get_changelog_content,
    run_inbox_browser,
    run_migration_overlay,
    run_staging_browser,
    run_tui,
)

__all__ = [
    "BrowseApp",
    "InboxBrowseApp",
    "MCPConfigApp",
    "MigrationOverlayApp",
    "RekallMenuApp",
    "ResearchApp",
    "SourcesBrowseApp",
    "StagingBrowseApp",
    "apply_migration_from_tui",
    "check_migration_needed",
    "get_changelog_content",
    "run_inbox_browser",
    "run_migration_overlay",
    "run_staging_browser",
    "run_tui",
]
