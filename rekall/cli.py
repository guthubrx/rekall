"""Rekall CLI - Developer Knowledge Management System."""

from __future__ import annotations

import platform
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Optional

import typer
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from rekall import __version__
from rekall.config import get_config
from rekall.db import Database
from rekall.models import (
    VALID_MEMORY_TYPES,
    VALID_RELATION_TYPES,
    VALID_TYPES,
    Entry,
    generate_ulid,
)

console = Console()

# ASCII Banner - REKALL (Total Recall reference)
BANNER = """\
[bold cyan]        ██████╗ ███████╗██╗  ██╗ █████╗ ██╗     ██╗
        ██╔══██╗██╔════╝██║ ██╔╝██╔══██╗██║     ██║
        ██████╔╝█████╗  █████╔╝ ███████║██║     ██║
        ██╔══██╗██╔══╝  ██╔═██╗ ██╔══██║██║     ██║
        ██║  ██║███████╗██║  ██╗██║  ██║███████╗███████╗
        ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝╚══════╝[/bold cyan]

[bold white]            Developer Knowledge Management System[/bold white]
[dim]        "Get your ass to Mars. Quaid... crush those bugs"[/dim]
"""


def show_banner():
    """Display the REKALL banner."""
    console.print(BANNER)


# Create Typer app with Rich markup
app = typer.Typer(
    name="rekall",
    help="Capture and retrieve bugs, patterns, and decisions.",
    add_completion=False,
    rich_markup_mode="rich",
    pretty_exceptions_show_locals=False,
)

# Database instance (lazy loaded)
_db: Optional[Database] = None


def get_db() -> Database:
    """Get or create database connection."""
    global _db
    if _db is None:
        config = get_config()
        _db = Database(config.db_path)
        _db.init()
    return _db


# Global CLI options stored in context
_cli_global: bool = False
_cli_legacy: bool = False


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    use_global: bool = typer.Option(
        False,
        "--global",
        "-g",
        help="Force global configuration (ignore local .rekall/)",
    ),
    use_legacy: bool = typer.Option(
        False,
        "--legacy",
        help="Use legacy ~/.rekall/ path (compatibility mode)",
    ),
):
    """Rekall - Developer Knowledge Management System."""
    global _cli_global, _cli_legacy
    _cli_global = use_global
    _cli_legacy = use_legacy

    # Only reset config if CLI flags are used (allows test injection)
    if use_legacy or use_global:
        from rekall.config import reset_config
        reset_config()

    # Apply legacy mode if requested
    if use_legacy:
        from pathlib import Path

        from rekall.paths import PathSource, ResolvedPaths

        legacy_path = Path.home() / ".rekall"
        paths = ResolvedPaths(
            config_dir=legacy_path,
            data_dir=legacy_path,
            cache_dir=legacy_path / "cache",
            db_path=legacy_path / "knowledge.db",
            source=PathSource.CLI,
        )
        from rekall.config import Config, set_config
        set_config(Config(paths=paths))
    elif use_global:
        # Force global config (skip local project detection)
        from rekall.config import Config, set_config
        from rekall.paths import PathResolver
        paths = PathResolver.resolve(force_global=True)
        set_config(Config(paths=paths))

    if ctx.invoked_subcommand is None:
        # Launch interactive TUI
        from rekall.tui import run_tui
        run_tui()


# ============================================================================
# Version Command (like specify)
# ============================================================================


@app.command()
def version():
    """Display version and system information."""
    show_banner()

    # Build info table
    info_table = Table(show_header=False, box=None, padding=(0, 4))
    info_table.add_column("Label", style="dim", justify="right", width=20)
    info_table.add_column("Value", style="bold")

    info_table.add_row("CLI Version", __version__)
    info_table.add_row("Python", platform.python_version())
    info_table.add_row("Platform", platform.system())
    info_table.add_row("Architecture", platform.machine())

    # Get OS version
    if platform.system() == "Darwin":
        os_version = platform.mac_ver()[0]
    elif platform.system() == "Windows":
        os_version = platform.win32_ver()[0]
    else:
        os_version = platform.release()
    info_table.add_row("OS Version", os_version)

    # Database info
    config = get_config()
    db_exists = config.db_path.exists()
    info_table.add_row("Database", str(config.db_path))
    info_table.add_row("DB Status", "[green]initialized[/green]" if db_exists else "[yellow]not initialized[/yellow]")

    console.print(Panel(
        info_table,
        title="REKALL CLI Information",
        border_style="cyan",
        padding=(1, 2),
    ))


# ============================================================================
# Config Command (FR-007)
# ============================================================================


@app.command()
def config(
    show: bool = typer.Option(
        False,
        "--show",
        "-s",
        help="Display current configuration paths and sources",
    ),
):
    """Manage Rekall configuration.

    Display or modify configuration settings.

    Examples:
        rekall config --show    # Show all paths and their sources
    """
    import os

    if show:
        cfg = get_config()
        paths = cfg.paths

        console.print("[bold cyan]Configuration Rekall[/bold cyan]")
        console.print("─" * 40)
        console.print(f"[bold]Source:[/bold] {paths.source.value}")
        console.print()

        console.print("[bold]Chemins:[/bold]")
        console.print(f"  Config:  {paths.config_dir}")
        console.print(f"  Data:    {paths.data_dir}")
        console.print(f"  Cache:   {paths.cache_dir}")
        console.print(f"  DB:      {paths.db_path}")
        console.print()

        console.print("[bold]Variables d'environnement:[/bold]")
        rekall_home = os.environ.get("REKALL_HOME")
        xdg_config = os.environ.get("XDG_CONFIG_HOME")
        xdg_data = os.environ.get("XDG_DATA_HOME")

        console.print(f"  REKALL_HOME:     {rekall_home or '[dim](not set)[/dim]'}")
        console.print(f"  XDG_CONFIG_HOME: {xdg_config or '[dim](not set)[/dim]'}")
        console.print(f"  XDG_DATA_HOME:   {xdg_data or '[dim](not set)[/dim]'}")
        console.print()

        if paths.is_local_project:
            console.print("[bold]Projet local:[/bold] [green]Détecté (.rekall/)[/green]")
        else:
            console.print("[bold]Projet local:[/bold] [dim]Non détecté[/dim]")
    else:
        console.print("Use [cyan]rekall config --show[/cyan] to display configuration.")
        console.print("Use [cyan]rekall config --help[/cyan] for more options.")


# ============================================================================
# Init Command
# ============================================================================


@app.command()
def init(
    local: bool = typer.Option(
        False,
        "--local",
        "-l",
        help="Initialize in current directory as local project",
    ),
):
    """Initialize Rekall database.

    Creates the database file. By default uses XDG paths.
    Use --local to create .rekall/ in current directory for team sharing.

    Examples:
        rekall init           # Initialize with XDG paths
        rekall init --local   # Initialize .rekall/ in current directory
    """
    from rekall.paths import init_local_project

    if local:
        # Initialize local project
        local_dir = init_local_project()
        db_path = local_dir / "knowledge.db"
        db = Database(db_path)
        db.init()
        db.close()

        console.print(f"[green]✓[/green] Local project initialized: {local_dir}")
        console.print(f"  Database: {db_path}")
        console.print("  [dim]Add .rekall/ to Git to share with your team[/dim]")
    else:
        cfg = get_config()
        cfg.paths.ensure_dirs()
        db = Database(cfg.db_path)
        db.init()
        db.close()

        console.print(f"[green]✓[/green] Database initialized: {cfg.db_path}")


# ============================================================================
# Search Command (US1)
# ============================================================================


@app.command()
def search(
    query: str = typer.Argument(..., help="Search query"),
    entry_type: Optional[str] = typer.Option(
        None,
        "--type",
        "-t",
        help=f"Filter by type: {', '.join(VALID_TYPES)}",
    ),
    project: Optional[str] = typer.Option(
        None,
        "--project",
        "-p",
        help="Filter by project",
    ),
    memory_type: Optional[str] = typer.Option(
        None,
        "--memory-type",
        "-m",
        help=f"Filter by memory type: {', '.join(VALID_MEMORY_TYPES)}",
    ),
    limit: int = typer.Option(20, "--limit", "-l", help="Maximum results"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON for AI agents"),
):
    """Search knowledge base.

    Examples:
        rekall search "circular import"
        rekall search "cache" --type pattern
        rekall search "react" --project frontend
        rekall search "timeout" --memory-type semantic
        rekall search "auth" --json  # For AI agents
    """
    import json

    db = get_db()
    results = db.search(query, entry_type=entry_type, project=project, memory_type=memory_type, limit=limit)

    # JSON output for AI agents
    if json_output:
        output = {
            "query": query,
            "results": [],
            "total_count": len(results),
            "context_matches": {
                "project": project is not None,
                "type": entry_type,
                "memory_type": memory_type,
            }
        }

        for result in results:
            entry = result.entry
            # Get links for this entry
            outgoing = db.get_links(entry.id, direction="outgoing")
            incoming = db.get_links(entry.id, direction="incoming")

            entry_data = {
                "id": entry.id,
                "type": entry.type,
                "title": entry.title,
                "content": entry.content or "",
                "tags": list(entry.tags),
                "project": entry.project,
                "confidence": entry.confidence,
                "consolidation_score": entry.consolidation_score,
                "access_count": entry.access_count,
                "last_accessed": entry.last_accessed.isoformat() if entry.last_accessed else None,
                # BM25 rank: lower = more relevant, normalize to 0-1 score
                "relevance_score": round(min(1.0, max(0, 1 - result.rank / 10)), 2) if result.rank else 0.5,
                "links": {
                    "outgoing": [{"target_id": lnk.target_id, "type": lnk.relation_type} for lnk in outgoing],
                    "incoming": [{"source_id": lnk.source_id, "type": lnk.relation_type} for lnk in incoming],
                }
            }
            output["results"].append(entry_data)

        print(json.dumps(output, indent=2, ensure_ascii=False))
        return

    # Human-readable output
    if not results:
        console.print("[yellow]No results found.[/yellow]")
        return

    # Display results in a table
    table = Table(title=f"Search: {query}", show_header=True, header_style="bold", box=box.ROUNDED)
    table.add_column("ID", style="dim", width=12)
    table.add_column("Type", width=10)
    table.add_column("Title", min_width=30)
    table.add_column("Confidence", justify="center", width=10)
    table.add_column("Project", width=15)

    for result in results:
        entry = result.entry
        confidence_stars = "★" * entry.confidence + "☆" * (5 - entry.confidence)
        table.add_row(
            entry.id[:12] + "...",
            entry.type,
            entry.title,
            confidence_stars,
            entry.project or "-",
        )

    console.print(table)
    console.print(f"\n[dim]Found {len(results)} result(s)[/dim]")

    # Show "See also" - entries linked to results but not in results
    result_ids = {r.entry.id for r in results}
    see_also = set()

    for result in results:
        outgoing = db.get_links(result.entry.id, direction="outgoing")
        incoming = db.get_links(result.entry.id, direction="incoming")

        for link in outgoing:
            if link.target_id not in result_ids:
                see_also.add(link.target_id)
        for link in incoming:
            if link.source_id not in result_ids:
                see_also.add(link.source_id)

    if see_also:
        console.print("\n[bold]See also:[/bold]")
        for entry_id in list(see_also)[:5]:  # Limit to 5
            entry = db.get(entry_id, update_access=False)
            if entry:
                console.print(f"  → {entry_id[:12]}... \"{entry.title}\"")
        if len(see_also) > 5:
            console.print(f"  [dim]... and {len(see_also) - 5} more[/dim]")


# ============================================================================
# Add Command (US2)
# ============================================================================


@app.command()
def add(
    entry_type: str = typer.Argument(
        ...,
        help=f"Entry type: {', '.join(VALID_TYPES)}",
    ),
    title: str = typer.Argument(..., help="Entry title"),
    tags: Optional[str] = typer.Option(
        None,
        "--tags",
        "-t",
        help="Comma-separated tags",
    ),
    project: Optional[str] = typer.Option(
        None,
        "--project",
        "-p",
        help="Project name",
    ),
    confidence: int = typer.Option(
        2,
        "--confidence",
        "-c",
        min=0,
        max=5,
        help="Confidence level (0-5)",
    ),
    content: Optional[str] = typer.Option(
        None,
        "--content",
        help="Entry content (markdown)",
    ),
    memory_type: str = typer.Option(
        "episodic",
        "--memory-type",
        "-m",
        help=f"Memory type: {', '.join(VALID_MEMORY_TYPES)}",
    ),
):
    """Add a new knowledge entry.

    Types: bug, pattern, decision, pitfall, config, reference
    Memory types: episodic (events/incidents), semantic (concepts/patterns)

    Examples:
        rekall add bug "Fix circular import" -t react,import -p my-project
        rekall add pattern "API error handling" -c 4 -m semantic
        rekall add decision "Use TypeScript" --content "Better type safety..."
    """
    # Validate type
    if entry_type not in VALID_TYPES:
        console.print(
            f"[red]Error: Invalid type '{entry_type}'[/red]\n"
            f"Valid types: {', '.join(VALID_TYPES)}"
        )
        raise typer.Exit(1)

    # Validate memory_type
    if memory_type not in VALID_MEMORY_TYPES:
        console.print(
            f"[red]Error: Invalid memory type '{memory_type}'[/red]\n"
            f"Valid types: {', '.join(VALID_MEMORY_TYPES)}"
        )
        raise typer.Exit(1)

    # Parse tags
    tag_list = []
    if tags:
        tag_list = [t.strip() for t in tags.split(",") if t.strip()]

    # Read content from stdin if not provided and stdin is not a tty
    entry_content = content or ""
    if not entry_content and not sys.stdin.isatty():
        entry_content = sys.stdin.read()

    # Create entry
    entry = Entry(
        id=generate_ulid(),
        title=title,
        type=entry_type,
        content=entry_content,
        project=project,
        tags=tag_list,
        confidence=confidence,
        memory_type=memory_type,
    )

    # Save to database
    db = get_db()
    db.add(entry)

    console.print(f"[green]✓[/green] Entry created: {entry.id}")
    console.print(f"  Type: {entry.type}")
    console.print(f"  Title: {entry.title}")
    if tag_list:
        console.print(f"  Tags: {', '.join(tag_list)}")
    if project:
        console.print(f"  Project: {project}")


# ============================================================================
# Show Command
# ============================================================================


@app.command()
def show(
    entry_id: str = typer.Argument(..., help="Entry ID (or prefix)"),
):
    """Show entry details.

    Example:
        rekall show 01ARZ3NDEK
    """
    db = get_db()

    # Try exact match first, then prefix match
    entry = db.get(entry_id)
    if entry is None:
        # Try prefix match
        all_entries = db.list_all(limit=1000)
        matches = [e for e in all_entries if e.id.startswith(entry_id)]
        if len(matches) == 1:
            entry = matches[0]
        elif len(matches) > 1:
            console.print(f"[yellow]Multiple entries match '{entry_id}':[/yellow]")
            for e in matches[:5]:
                console.print(f"  {e.id}: {e.title}")
            return
        else:
            console.print(f"[red]Entry not found: {entry_id}[/red]")
            raise typer.Exit(1)

    # Display entry
    confidence_stars = "★" * entry.confidence + "☆" * (5 - entry.confidence)

    panel_content = Text()
    panel_content.append("ID: ", style="bold")
    panel_content.append(f"{entry.id}\n")
    panel_content.append("Type: ", style="bold")
    panel_content.append(f"{entry.type}\n")
    panel_content.append("Confidence: ", style="bold")
    panel_content.append(f"{confidence_stars}\n")

    # Cognitive memory info
    panel_content.append("Memory: ", style="bold")
    panel_content.append(f"{entry.memory_type}\n")

    # Consolidation indicator
    score = entry.consolidation_score * 100
    if score >= 70:
        indicator = "🟢"
    elif score >= 30:
        indicator = "🟡"
    else:
        indicator = "🔴"
    bars = "█" * int(score / 10) + "░" * (10 - int(score / 10))
    panel_content.append("Consolidation: ", style="bold")
    panel_content.append(f"{indicator} {bars} {score:.0f}%\n")

    # Access info
    panel_content.append("Access: ", style="bold")
    panel_content.append(f"{entry.access_count} times")
    if entry.last_accessed:
        days_ago = (datetime.now() - entry.last_accessed).days
        if days_ago == 0:
            panel_content.append(" │ Last: today\n")
        elif days_ago == 1:
            panel_content.append(" │ Last: yesterday\n")
        else:
            panel_content.append(f" │ Last: {days_ago} days ago\n")
    else:
        panel_content.append("\n")

    if entry.project:
        panel_content.append("Project: ", style="bold")
        panel_content.append(f"{entry.project}\n")
    if entry.tags:
        panel_content.append("Tags: ", style="bold")
        panel_content.append(f"{', '.join(entry.tags)}\n")
    panel_content.append("Created: ", style="bold")
    panel_content.append(f"{entry.created_at.strftime('%Y-%m-%d %H:%M')}\n")
    if entry.status == "obsolete":
        panel_content.append("Status: ", style="bold")
        panel_content.append("OBSOLETE", style="red")
        if entry.superseded_by:
            panel_content.append(f" (replaced by {entry.superseded_by})")
        panel_content.append("\n")

    console.print(Panel(panel_content, title=entry.title, border_style="cyan"))

    if entry.content:
        console.print("\n[bold]Content:[/bold]")
        console.print(entry.content)

    # Show related entries
    outgoing = db.get_links(entry.id, direction="outgoing")
    incoming = db.get_links(entry.id, direction="incoming")

    if outgoing or incoming:
        console.print("\n[bold]Related:[/bold]")
        for link in outgoing:
            target = db.get(link.target_id, update_access=False)
            if target:
                console.print(f"  → [{link.relation_type}] {link.target_id[:12]}... \"{target.title}\"")
        for link in incoming:
            source = db.get(link.source_id, update_access=False)
            if source:
                console.print(f"  ← [{link.relation_type}] {link.source_id[:12]}... \"{source.title}\"")


# ============================================================================
# Browse Command
# ============================================================================


@app.command()
def browse(
    entry_type: Optional[str] = typer.Option(
        None,
        "--type",
        "-t",
        help=f"Filter by type: {', '.join(VALID_TYPES)}",
    ),
    project: Optional[str] = typer.Option(
        None,
        "--project",
        "-p",
        help="Filter by project",
    ),
    memory_type: Optional[str] = typer.Option(
        None,
        "--memory-type",
        "-m",
        help=f"Filter by memory type: {', '.join(VALID_MEMORY_TYPES)}",
    ),
    limit: int = typer.Option(20, "--limit", "-l", help="Maximum entries"),
):
    """Browse all entries.

    Examples:
        rekall browse
        rekall browse --type bug
        rekall browse --project my-project
        rekall browse --memory-type semantic
    """
    db = get_db()
    entries = db.list_all(entry_type=entry_type, project=project, memory_type=memory_type, limit=limit)

    if not entries:
        console.print("[yellow]No entries found.[/yellow]")
        return

    table = Table(title="Knowledge Base", show_header=True, header_style="bold", box=box.ROUNDED)
    table.add_column("ID", style="dim", width=12)
    table.add_column("Type", width=10)
    table.add_column("Title", min_width=30)
    table.add_column("Confidence", justify="center", width=10)
    table.add_column("Created", width=12)

    for entry in entries:
        confidence_stars = "★" * entry.confidence + "☆" * (5 - entry.confidence)
        table.add_row(
            entry.id[:12] + "...",
            entry.type,
            entry.title,
            confidence_stars,
            entry.created_at.strftime("%Y-%m-%d"),
        )

    console.print(table)
    console.print(f"\n[dim]Showing {len(entries)} entries[/dim]")


# ============================================================================
# Deprecate Command
# ============================================================================


@app.command()
def deprecate(
    entry_id: str = typer.Argument(..., help="Entry ID to deprecate"),
    replaced_by: Optional[str] = typer.Option(
        None,
        "--replaced-by",
        "-r",
        help="ID of the replacing entry",
    ),
):
    """Mark an entry as obsolete.

    Example:
        rekall deprecate 01ARZ3NDEK --replaced-by 01BRZ4NEFL
    """
    db = get_db()
    entry = db.get(entry_id)

    if entry is None:
        console.print(f"[red]Entry not found: {entry_id}[/red]")
        raise typer.Exit(1)

    entry.status = "obsolete"
    entry.superseded_by = replaced_by
    db.update(entry)

    console.print(f"[green]✓[/green] Entry marked as obsolete: {entry_id}")
    if replaced_by:
        console.print(f"  Replaced by: {replaced_by}")


# ============================================================================
# Install Command (US4 - IDE Integration)
# ============================================================================


@app.command()
def install(
    ide: Optional[str] = typer.Argument(
        None,
        help="IDE/Agent to install integration for",
    ),
    list_available: bool = typer.Option(
        False,
        "--list",
        "-l",
        help="List available integrations",
    ),
    global_install: bool = typer.Option(
        False,
        "--global",
        "-g",
        help="Install globally (in home directory) instead of locally",
    ),
):
    """Install IDE/Agent integration.

    Creates configuration files for your AI coding assistant.

    Examples:
        rekall install --list          # Show available integrations
        rekall install cursor          # Create .cursorrules (local)
        rekall install claude          # Create Claude Code skill (local)
        rekall install claude --global # Create Claude Code skill (global ~/.claude/)
        rekall install copilot         # Create Copilot instructions
    """
    from rekall import integrations

    # List mode
    if list_available or ide is None:
        available = integrations.get_available()

        table = Table(title="Available Integrations", show_header=True, header_style="bold", box=box.ROUNDED)
        table.add_column("Name", style="cyan", width=12)
        table.add_column("Description", min_width=25)
        table.add_column("Local", style="dim")
        table.add_column("Global", style="dim")

        for name, desc, local_target, global_target in available:
            table.add_row(name, desc, local_target, global_target or "—")

        console.print(table)
        console.print("\n[dim]Usage: rekall install <name> [--global][/dim]")
        return

    # Check if global install is supported
    if global_install and not integrations.supports_global(ide):
        console.print(f"[red]Error: '{ide}' does not support global installation[/red]")
        raise typer.Exit(1)

    # Install mode
    try:
        target_path = integrations.install(ide, Path.cwd(), global_install=global_install)
        location = "globally" if global_install else "locally"
        console.print(f"[green]✓[/green] Integration installed {location}: {ide}")
        console.print(f"  Created: {target_path}")
    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")

        # Show available options
        console.print("\n[yellow]Available integrations:[/yellow]")
        for name, desc, local_target, global_target in integrations.get_available():
            console.print(f"  [cyan]{name}[/cyan] - {desc}")

        raise typer.Exit(1)


# ============================================================================
# Research Command (US5 - Curated Research Sources)
# ============================================================================


def get_research_topics() -> dict[str, Path]:
    """Get available research topics from bundled files."""

    topics = {}

    # Try to find research files in package
    try:
        # Python 3.9+ way
        research_dir = Path(__file__).parent / "research"
        if research_dir.exists():
            for f in research_dir.glob("*.md"):
                if f.name == "README.md":
                    continue
                # Extract topic name from filename (e.g., "01-ai-agents-agentic-ai.md" -> "ai-agents")
                name = f.stem
                # Remove number prefix if present
                if name[:2].isdigit() and name[2] == "-":
                    name = name[3:]
                # Use full name for better matching
                full_topic = "-".join(name.split("-")[:2]) if "-" in name else name
                topics[full_topic] = f
    except Exception:
        pass

    return topics


@app.command()
def research(
    topic: Optional[str] = typer.Argument(
        None,
        help="Research topic to display",
    ),
    list_topics: bool = typer.Option(
        False,
        "--list",
        "-l",
        help="List available research topics",
    ),
):
    """Browse curated research sources.

    Access curated research documents on various development topics.

    Examples:
        rekall research --list           # Show available topics
        rekall research ai-agents        # Show AI agents research
        rekall research security         # Show security research
    """
    topics = get_research_topics()

    # List mode or no topic
    if list_topics or topic is None:
        table = Table(title="Available Research Topics", show_header=True, header_style="bold", box=box.ROUNDED)
        table.add_column("Topic", style="cyan", width=25)
        table.add_column("File", style="dim")

        for name, path in sorted(topics.items()):
            table.add_row(name, path.name)

        console.print(table)
        console.print("\n[dim]Usage: rekall research <topic>[/dim]")
        return

    # Find matching topic
    matching = None
    for name, path in topics.items():
        if topic.lower() in name.lower() or name.lower() in topic.lower():
            matching = (name, path)
            break

    if matching is None:
        console.print(f"[red]Error: Unknown topic '{topic}'[/red]")
        console.print("\n[yellow]Available topics:[/yellow]")
        for name in sorted(topics.keys()):
            console.print(f"  [cyan]{name}[/cyan]")
        raise typer.Exit(1)

    # Display content
    name, path = matching
    content = path.read_text()

    console.print(Panel(
        f"[bold]{name}[/bold]\n[dim]{path.name}[/dim]",
        border_style="cyan",
    ))
    console.print()
    console.print(content)


# ============================================================================
# Similar Command (US6 - Semantic Search with FTS Fallback)
# ============================================================================


@app.command()
def similar(
    query: str = typer.Argument(..., help="Query to find similar entries"),
    limit: int = typer.Option(10, "--limit", "-l", help="Maximum results"),
):
    """Find semantically similar entries.

    Uses embeddings when configured, falls back to FTS otherwise.

    Examples:
        rekall similar "error handling patterns"
        rekall similar "authentication flow" -l 5
    """
    config = get_config()
    db = get_db()

    # Check if embeddings provider is configured
    has_embeddings = config.embeddings_provider is not None

    if has_embeddings:
        # TODO: Implement actual embedding-based search
        # For now, just note that it would use embeddings
        console.print("[dim]Using embeddings provider: {config.embeddings_provider}[/dim]")
    else:
        console.print("[dim]No embeddings provider configured, using FTS fallback[/dim]")

    # Fallback to FTS search
    results = db.search(query, limit=limit)

    if not results:
        console.print("[yellow]No similar entries found.[/yellow]")
        return

    # Display results
    table = Table(title=f"Similar to: {query}", show_header=True, header_style="bold", box=box.ROUNDED)
    table.add_column("ID", style="dim", width=12)
    table.add_column("Type", width=10)
    table.add_column("Title", min_width=30)
    table.add_column("Confidence", justify="center", width=10)

    for result in results:
        entry = result.entry
        confidence_stars = "★" * entry.confidence + "☆" * (5 - entry.confidence)
        table.add_row(
            entry.id[:12] + "...",
            entry.type,
            entry.title,
            confidence_stars,
        )

    console.print(table)
    console.print(f"\n[dim]Found {len(results)} similar entries (FTS fallback)[/dim]")


# ============================================================================
# Export/Import Commands (Phase 9 + Export/Import Sync)
# ============================================================================


@app.command()
def export(
    output: str = typer.Argument(
        ...,
        help="Output file path (.rekall.zip for archive, .md or .json for text)",
    ),
    format: Optional[str] = typer.Option(
        None,
        "--format",
        "-f",
        help="Export format: rekall (default), md, or json",
    ),
    entry_type: Optional[str] = typer.Option(
        None,
        "--type",
        "-t",
        help="Filter by entry type",
    ),
    project: Optional[str] = typer.Option(
        None,
        "--project",
        "-p",
        help="Filter by project",
    ),
):
    """Export knowledge base.

    Export all entries to .rekall.zip archive (portable backup) or text formats.

    Examples:
        rekall export backup.rekall.zip
        rekall export backup.rekall.zip --project myproject
        rekall export --format md knowledge.md
        rekall export --format json backup.json
    """
    from rekall import exporters
    from rekall.archive import RekallArchive

    db = get_db()
    entries = db.list_all(entry_type=entry_type, project=project, limit=100000)

    if not entries:
        console.print("[yellow]No entries to export.[/yellow]")
        return

    # Determine format from output extension or explicit option
    output_path = Path(output)
    if format is None:
        if output_path.name.endswith(".rekall.zip"):
            format = "rekall"
        elif output_path.suffix == ".json":
            format = "json"
        else:
            format = "md"

    # Check for sensitive data
    sensitive = exporters.detect_sensitive_data(entries)
    if sensitive:
        console.print(f"[yellow]Warning: {len(sensitive)} entries may contain sensitive data:[/yellow]")
        for entry_id, title, pattern in sensitive[:5]:
            console.print(f"  [dim]{entry_id[:12]}[/dim] {title} ({pattern})")
        if len(sensitive) > 5:
            console.print(f"  [dim]... and {len(sensitive) - 5} more[/dim]")
        console.print()

    # Export
    if format == "rekall":
        RekallArchive.create(output_path, entries)
        console.print(f"[green]✓[/green] Exported {len(entries)} entries to {output}")
    elif format == "json":
        content = exporters.export_json(entries)
        output_path.write_text(content)
        console.print(f"[green]✓[/green] Exported {len(entries)} entries to {output}")
    else:
        content = exporters.export_markdown(entries)
        output_path.write_text(content)
        console.print(f"[green]✓[/green] Exported {len(entries)} entries to {output}")


@app.command("import")
def import_archive(
    archive: str = typer.Argument(..., help="Path to .rekall.zip archive file"),
    strategy: str = typer.Option(
        "skip",
        "--strategy",
        "-s",
        help="Conflict resolution: skip (default), replace, merge",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        "-n",
        help="Preview changes without importing",
    ),
    yes: bool = typer.Option(
        False,
        "--yes",
        "-y",
        help="Skip confirmation prompt",
    ),
    no_backup: bool = typer.Option(
        False,
        "--no-backup",
        help="Skip automatic backup before replace",
    ),
):
    """Import knowledge base from .rekall.zip archive.

    Import entries from a portable .rekall.zip archive with conflict resolution.

    Strategies:
        skip    - Keep local entries on conflict (default)
        replace - Overwrite local with imported (creates backup)
        merge   - Create new entries with new IDs

    Examples:
        rekall import backup.rekall.zip
        rekall import backup.rekall.zip --dry-run
        rekall import backup.rekall.zip --strategy replace --yes
    """
    from rekall.archive import RekallArchive
    from rekall.sync import ImportExecutor, build_import_plan

    archive_path = Path(archive)

    # Check file exists
    if not archive_path.exists():
        console.print(f"[red]Error: File not found: {archive}[/red]")
        raise typer.Exit(1)

    # Open and validate archive
    rekall_archive = RekallArchive.open(archive_path)
    if rekall_archive is None:
        console.print(f"[red]Error: Invalid or corrupted archive: {archive}[/red]")
        raise typer.Exit(1)

    validation = rekall_archive.validate()
    if not validation.valid:
        console.print("[red]Error: Archive validation failed:[/red]")
        for error in validation.errors:
            console.print(f"  - {error}")
        raise typer.Exit(1)

    # Get manifest and entries
    manifest = rekall_archive.get_manifest()
    imported_entries = rekall_archive.get_entries()

    console.print("[cyan]Archive info:[/cyan]")
    console.print(f"  Version: {manifest.format_version}")
    console.print(f"  Created: {manifest.created_at.strftime('%Y-%m-%d %H:%M')}")
    console.print(f"  Entries: {manifest.stats.entries_count}")
    console.print()

    # Build import plan
    db = get_db()
    plan = build_import_plan(db, imported_entries)

    # Show preview
    executor = ImportExecutor(db)
    preview = executor.preview(plan)
    console.print(preview)
    console.print()

    # Dry run mode
    if dry_run:
        console.print("[yellow]Dry run - no changes made.[/yellow]")
        return

    # Confirmation
    if not yes:
        if plan.total == 0:
            console.print("[yellow]Nothing to import.[/yellow]")
            return

        confirm = typer.confirm("Continue with import?")
        if not confirm:
            console.print("[yellow]Import cancelled.[/yellow]")
            return

    # Validate strategy
    if strategy not in ("skip", "replace", "merge"):
        console.print(f"[red]Error: Invalid strategy '{strategy}'. Use: skip, replace, merge[/red]")
        raise typer.Exit(1)

    # Configure backup
    backup_dir = None if no_backup else db.db_path.parent / "backups"
    executor = ImportExecutor(db, backup_dir=backup_dir)

    # Execute import
    result = executor.execute(plan, strategy=strategy)

    if result.success:
        console.print()
        console.print("[green]✓ Import completed successfully![/green]")
        console.print(f"  Added: {result.added}")
        if result.replaced:
            console.print(f"  Replaced: {result.replaced}")
        if result.merged:
            console.print(f"  Merged: {result.merged}")
        console.print(f"  Skipped: {result.skipped}")
        if result.backup_path:
            console.print(f"  Backup: {result.backup_path}")
    else:
        console.print("[red]Error: Import failed[/red]")
        for error in result.errors:
            console.print(f"  - {error}")
        raise typer.Exit(1)


# ============================================================================
# Link Command (US1 - Knowledge Graph)
# ============================================================================


@app.command()
def link(
    source_id: str = typer.Argument(..., help="Source entry ID"),
    target_id: str = typer.Argument(..., help="Target entry ID"),
    relation_type: str = typer.Option(
        "related",
        "--type",
        "-t",
        help=f"Relation type: {', '.join(VALID_RELATION_TYPES)}",
    ),
):
    """Create a link between two entries.

    Builds knowledge graph by connecting related entries.

    Examples:
        rekall link 01HXYZ 01HABC                    # related (default)
        rekall link 01HXYZ 01HABC --type supersedes  # A replaces B
        rekall link 01HXYZ 01HABC --type derived_from
    """
    if relation_type not in VALID_RELATION_TYPES:
        console.print(
            f"[red]Error: Invalid relation type '{relation_type}'[/red]\n"
            f"Valid types: {', '.join(VALID_RELATION_TYPES)}"
        )
        raise typer.Exit(1)

    db = get_db()

    try:
        db.add_link(source_id, target_id, relation_type)
        console.print(f"[green]✓[/green] Created link: {source_id[:12]}... → [{relation_type}] → {target_id[:12]}...")
    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


# ============================================================================
# Unlink Command (US1 - Knowledge Graph)
# ============================================================================


@app.command()
def unlink(
    source_id: str = typer.Argument(..., help="Source entry ID"),
    target_id: str = typer.Argument(..., help="Target entry ID"),
    relation_type: Optional[str] = typer.Option(
        None,
        "--type",
        "-t",
        help="Specific relation type to remove (all if not specified)",
    ),
):
    """Remove link(s) between two entries.

    Examples:
        rekall unlink 01HXYZ 01HABC                # Remove all links
        rekall unlink 01HXYZ 01HABC --type related # Remove specific type
    """
    if relation_type and relation_type not in VALID_RELATION_TYPES:
        console.print(
            f"[red]Error: Invalid relation type '{relation_type}'[/red]\n"
            f"Valid types: {', '.join(VALID_RELATION_TYPES)}"
        )
        raise typer.Exit(1)

    db = get_db()
    count = db.delete_link(source_id, target_id, relation_type)

    if count == 0:
        console.print(f"[yellow]No links found between {source_id[:12]}... and {target_id[:12]}...[/yellow]")
    else:
        console.print(f"[green]✓[/green] Deleted {count} link(s)")


# ============================================================================
# Related Command (US1 - Knowledge Graph)
# ============================================================================


@app.command()
def related(
    entry_id: str = typer.Argument(..., help="Entry ID"),
    relation_type: Optional[str] = typer.Option(
        None,
        "--type",
        "-t",
        help="Filter by relation type",
    ),
    depth: int = typer.Option(
        1,
        "--depth",
        "-d",
        min=1,
        max=3,
        help="Traversal depth (1-3)",
    ),
):
    """Show entries linked to a given entry.

    Navigates the knowledge graph to find related entries.

    Examples:
        rekall related 01HXYZ
        rekall related 01HXYZ --type derived_from
        rekall related 01HXYZ --depth 2
    """
    if relation_type and relation_type not in VALID_RELATION_TYPES:
        console.print(
            f"[red]Error: Invalid relation type '{relation_type}'[/red]\n"
            f"Valid types: {', '.join(VALID_RELATION_TYPES)}"
        )
        raise typer.Exit(1)

    db = get_db()

    # Get the entry first
    entry = db.get(entry_id, update_access=False)
    if entry is None:
        console.print(f"[red]Entry not found: {entry_id}[/red]")
        raise typer.Exit(1)

    # Get outgoing links
    outgoing = db.get_links(entry_id, relation_type=relation_type, direction="outgoing")
    incoming = db.get_links(entry_id, relation_type=relation_type, direction="incoming")

    if not outgoing and not incoming:
        console.print(f"[yellow]No links found for entry {entry_id[:12]}...[/yellow]")
        return

    console.print(f"\n[bold]Related to \"{entry.title}\"[/bold] ({entry_id[:12]}...):\n")

    if outgoing:
        console.print("[bold]Outgoing (→):[/bold]")
        for link in outgoing:
            target = db.get(link.target_id, update_access=False)
            if target:
                console.print(f"  [{link.relation_type}] {link.target_id[:12]}... \"{target.title}\"")

    if incoming:
        console.print("\n[bold]Incoming (←):[/bold]")
        for link in incoming:
            source = db.get(link.source_id, update_access=False)
            if source:
                console.print(f"  [{link.relation_type}] {link.source_id[:12]}... \"{source.title}\"")

    console.print(f"\n[dim]Total: {len(outgoing) + len(incoming)} links[/dim]")


@app.command()
def graph(
    entry_id: str = typer.Argument(..., help="Entry ID to visualize"),
    depth: int = typer.Option(
        2,
        "--depth",
        "-d",
        min=1,
        max=4,
        help="Maximum traversal depth (1-4)",
    ),
    outgoing_only: bool = typer.Option(
        False,
        "--outgoing",
        "-o",
        help="Show only outgoing links (→)",
    ),
    incoming_only: bool = typer.Option(
        False,
        "--incoming",
        "-i",
        help="Show only incoming links (←)",
    ),
):
    """Visualize entry connections as ASCII tree.

    Displays the knowledge graph centered on an entry with
    colored relation types and recursive traversal.

    Examples:
        rekall graph 01HXYZ
        rekall graph 01HXYZ --depth 3
        rekall graph 01HXYZ --outgoing
    """
    db = get_db()

    # Determine direction
    show_incoming = not outgoing_only
    show_outgoing = not incoming_only

    # If both flags are set, show both (they cancel out)
    if outgoing_only and incoming_only:
        show_incoming = True
        show_outgoing = True

    # Render the graph
    output = db.render_graph_ascii(
        entry_id,
        max_depth=depth,
        show_incoming=show_incoming,
        show_outgoing=show_outgoing,
    )

    console.print()
    console.print(output)
    console.print()


# ============================================================================
# Stale Command (US5 - Access Tracking)
# ============================================================================


@app.command()
def stale(
    days: int = typer.Option(
        30,
        "--days",
        "-d",
        help="Days since last access",
    ),
    limit: int = typer.Option(20, "--limit", "-l", help="Maximum results"),
):
    """List entries not accessed recently.

    Identifies knowledge at risk of being forgotten.

    Examples:
        rekall stale           # Not accessed in 30+ days
        rekall stale --days 7  # Not accessed in 7+ days
    """
    db = get_db()
    entries = db.get_stale_entries(days=days, limit=limit)

    if not entries:
        console.print(f"[green]No stale entries (all accessed within {days} days).[/green]")
        return

    console.print(f"\n[bold]Stale entries[/bold] (not accessed in {days}+ days):\n")

    table = Table(show_header=True, header_style="bold", box=box.ROUNDED)
    table.add_column("ID", style="dim", width=12)
    table.add_column("Title", min_width=30)
    table.add_column("Days", justify="right", width=6)
    table.add_column("Status", width=10)

    for entry in entries:
        days_stale = 0
        if entry.last_accessed:
            days_stale = (datetime.now() - entry.last_accessed).days

        # Status indicator
        if days_stale > 60:
            status = "🔴 fragile"
        elif days_stale > 30:
            status = "🟡 fading"
        else:
            status = "🟢 ok"

        table.add_row(
            entry.id[:12] + "...",
            entry.title,
            str(days_stale),
            status,
        )

    console.print(table)
    console.print(f"\n[dim]{len(entries)} entries need attention.[/dim]")
    console.print("[dim]Consider: rekall review (spaced repetition) or rekall deprecate (mark obsolete)[/dim]")


# ============================================================================
# Review Command (US6 - Spaced Repetition)
# ============================================================================


@app.command()
def review(
    limit: int = typer.Option(
        10,
        "--limit",
        "-l",
        help="Number of entries to review",
    ),
    project: Optional[str] = typer.Option(
        None,
        "--project",
        "-p",
        help="Filter by project",
    ),
):
    """Start a spaced repetition review session.

    Reviews entries due for reinforcement using SM-2 algorithm.

    Examples:
        rekall review
        rekall review --limit 5
        rekall review --project myapp
    """
    db = get_db()
    items = db.get_due_entries(limit=limit, project=project)

    if not items:
        console.print("[green]No entries due for review![/green]")
        return

    console.print(f"\n[bold]Review session: {len(items)} entries due[/bold]\n")

    reviewed = 0
    ratings = []

    for i, item in enumerate(items, 1):
        entry = item.entry

        console.print(f"[bold][{i}/{len(items)}][/bold] {entry.title} ({entry.id[:12]}...)")
        console.print(f"      Type: {entry.type} │ Memory: {entry.memory_type}")
        if item.days_overdue > 0:
            console.print(f"      [yellow]Overdue: {item.days_overdue} days[/yellow]")

        if entry.content:
            preview = entry.content[:200] + "..." if len(entry.content) > 200 else entry.content
            console.print(f"\n      [dim]{preview}[/dim]\n")

        console.print("      Rate your recall:")
        console.print("      [1] Forgot  [2] Hard  [3] Good  [4] Easy  [5] Perfect  [q] Quit")

        try:
            rating = typer.prompt("", default="3")
            if rating.lower() == "q":
                console.print("[yellow]Review session ended.[/yellow]")
                break

            rating_int = int(rating)
            if not 1 <= rating_int <= 5:
                console.print("[yellow]Invalid rating, using 3[/yellow]")
                rating_int = 3

            # Update review schedule
            db.update_review_schedule(entry.id, rating_int)
            reviewed += 1
            ratings.append(rating_int)

            # Show next review info
            updated = db.get(entry.id, update_access=False)
            if updated and updated.next_review:
                days_until = (updated.next_review - date.today()).days
                console.print(f"      [dim]Next review: in {days_until} days[/dim]")

            console.print("─" * 50)

        except (ValueError, KeyboardInterrupt):
            console.print("\n[yellow]Review session ended.[/yellow]")
            break

    # Summary
    if reviewed > 0:
        avg_rating = sum(ratings) / len(ratings)
        console.print("\n[bold]Review complete![/bold]")
        console.print(f"  Reviewed: {reviewed} entries")
        console.print(f"  Average recall: {avg_rating:.1f}/5")


# ============================================================================
# Generalize Command (US4, US7 - Episodic to Semantic)
# ============================================================================


@app.command()
def generalize(
    entry_ids: list[str] = typer.Argument(..., help="Entry IDs to generalize (2+ required)"),
    title: Optional[str] = typer.Option(
        None,
        "--title",
        "-t",
        help="Title for the semantic entry",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Show draft without creating",
    ),
):
    """Create a semantic entry from multiple episodic entries.

    Generalizes patterns from specific incidents into reusable knowledge.

    Examples:
        rekall generalize 01HXYZ 01HABC 01HDEF
        rekall generalize 01HXYZ 01HABC --title "Pattern timeout handling"
        rekall generalize 01HXYZ 01HABC --dry-run
    """
    if len(entry_ids) < 2:
        console.print("[red]Error: Need at least 2 entries to generalize[/red]")
        raise typer.Exit(1)

    db = get_db()

    # Load entries
    entries = []
    for entry_id in entry_ids:
        entry = db.get(entry_id, update_access=False)
        if entry is None:
            console.print(f"[red]Entry not found: {entry_id}[/red]")
            raise typer.Exit(1)
        entries.append(entry)

    # Check all are episodic
    non_episodic = [e for e in entries if e.memory_type != "episodic"]
    if non_episodic:
        console.print("[yellow]Warning: Some entries are not episodic:[/yellow]")
        for e in non_episodic:
            console.print(f"  - {e.id[:12]}... ({e.memory_type})")

    console.print(f"\n[bold]Analyzing {len(entries)} entries...[/bold]\n")

    # Show source entries
    console.print("[bold]Source entries:[/bold]")
    for e in entries:
        console.print(f"  - [{e.type}] {e.id[:12]}... \"{e.title}\"")

    # Collect common tags
    all_tags = []
    for e in entries:
        all_tags.extend(e.tags)
    common_tags = list(set(all_tags))[:5]

    # Generate title if not provided
    if not title:
        title = f"Pattern: {entries[0].title[:40]}..."

    console.print("\n[bold]Draft semantic entry:[/bold]")
    console.print("─" * 50)
    console.print(f"[bold]Title:[/bold] {title}")
    console.print("[bold]Type:[/bold] pattern")
    console.print("[bold]Memory:[/bold] semantic")
    console.print(f"[bold]Tags:[/bold] {', '.join(common_tags)}")
    console.print("\n[bold]Content:[/bold]")
    console.print("## Pattern\n(Describe the common pattern here)\n")
    console.print("## Resolution\n(Describe the common solution)\n")
    console.print("## Sources (episodic)")
    for e in entries:
        console.print(f"- {e.id} \"{e.title}\"")
    console.print("─" * 50)

    if dry_run:
        console.print("\n[dim]--dry-run: No entry created[/dim]")
        return

    # Confirm creation
    if not typer.confirm("\nCreate this entry?", default=True):
        console.print("[yellow]Cancelled.[/yellow]")
        return

    # Create semantic entry
    content = """## Pattern

(Describe the common pattern observed across these incidents)

## Resolution

(Describe the common solution or approach)

## Sources (episodic)

"""
    for e in entries:
        content += f"- {e.id} \"{e.title}\"\n"

    new_entry = Entry(
        id=generate_ulid(),
        title=title,
        type="pattern",
        content=content,
        project=entries[0].project,
        tags=common_tags,
        confidence=3,
        memory_type="semantic",
    )

    db.add(new_entry)
    console.print(f"\n[green]✓[/green] Created semantic entry: {new_entry.id}")

    # Create derived_from links
    for e in entries:
        try:
            db.add_link(new_entry.id, e.id, "derived_from")
            console.print(f"  [dim]→ Linked to {e.id[:12]}...[/dim]")
        except ValueError:
            pass  # Link may already exist

    console.print(f"\n[dim]Use 'rekall show {new_entry.id}' to view and edit the content.[/dim]")


# ============================================================================
# Info Command (Database Maintenance)
# ============================================================================


@app.command()
def info():
    """Display database statistics.

    Shows database path, schema version, entry counts, links, and file size.

    Example:
        rekall info
    """
    from rekall import __release_date__, __version__
    from rekall.backup import get_database_stats
    from rekall.db import CURRENT_SCHEMA_VERSION

    config = get_config()

    stats = get_database_stats(config.db_path)

    if stats is None:
        console.print("[yellow]No database found.[/yellow]")
        console.print("Run [cyan]rekall init[/cyan] to create one.")
        raise typer.Exit(1)

    # Build info display
    show_banner()

    info_table = Table(show_header=False, box=None, padding=(0, 2))
    info_table.add_column("Label", style="bold", justify="right", width=12)
    info_table.add_column("Value")

    # App version
    info_table.add_row("Version", f"v{__version__} ({__release_date__})")

    info_table.add_row("Database", str(stats.path))

    # Schema version with status
    schema_status = "[green](current)[/green]" if stats.is_current else "[yellow](outdated - run init)[/yellow]"
    info_table.add_row("Schema", f"v{stats.schema_version}/{CURRENT_SCHEMA_VERSION} {schema_status}")

    # Entries with breakdown
    info_table.add_row(
        "Entries",
        f"{stats.total_entries} ({stats.active_entries} active, {stats.obsolete_entries} obsolete)"
    )

    info_table.add_row("Links", str(stats.links_count))
    info_table.add_row("Size", stats.file_size_human)

    console.print(Panel(
        info_table,
        title="Database Information",
        border_style="cyan",
        padding=(1, 2),
    ))


# ============================================================================
# Backup Command (Database Maintenance)
# ============================================================================


@app.command()
def backup(
    output: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="Custom output path (default: ~/.rekall/backups/)",
    ),
):
    """Create a backup of the database.

    Safely copies the database after flushing WAL journal.
    Validates backup integrity after creation.

    Examples:
        rekall backup
        rekall backup --output ~/my-backups/rekall.db
    """
    from rekall.backup import create_backup

    config = get_config()

    if not config.db_path.exists():
        console.print("[red]Error: No database to backup.[/red]")
        raise typer.Exit(1)

    try:
        backup_info = create_backup(config.db_path, output)
        console.print(f"[green]✓[/green] Backup created: {backup_info.path}")
        console.print(f"  Size: {backup_info.size_human}")
    except Exception as e:
        console.print(f"[red]Error: Backup failed - {e}[/red]")
        raise typer.Exit(1)


# ============================================================================
# Restore Command (Database Maintenance)
# ============================================================================


@app.command()
def restore(
    backup_file: Path = typer.Argument(..., help="Path to backup file"),
    no_safety: bool = typer.Option(
        False,
        "--no-safety",
        help="Skip safety backup of current database",
    ),
    yes: bool = typer.Option(
        False,
        "--yes",
        "-y",
        help="Skip confirmation prompt",
    ),
):
    """Restore database from a backup.

    Creates a safety backup before restore (unless --no-safety).
    Validates backup integrity before restoring.

    Examples:
        rekall restore ~/.rekall/backups/knowledge_2025-12-09_143022.db
        rekall restore backup.db --yes
    """
    from rekall.backup import get_database_stats, restore_backup, validate_backup

    config = get_config()

    # Check backup exists
    if not backup_file.exists():
        console.print(f"[red]Error: Backup file not found: {backup_file}[/red]")
        raise typer.Exit(1)

    # Validate backup
    if not validate_backup(backup_file):
        console.print("[red]Error: Invalid backup file (integrity check failed).[/red]")
        console.print("[dim]Current database unchanged.[/dim]")
        raise typer.Exit(1)

    # Show backup info
    backup_stats = get_database_stats(backup_file)
    if backup_stats:
        console.print("[cyan]Backup info:[/cyan]")
        console.print(f"  Entries: {backup_stats.total_entries} ({backup_stats.active_entries} active)")
        console.print(f"  Links: {backup_stats.links_count}")
        console.print(f"  Size: {backup_stats.file_size_human}")
        console.print()

    # Confirmation
    if not yes:
        confirm = typer.confirm("Restore this backup? (Current database will be replaced)")
        if not confirm:
            console.print("[yellow]Restore cancelled.[/yellow]")
            return

    try:
        # Show safety backup message
        if not no_safety and config.db_path.exists():
            console.print("[yellow]⚠ Creating safety backup before restore...[/yellow]")

        success, safety_backup = restore_backup(
            backup_file,
            config.db_path,
            create_safety_backup=not no_safety,
        )

        if success:
            if safety_backup:
                console.print(f"  Saved: {safety_backup.path}")
                console.print()

            console.print(f"[green]✓[/green] Database restored from: {backup_file}")

            # Show restored stats
            restored_stats = get_database_stats(config.db_path)
            if restored_stats:
                console.print(f"  Entries: {restored_stats.total_entries} | Links: {restored_stats.links_count}")

    except FileNotFoundError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)
    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
        console.print("[dim]Current database unchanged.[/dim]")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
