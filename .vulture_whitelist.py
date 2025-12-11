# Vulture whitelist for false positives
# Add unused code that is actually used (e.g., via dynamic imports, CLI entry points)

# CLI entry point (called by typer)
from rekall.cli import app  # noqa: F401

# Pydantic validators are called by the framework
from rekall.validators import (
    EntryValidator,
    ConfigValidator,
    ArchiveValidator,
)

# These are intentionally exported
EntryValidator.validate_tags
EntryValidator.validate_title

# MCP server entry point (external invocation)
from rekall.mcp_server import main  # noqa: F401
