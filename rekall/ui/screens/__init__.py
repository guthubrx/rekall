# rekall/ui/screens/__init__.py
"""
TUI screens package.

This package contains Textual App screens for the Rekall TUI.

Current State (Facade Pattern):
    All screens currently live in tui_main.py. This package provides
    the module structure for future extraction.

Screens:
    - main.py: RekallMenuApp (main menu)
    - browse.py: BrowseApp (entry browser)
    - research.py: ResearchApp (research mode)
    - sources.py: SourcesBrowseApp (sources browser)
    - inbox.py: InboxBrowseApp (inbox browser)
    - staging.py: StagingBrowseApp (staging browser)
    - config.py: MCPConfigApp (MCP configuration)
"""

from __future__ import annotations

__all__: list[str] = []
