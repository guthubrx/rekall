"""Rekall CLI - Developer Knowledge Management System."""

from __future__ import annotations

import platform
import sys
from datetime import date, datetime
from pathlib import Path

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
    StructuredContext,
    generate_ulid,
)
from rekall.utils import check_file_permissions, secure_file_permissions
from rekall.validators import EntryValidator

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


def _check_and_fix_permissions() -> None:
    """Check and fix file permissions at startup.

    Verifies that DB and config files have secure permissions (0o600).
    If not, warns the user and attempts to fix them automatically.
    """
    config = get_config()
    files_to_check = [
        ("Database", config.db_path),
        ("Config", config.config_dir / "config.toml"),
    ]

    for name, path in files_to_check:
        if path.exists() and not check_file_permissions(path):
            current_mode = path.stat().st_mode & 0o777
            console.print(
                f"[yellow]⚠ {name} file has insecure permissions "
                f"({oct(current_mode)}), fixing to 0o600...[/yellow]"
            )
            secure_file_permissions(path)


def _display_validation_error(error: Exception, context: str = "Input") -> None:
    """Display a Pydantic validation error with Rich formatting.

    Args:
        error: The Pydantic ValidationError
        context: Context string (e.g., "Entry", "Config")
    """
    from pydantic import ValidationError as PydanticValidationError

    if not isinstance(error, PydanticValidationError):
        console.print(f"[red]Error: {error}[/red]")
        return

    # Build error panel
    error_lines = []
    suggestions = []

    for err in error.errors():
        field = ".".join(str(loc) for loc in err["loc"]) if err["loc"] else "input"
        msg = err["msg"]
        error_type = err["type"]

        error_lines.append(f"• [bold]{field}[/bold]: {msg}")

        # Add helpful suggestions based on error type
        if error_type == "string_too_long":
            if "title" in field:
                suggestions.append("Hint: Keep titles under 500 characters")
            elif "content" in field:
                suggestions.append("Hint: Content is limited to 1MB")
            elif "tag" in field.lower():
                suggestions.append("Hint: Each tag should be under 100 characters")
        elif error_type == "string_too_short" or "empty" in msg.lower():
            suggestions.append(f"Hint: {field} cannot be empty")
        elif "pattern" in error_type:
            if "entry_type" in field:
                suggestions.append("Hint: Valid types: bug, pattern, decision, config, pitfall, reference, note")
        elif error_type == "value_error":
            suggestions.append(f"Hint: Check the value for {field}")

    # Create panel content
    panel_content = "\n".join(error_lines)
    if suggestions:
        panel_content += "\n\n[dim]" + "\n".join(set(suggestions)) + "[/dim]"

    console.print(Panel(
        panel_content,
        title=f"[red]✗ {context} Validation Error[/red]",
        border_style="red",
    ))


# Create Typer app with Rich markup
app = typer.Typer(
    name="rekall",
    help="Capture and retrieve bugs, patterns, and decisions.",
    add_completion=False,
    rich_markup_mode="rich",
    pretty_exceptions_show_locals=False,
)

# Database instance (lazy loaded)
_db: Database | None = None


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

    # Security check: verify/fix file permissions at startup
    _check_and_fix_permissions()

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
    from rekall.db import CURRENT_SCHEMA_VERSION, Database

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

    # Schema version info
    if db_exists:
        try:
            db = Database(config.db_path)
            db.conn = __import__("sqlite3").connect(str(config.db_path))
            current_schema = db.get_schema_version()
            db.close()

            if current_schema < CURRENT_SCHEMA_VERSION:
                pending = CURRENT_SCHEMA_VERSION - current_schema
                info_table.add_row(
                    "Schema Version",
                    f"v{current_schema} → v{CURRENT_SCHEMA_VERSION} [yellow]({pending} migration(s) pending)[/yellow]"
                )
            else:
                info_table.add_row("Schema Version", f"v{current_schema} [green](current)[/green]")
        except Exception:
            info_table.add_row("Schema Version", "[red]error reading[/red]")
    else:
        info_table.add_row("Schema Version", f"v{CURRENT_SCHEMA_VERSION} (latest)")

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
    entry_type: str | None = typer.Option(
        None,
        "--type",
        "-t",
        help=f"Filter by type: {', '.join(VALID_TYPES)}",
    ),
    project: str | None = typer.Option(
        None,
        "--project",
        "-p",
        help="Filter by project",
    ),
    memory_type: str | None = typer.Option(
        None,
        "--memory-type",
        "-m",
        help=f"Filter by memory type: {', '.join(VALID_MEMORY_TYPES)}",
    ),
    limit: int = typer.Option(20, "--limit", "-l", help="Maximum results"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON for AI agents"),
    context: str | None = typer.Option(
        None,
        "--context",
        help="Conversation context for semantic search (AI agent use)",
    ),
    semantic_only: bool = typer.Option(
        False,
        "--semantic-only",
        help="Use semantic search only (requires embeddings)",
    ),
):
    """Search knowledge base.

    Uses hybrid search (FTS + semantic) when embeddings are enabled.

    Examples:
        rekall search "circular import"
        rekall search "cache" --type pattern
        rekall search "react" --project frontend
        rekall search "timeout" --memory-type semantic
        rekall search "auth" --json  # For AI agents
        rekall search "error handling" --context "API development"
        rekall search "patterns" --semantic-only
    """
    import json

    db = get_db()
    cfg = get_config()

    # Determine search mode
    use_hybrid = cfg.smart_embeddings_enabled and not semantic_only
    use_semantic = semantic_only

    # Semantic scores for display
    semantic_scores: dict[str, float] = {}

    if use_semantic:
        # Semantic-only search
        from rekall.embeddings import get_embedding_service

        service = get_embedding_service(
            dimensions=cfg.smart_embeddings_dimensions,
            similarity_threshold=cfg.smart_embeddings_similarity_threshold,
        )

        if not service.available:
            console.print("[red]Error: Embeddings not available for --semantic-only[/red]")
            console.print("[dim]Install with: pip install sentence-transformers numpy[/dim]")
            raise typer.Exit(1)

        sem_results = service.semantic_search(query, db, context=context, limit=limit)

        # Convert to SearchResult-like format for unified processing
        from rekall.db import SearchResult
        results = []
        for entry, score in sem_results:
            # Apply filters
            if entry_type and entry.type != entry_type:
                continue
            if project and entry.project != project:
                continue
            if memory_type and entry.memory_type != memory_type:
                continue
            results.append(SearchResult(entry=entry, rank=None))
            semantic_scores[entry.id] = score

    elif use_hybrid:
        # Hybrid search (FTS + semantic)
        from rekall.embeddings import get_embedding_service

        service = get_embedding_service(
            dimensions=cfg.smart_embeddings_dimensions,
            similarity_threshold=cfg.smart_embeddings_similarity_threshold,
        )

        hybrid_results = service.hybrid_search(
            query, db,
            context=context,
            limit=limit,
            entry_type=entry_type,
            project=project,
            memory_type=memory_type,
        )

        # Convert to SearchResult format
        from rekall.db import SearchResult
        results = []
        for entry, _combined_score, sem_score in hybrid_results:
            results.append(SearchResult(entry=entry, rank=None))
            if sem_score is not None:
                semantic_scores[entry.id] = sem_score

    else:
        # FTS-only search (default when embeddings disabled)
        results = db.search(query, entry_type=entry_type, project=project, memory_type=memory_type, limit=limit)

    # JSON output for AI agents
    if json_output:
        search_mode = "semantic" if use_semantic else ("hybrid" if use_hybrid else "fts")
        output = {
            "query": query,
            "results": [],
            "total_count": len(results),
            "search_mode": search_mode,
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
                "semantic_score": round(semantic_scores.get(entry.id, 0), 3) if entry.id in semantic_scores else None,
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

    # Display search mode
    if use_semantic:
        console.print("[dim]Search mode: semantic only[/dim]")
    elif use_hybrid and semantic_scores:
        console.print("[dim]Search mode: hybrid (FTS + semantic)[/dim]")

    # Display results in a table
    table = Table(title=f"Search: {query}", show_header=True, header_style="bold", box=box.ROUNDED)
    table.add_column("ID", style="dim", width=12)
    table.add_column("Type", width=10)
    table.add_column("Title", min_width=30)
    table.add_column("Confidence", justify="center", width=10)
    if semantic_scores:
        table.add_column("Semantic", justify="center", width=10)
    table.add_column("Project", width=15)

    for result in results:
        entry = result.entry
        confidence_stars = "★" * entry.confidence + "☆" * (5 - entry.confidence)
        row = [
            entry.id[:12] + "...",
            entry.type,
            entry.title,
            confidence_stars,
        ]
        if semantic_scores:
            sem_score = semantic_scores.get(entry.id)
            row.append(f"{sem_score:.0%}" if sem_score else "-")
        row.append(entry.project or "-")
        table.add_row(*row)

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
    tags: str | None = typer.Option(
        None,
        "--tags",
        "-t",
        help="Comma-separated tags",
    ),
    project: str | None = typer.Option(
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
    content: str | None = typer.Option(
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
    context: str | None = typer.Option(
        None,
        "--context",
        help="Conversation context for semantic embedding (AI agent use)",
    ),
    context_json: str | None = typer.Option(
        None,
        "--context-json",
        "-cj",
        help="Structured context as JSON: {situation, solution, trigger_keywords, ...}",
    ),
    context_interactive: bool = typer.Option(
        False,
        "--context-interactive",
        "-ci",
        help="Interactively prompt for structured context fields",
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

    # Validate entry data with Pydantic (T017: Input validation)
    from pydantic import ValidationError as PydanticValidationError

    try:
        validated = EntryValidator(
            title=title,
            content=entry_content,
            tags=tag_list,
            entry_type=entry_type,
            confidence=confidence,
            project=project,
        )
        # Use validated/normalized values
        title = validated.title
        entry_content = validated.content
        tag_list = validated.tags
    except PydanticValidationError as e:
        # T018: Rich error messages with suggestions
        _display_validation_error(e, "Entry")
        raise typer.Exit(1)

    # Check context requirement based on config
    # Context can be provided via --context, --context-json, or --context-interactive
    cfg = get_config()
    context_mode = cfg.smart_embeddings_context_mode
    has_context = context or context_json or context_interactive
    if not has_context:
        if context_mode == "required":
            console.print(
                "[red]Error: --context is required[/red]\n"
                "Set context_mode = \"optional\" in config.toml to disable this check."
            )
            raise typer.Exit(1)
        elif context_mode == "recommended":
            console.print(
                "[yellow]⚠ Warning: --context not provided[/yellow]\n"
                "[dim]Context helps AI verify suggestions. Use --context to add conversation context.[/dim]"
            )

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

    # Handle structured context (--context-interactive or --context-json)
    structured_ctx = None

    if context_interactive:
        # Interactive mode: prompt for each field
        from rekall.context_extractor import extract_keywords, suggest_keywords

        console.print("\n[bold cyan]Structured Context[/bold cyan]")
        console.print("[dim]This helps find this entry later. Press Enter to skip optional fields.[/dim]\n")

        situation = typer.prompt("Situation (what was the problem?)")
        solution = typer.prompt("Solution (how was it resolved?)")

        # Suggest keywords based on title + content
        suggested = suggest_keywords(title, entry_content, max_suggestions=5)
        if suggested:
            console.print(f"[dim]Suggested keywords: {', '.join(suggested)}[/dim]")

        keywords_input = typer.prompt(
            "Keywords (comma-separated, or press Enter for auto-extract)",
            default="",
        )
        if keywords_input.strip():
            trigger_keywords = [k.strip() for k in keywords_input.split(",") if k.strip()]
        else:
            trigger_keywords = extract_keywords(title, f"{entry_content} {situation} {solution}")[:5]
            console.print(f"[dim]Auto-extracted: {', '.join(trigger_keywords)}[/dim]")

        what_failed = typer.prompt("What didn't work? (optional)", default="")

        try:
            structured_ctx = StructuredContext(
                situation=situation,
                solution=solution,
                trigger_keywords=trigger_keywords,
                what_failed=what_failed if what_failed else None,
                extraction_method="hybrid" if not keywords_input.strip() else "manual",
            )
            db.store_structured_context(entry.id, structured_ctx)
            context = f"Situation: {situation}\nSolution: {solution}"
        except ValueError as e:
            console.print(f"[red]Error: {e}[/red]")
            raise typer.Exit(1)

    elif context_json:
        import json as json_module
        try:
            ctx_data = json_module.loads(context_json)
            structured_ctx = StructuredContext(
                situation=ctx_data.get("situation", ""),
                solution=ctx_data.get("solution", ""),
                trigger_keywords=ctx_data.get("trigger_keywords", []),
                what_failed=ctx_data.get("what_failed"),
                conversation_excerpt=ctx_data.get("conversation_excerpt"),
                files_modified=ctx_data.get("files_modified"),
                error_messages=ctx_data.get("error_messages"),
            )
            db.store_structured_context(entry.id, structured_ctx)
            # Also create legacy context for embeddings
            context = f"Situation: {structured_ctx.situation}\nSolution: {structured_ctx.solution}"
        except json_module.JSONDecodeError as e:
            console.print(f"[red]Error: Invalid JSON in --context-json: {e}[/red]")
            raise typer.Exit(1)
        except ValueError as e:
            console.print(f"[red]Error: Invalid structured context: {e}[/red]")
            raise typer.Exit(1)

    # Store compressed context if provided (for AI verification of suggestions)
    if context:
        db.store_context(entry.id, context)

    console.print(f"[green]✓[/green] Entry created: {entry.id}")
    console.print(f"  Type: {entry.type}")
    console.print(f"  Title: {entry.title}")
    if tag_list:
        console.print(f"  Tags: {', '.join(tag_list)}")
    if project:
        console.print(f"  Project: {project}")
    if structured_ctx:
        console.print(f"  [dim]Context: {len(structured_ctx.trigger_keywords)} keywords stored[/dim]")

    # Calculate embeddings if enabled (cfg already loaded above)
    if cfg.smart_embeddings_enabled:
        from rekall.embeddings import get_embedding_service
        from rekall.models import Embedding

        service = get_embedding_service(
            dimensions=cfg.smart_embeddings_dimensions,
            similarity_threshold=cfg.smart_embeddings_similarity_threshold,
        )

        if service.available:
            embeddings = service.calculate_for_entry(entry, context=context)

            # Save summary embedding
            if embeddings["summary"] is not None:
                emb = Embedding.from_numpy(
                    entry.id,
                    "summary",
                    embeddings["summary"],
                    service.model_name,
                )
                db.add_embedding(emb)
                console.print("  [dim]📊 Summary embedding calculated[/dim]")

            # Save context embedding if provided
            if embeddings["context"] is not None:
                emb = Embedding.from_numpy(
                    entry.id,
                    "context",
                    embeddings["context"],
                    service.model_name,
                )
                db.add_embedding(emb)
                console.print("  [dim]📊 Context embedding calculated[/dim]")
        else:
            console.print("  [dim yellow]⚠ Embeddings disabled (dependencies missing)[/dim yellow]")


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

    # Embedding status
    embeddings_list = db.get_embeddings(entry.id)
    if embeddings_list:
        emb_types = [e.embedding_type for e in embeddings_list]
        panel_content.append("Embeddings: ", style="bold")
        panel_content.append(f"📊 {', '.join(emb_types)}\n")

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
    entry_type: str | None = typer.Option(
        None,
        "--type",
        "-t",
        help=f"Filter by type: {', '.join(VALID_TYPES)}",
    ),
    project: str | None = typer.Option(
        None,
        "--project",
        "-p",
        help="Filter by project",
    ),
    memory_type: str | None = typer.Option(
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
    replaced_by: str | None = typer.Option(
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
    ide: str | None = typer.Argument(
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
    topic: str | None = typer.Argument(
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
    format: str | None = typer.Option(
        None,
        "--format",
        "-f",
        help="Export format: rekall (default), md, or json",
    ),
    entry_type: str | None = typer.Option(
        None,
        "--type",
        "-t",
        help="Filter by entry type",
    ),
    project: str | None = typer.Option(
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
    reason: str | None = typer.Option(
        None,
        "--reason",
        "-r",
        help="Justification for the link (why this relation type)",
    ),
):
    """Create a link between two entries.

    Builds knowledge graph by connecting related entries.

    Examples:
        rekall link 01HXYZ 01HABC                    # related (default)
        rekall link 01HXYZ 01HABC --type supersedes  # A replaces B
        rekall link 01HXYZ 01HABC --type derived_from --reason "B is a fix for bug A"
    """
    if relation_type not in VALID_RELATION_TYPES:
        console.print(
            f"[red]Error: Invalid relation type '{relation_type}'[/red]\n"
            f"Valid types: {', '.join(VALID_RELATION_TYPES)}"
        )
        raise typer.Exit(1)

    db = get_db()

    try:
        db.add_link(source_id, target_id, relation_type, reason=reason)
        output = f"[green]✓[/green] Created link: {source_id[:12]}... → [{relation_type}] → {target_id[:12]}..."
        if reason:
            output += f"\n  Reason: {reason}"
        console.print(output)
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
    relation_type: str | None = typer.Option(
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
    relation_type: str | None = typer.Option(
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
    project: str | None = typer.Option(
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
    title: str | None = typer.Option(
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
    output: Path | None = typer.Option(
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


# ============================================================================
# Suggest Command (Smart Embeddings - Phase 5)
# ============================================================================


@app.command()
def suggest(
    accept: str | None = typer.Option(
        None,
        "--accept",
        "-a",
        help="Accept suggestion by ID (creates link or shows generalize command)",
    ),
    reject: str | None = typer.Option(
        None,
        "--reject",
        "-r",
        help="Reject suggestion by ID",
    ),
    suggestion_type: str | None = typer.Option(
        None,
        "--type",
        "-t",
        help="Filter by type: link, generalize",
    ),
    limit: int = typer.Option(20, "--limit", "-l", help="Maximum suggestions to show"),
):
    """Manage smart embedding suggestions.

    Lists pending suggestions (similar entries to link, entries to generalize).
    Use --accept or --reject to process suggestions.

    Examples:
        rekall suggest                    # List pending suggestions
        rekall suggest --type link        # Show link suggestions only
        rekall suggest --accept ABC123    # Accept a suggestion
        rekall suggest --reject ABC123    # Reject a suggestion
    """
    from rekall.models import VALID_SUGGESTION_TYPES

    db = get_db()

    # Accept a suggestion
    if accept:
        suggestion = db.get_suggestion(accept)
        if suggestion is None:
            console.print(f"[red]Suggestion not found: {accept}[/red]")
            raise typer.Exit(1)

        if suggestion.status != "pending":
            console.print(f"[yellow]Suggestion already {suggestion.status}[/yellow]")
            raise typer.Exit(1)

        if suggestion.suggestion_type == "link":
            # Create the link
            if len(suggestion.entry_ids) >= 2:
                source_id = suggestion.entry_ids[0]
                target_id = suggestion.entry_ids[1]
                try:
                    db.add_link(source_id, target_id, "related")
                    db.update_suggestion_status(accept, "accepted")
                    console.print(f"[green]✓[/green] Link created: {source_id[:12]}... → {target_id[:12]}...")
                except ValueError as e:
                    console.print(f"[red]Error creating link: {e}[/red]")
                    raise typer.Exit(1)
        else:
            # Generalize suggestion - show command to use
            db.update_suggestion_status(accept, "accepted")
            entry_ids_str = " ".join(suggestion.entry_ids)
            console.print("[green]✓[/green] Suggestion accepted.")
            console.print("\nTo generalize these entries, run:")
            console.print(f"  [cyan]rekall generalize {entry_ids_str}[/cyan]")
        return

    # Reject a suggestion
    if reject:
        suggestion = db.get_suggestion(reject)
        if suggestion is None:
            console.print(f"[red]Suggestion not found: {reject}[/red]")
            raise typer.Exit(1)

        if suggestion.status != "pending":
            console.print(f"[yellow]Suggestion already {suggestion.status}[/yellow]")
            raise typer.Exit(1)

        db.update_suggestion_status(reject, "rejected")
        console.print(f"[green]✓[/green] Suggestion rejected: {reject[:12]}...")
        return

    # Validate type filter
    if suggestion_type and suggestion_type not in VALID_SUGGESTION_TYPES:
        console.print(
            f"[red]Error: Invalid type '{suggestion_type}'[/red]\n"
            f"Valid types: {', '.join(VALID_SUGGESTION_TYPES)}"
        )
        raise typer.Exit(1)

    # List pending suggestions
    suggestions = db.get_suggestions(status="pending", suggestion_type=suggestion_type, limit=limit)

    if not suggestions:
        console.print("[green]No pending suggestions.[/green]")
        return

    console.print(f"\n[bold]Pending Suggestions[/bold] ({len(suggestions)})\n")

    # Group by type
    link_suggestions = [s for s in suggestions if s.suggestion_type == "link"]
    generalize_suggestions = [s for s in suggestions if s.suggestion_type == "generalize"]

    if link_suggestions:
        console.print("[bold cyan]Link Suggestions[/bold cyan]")
        table = Table(show_header=True, header_style="bold", box=box.ROUNDED)
        table.add_column("ID", style="dim", width=14)
        table.add_column("Entries", min_width=40)
        table.add_column("Score", justify="center", width=8)
        table.add_column("Reason", width=30)

        for s in link_suggestions:
            # Get entry titles
            entry_titles = []
            for eid in s.entry_ids[:2]:
                entry = db.get(eid, update_access=False)
                if entry:
                    entry_titles.append(f"{eid[:8]}... \"{entry.title[:20]}\"")
            entries_str = " ↔ ".join(entry_titles)

            table.add_row(
                s.id[:14],
                entries_str,
                f"{s.score:.0%}",
                (s.reason[:27] + "...") if len(s.reason) > 30 else s.reason,
            )

        console.print(table)
        console.print()

    if generalize_suggestions:
        console.print("[bold cyan]Generalize Suggestions[/bold cyan]")
        table = Table(show_header=True, header_style="bold", box=box.ROUNDED)
        table.add_column("ID", style="dim", width=14)
        table.add_column("Entries", min_width=40)
        table.add_column("Count", justify="center", width=6)
        table.add_column("Score", justify="center", width=8)

        for s in generalize_suggestions:
            # Get entry titles
            entry_titles = []
            for eid in s.entry_ids[:3]:
                entry = db.get(eid, update_access=False)
                if entry:
                    entry_titles.append(f"\"{entry.title[:15]}\"")
            entries_str = ", ".join(entry_titles)
            if len(s.entry_ids) > 3:
                entries_str += f" +{len(s.entry_ids) - 3}"

            table.add_row(
                s.id[:14],
                entries_str,
                str(len(s.entry_ids)),
                f"{s.score:.0%}",
            )

        console.print(table)
        console.print()

    console.print("[dim]Use --accept ID or --reject ID to process suggestions[/dim]")


# ============================================================================
# Embeddings Command (Smart Embeddings - Phase 7)
# ============================================================================


@app.command()
def embeddings(
    migrate: bool = typer.Option(
        False,
        "--migrate",
        help="Calculate embeddings for entries without them",
    ),
    status: bool = typer.Option(
        False,
        "--status",
        "-s",
        help="Show embedding status and statistics",
    ),
    limit: int = typer.Option(100, "--limit", "-l", help="Max entries to migrate"),
):
    """Manage smart embeddings.

    View status or migrate existing entries to have embeddings.

    Examples:
        rekall embeddings --status         # Show embedding statistics
        rekall embeddings --migrate        # Calculate missing embeddings
        rekall embeddings --migrate -l 50  # Migrate max 50 entries
    """
    from rich.progress import Progress

    cfg = get_config()
    db = get_db()

    if status:
        # Show embedding status
        total_entries = len(db.list_all(limit=100000))
        total_embeddings = db.count_embeddings()
        entries_without = len(db.get_entries_without_embeddings("summary"))

        console.print("\n[bold]Embedding Status[/bold]\n")
        console.print(f"  Enabled: {'[green]Yes[/green]' if cfg.smart_embeddings_enabled else '[yellow]No[/yellow]'}")
        console.print(f"  Model: {cfg.smart_embeddings_model}")
        console.print(f"  Dimensions: {cfg.smart_embeddings_dimensions}")
        console.print(f"  Threshold: {cfg.smart_embeddings_similarity_threshold}")
        console.print()
        console.print(f"  Total entries: {total_entries}")
        console.print(f"  Total embeddings: {total_embeddings}")
        console.print(f"  Entries without embeddings: {entries_without}")

        if entries_without > 0:
            console.print("\n[dim]Run 'rekall embeddings --migrate' to calculate missing embeddings[/dim]")
        return

    if migrate:
        if not cfg.smart_embeddings_enabled:
            console.print("[yellow]Warning: smart_embeddings_enabled is False in config[/yellow]")
            console.print("[dim]Embeddings will be calculated but not used for search[/dim]")
            console.print()

        from rekall.embeddings import get_embedding_service
        from rekall.models import Embedding

        service = get_embedding_service(
            dimensions=cfg.smart_embeddings_dimensions,
            similarity_threshold=cfg.smart_embeddings_similarity_threshold,
        )

        if not service.available:
            console.print("[red]Error: Embedding dependencies not available[/red]")
            console.print("[dim]Install with: pip install sentence-transformers numpy[/dim]")
            raise typer.Exit(1)

        entries = db.get_entries_without_embeddings("summary")[:limit]

        if not entries:
            console.print("[green]All entries already have embeddings.[/green]")
            return

        console.print(f"Calculating embeddings for {len(entries)} entries...")

        with Progress() as progress:
            task = progress.add_task("[cyan]Migrating...", total=len(entries))

            for entry in entries:
                embeddings_dict = service.calculate_for_entry(entry)

                if embeddings_dict["summary"] is not None:
                    emb = Embedding.from_numpy(
                        entry.id,
                        "summary",
                        embeddings_dict["summary"],
                        service.model_name,
                    )
                    db.add_embedding(emb)

                progress.update(task, advance=1)

        console.print(f"\n[green]✓[/green] Migrated {len(entries)} entries")

        # Check if more remain
        remaining = len(db.get_entries_without_embeddings("summary"))
        if remaining > 0:
            console.print(f"[dim]{remaining} entries still need embeddings[/dim]")
        return

    # Default: show help
    console.print("Use [cyan]rekall embeddings --status[/cyan] to view statistics.")
    console.print("Use [cyan]rekall embeddings --migrate[/cyan] to calculate missing embeddings.")


# ============================================================================
# Migrate Command (Feature 007 - Migration & Maintenance)
# ============================================================================


@app.command()
def migrate(
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        "-n",
        help="Preview migrations without applying them",
    ),
    enrich_context: bool = typer.Option(
        False,
        "--enrich-context",
        help="Enrich legacy entries without structured context",
    ),
    yes: bool = typer.Option(
        False,
        "--yes",
        "-y",
        help="Skip confirmation prompt",
    ),
):
    """Apply pending database migrations.

    Automatically creates a backup before applying migrations.
    Use --dry-run to preview changes without modifying the database.
    Use --enrich-context to add structured context to legacy entries.

    Examples:
        rekall migrate              # Apply pending migrations
        rekall migrate --dry-run    # Preview without applying
        rekall migrate --enrich-context  # Enrich legacy entries
    """
    from rekall.backup import create_backup
    from rekall.db import CURRENT_SCHEMA_VERSION, MIGRATIONS, Database

    config = get_config()

    if not config.db_path.exists():
        console.print("[yellow]No database found.[/yellow]")
        console.print("Run [cyan]rekall init[/cyan] to create one.")
        raise typer.Exit(1)

    # Connect to get current version
    db = Database(config.db_path)
    db.conn = __import__("sqlite3").connect(str(config.db_path))
    current_version = db.get_schema_version()

    # Handle --enrich-context mode
    if enrich_context:
        from rekall.context_extractor import extract_keywords

        db.init()  # Ensure full connection
        entries = db.list_all(limit=100000)
        legacy_entries = []

        for entry in entries:
            ctx = db.get_structured_context(entry.id)
            if ctx is None:
                legacy_entries.append(entry)

        if not legacy_entries:
            console.print("[green]All entries already have structured context.[/green]")
            db.close()
            return

        console.print(f"Found [cyan]{len(legacy_entries)}[/cyan] entries without structured context.\n")

        if dry_run:
            console.print("[yellow]Dry run - showing first 5 entries:[/yellow]")
            for entry in legacy_entries[:5]:
                keywords = extract_keywords(entry.title, entry.content or "")[:5]
                console.print(f"  • {entry.id[:12]}... \"{entry.title}\"")
                console.print(f"    [dim]Keywords: {', '.join(keywords)}[/dim]")
            if len(legacy_entries) > 5:
                console.print(f"  [dim]... and {len(legacy_entries) - 5} more[/dim]")
            db.close()
            return

        if not yes:
            confirm = typer.confirm(f"Enrich {len(legacy_entries)} entries?")
            if not confirm:
                console.print("[yellow]Cancelled.[/yellow]")
                db.close()
                return

        # Enrich entries
        from rekall.models import StructuredContext

        enriched = 0
        for entry in legacy_entries:
            keywords = extract_keywords(entry.title, entry.content or "")[:5]
            if not keywords:
                keywords = [entry.type]  # Fallback

            # Generate basic situation/solution from content
            content = entry.content or entry.title
            situation = f"Context from: {entry.title}"
            solution = content[:200] if len(content) > 200 else content

            try:
                ctx = StructuredContext(
                    situation=situation,
                    solution=solution,
                    trigger_keywords=keywords,
                    extraction_method="migrated",
                )
                db.store_structured_context(entry.id, ctx)
                enriched += 1
            except ValueError:
                continue  # Skip invalid entries

        console.print(f"[green]✓[/green] Enriched {enriched} entries with structured context.")
        db.close()
        return

    # Schema migrations
    pending_versions = [v for v in sorted(MIGRATIONS.keys()) if v > current_version]

    if not pending_versions:
        console.print(f"[green]Database schema is current (v{current_version}).[/green]")
        db.close()
        return

    console.print(f"Current schema: v{current_version}")
    console.print(f"Target schema: v{CURRENT_SCHEMA_VERSION}")
    console.print(f"Pending migrations: {len(pending_versions)}\n")

    # Show migration details
    for version in pending_versions:
        statements = MIGRATIONS[version]
        console.print(f"[bold]Migration v{version}:[/bold]")
        for stmt in statements[:3]:  # Show first 3 statements
            # Truncate long statements
            preview = stmt.strip()[:60]
            if len(stmt.strip()) > 60:
                preview += "..."
            console.print(f"  [dim]{preview}[/dim]")
        if len(statements) > 3:
            console.print(f"  [dim]... and {len(statements) - 3} more statements[/dim]")
        console.print()

    if dry_run:
        console.print("[yellow]Dry run - no changes made.[/yellow]")
        db.close()
        return

    # Confirmation
    if not yes:
        confirm = typer.confirm("Apply migrations?")
        if not confirm:
            console.print("[yellow]Migration cancelled.[/yellow]")
            db.close()
            return

    # Create backup before migration
    console.print("[cyan]Creating backup before migration...[/cyan]")
    try:
        backup_info = create_backup(config.db_path)
        console.print(f"  Backup: {backup_info.path}")
    except Exception as e:
        console.print(f"[red]Backup failed: {e}[/red]")
        console.print("[yellow]Migration aborted for safety.[/yellow]")
        db.close()
        raise typer.Exit(1)

    # Apply migrations
    db.close()
    db = Database(config.db_path)
    try:
        db.init()  # This applies migrations
        new_version = db.get_schema_version()
        console.print(f"\n[green]✓[/green] Migrated from v{current_version} to v{new_version}")

        # If migrating to v7+, also migrate context data to compressed format
        if new_version >= 7 and current_version < 7:
            pending_data = db.count_entries_without_context_blob()
            if pending_data > 0:
                console.print(f"\n[cyan]Migrating {pending_data} entries to compressed format...[/cyan]")
                migrated, keywords = db.migrate_to_compressed_context()
                console.print(f"[green]✓[/green] Compressed {migrated} entries, indexed {keywords} keywords")
    except Exception as e:
        console.print(f"[red]Migration failed: {e}[/red]")
        console.print(f"[yellow]Restore from backup: {backup_info.path}[/yellow]")
        raise typer.Exit(1)
    finally:
        db.close()


# ============================================================================
# Changelog Command (Feature 007 - Migration & Maintenance)
# ============================================================================


@app.command()
def changelog(
    version_filter: str | None = typer.Argument(
        None,
        help="Show changes for specific version (e.g., '0.2.0')",
    ),
):
    """Display changelog and version history.

    Shows changes by version from the CHANGELOG.md file.

    Examples:
        rekall changelog          # Show full changelog
        rekall changelog 0.2.0    # Show changes for v0.2.0
    """
    # Find CHANGELOG.md
    changelog_paths = [
        Path(__file__).parent.parent / "CHANGELOG.md",  # In package root
        Path(__file__).parent / "CHANGELOG.md",  # In rekall/
        Path.cwd() / "CHANGELOG.md",  # In current directory
    ]

    changelog_path = None
    for path in changelog_paths:
        if path.exists():
            changelog_path = path
            break

    if changelog_path is None:
        console.print("[yellow]CHANGELOG.md not found.[/yellow]")
        console.print("[dim]Create one at project root to enable this command.[/dim]")
        raise typer.Exit(1)

    content = changelog_path.read_text()

    if version_filter:
        # Extract specific version section
        import re

        # Match version header (## [0.2.0] or ## 0.2.0)
        pattern = rf"##\s*\[?{re.escape(version_filter)}\]?.*?\n(.*?)(?=##\s*\[?\d|\Z)"
        match = re.search(pattern, content, re.DOTALL)

        if match:
            console.print(f"[bold cyan]Changelog v{version_filter}[/bold cyan]\n")
            console.print(match.group(1).strip())
        else:
            console.print(f"[yellow]Version {version_filter} not found in changelog.[/yellow]")
            raise typer.Exit(1)
    else:
        # Show full changelog with Rich formatting
        from rich.markdown import Markdown

        md = Markdown(content)
        console.print(md)


# ============================================================================
# MCP Server Command (Smart Embeddings - Phase 6)
# ============================================================================


@app.command("mcp-server")
def mcp_server():
    """Start the MCP (Model Context Protocol) server.

    Provides AI agent tools for interacting with Rekall:
    - rekall_help: Usage guide
    - rekall_search: Search knowledge base
    - rekall_show: Get entry details
    - rekall_add: Add new entries
    - rekall_link: Link entries
    - rekall_suggest: Get suggestions

    Configure in Claude Desktop or other MCP clients:
        {
            "mcpServers": {
                "rekall": {
                    "command": "rekall",
                    "args": ["mcp-server"]
                }
            }
        }

    Examples:
        rekall mcp-server
    """
    import asyncio

    from rekall.mcp_server import MCPNotAvailable, run_server

    try:
        asyncio.run(run_server())
    except MCPNotAvailable as e:
        console.print(f"[red]Error: {e}[/red]")
        console.print("[dim]Install with: pip install mcp[/dim]")
        raise typer.Exit(1)
    except KeyboardInterrupt:
        console.print("\n[yellow]MCP server stopped.[/yellow]")


if __name__ == "__main__":
    app()
