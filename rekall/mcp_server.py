"""MCP Server for Rekall - Developer Knowledge Management System.

This module provides Model Context Protocol (MCP) tools for AI agents
to interact with Rekall's knowledge base.

Tools provided:
- rekall_help: Guide for using Rekall (call first)
- rekall_search: Search the knowledge base
- rekall_show: Get full details of an entry
- rekall_add: Add a new entry
- rekall_link: Create a link between entries
- rekall_unlink: Remove a link between entries (Feature 015)
- rekall_suggest: Get pending suggestions
- rekall_related: Explore related entries in the knowledge graph (Feature 015)
- rekall_similar: Find semantically similar entries (Feature 015)
- rekall_sources_suggest: Suggest sources for an entry (Feature 015)
- rekall_info: Get knowledge base statistics (Feature 015)
- rekall_stale: Find entries not accessed recently (Feature 015)
- rekall_generalize: Create a pattern from multiple entries (Feature 015)
- rekall_sources_verify: Check URL accessibility (Feature 015)

Requires: pip install mcp
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from rekall.db import Database

logger = logging.getLogger(__name__)

# Check if MCP SDK is available
MCP_AVAILABLE = False
try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import TextContent, Tool

    MCP_AVAILABLE = True
except ImportError:
    pass


class MCPNotAvailable(Exception):
    """Raised when MCP SDK is not installed."""

    pass


# Help content for agents
REKALL_HELP = """# Rekall - Developer Knowledge Management

## Quick Start
1. Search before adding: `rekall_search(query="your topic")`
2. Add with context: `rekall_add(type, title, content, context="conversation context")`
3. Link related entries: `rekall_link(source_id, target_id)`

## When to Search
- Before solving a bug (check for similar issues)
- When implementing patterns (check existing patterns)
- When making decisions (check past decisions)

## When to Add
- After solving a bug: type="bug", include solution
- Discovering a pattern: type="pattern"
- Making a decision: type="decision", include rationale
- Configuration gotchas: type="config"

## Entry Types
- bug: Bug fixes and error solutions
- pattern: Reusable code patterns
- decision: Architecture/design decisions
- pitfall: Common mistakes to avoid
- config: Configuration and setup notes
- reference: External references and docs

## Tools Available

### Core Tools
- rekall_help: Get this usage guide
- rekall_search: Search the knowledge base
- rekall_show: Get full details of an entry
- rekall_add: Add a new entry with structured context
- rekall_link: Create a link between entries
- rekall_unlink: Remove a link between entries
- rekall_suggest: Get pending suggestions

### Discovery Tools
- rekall_related: Explore entries linked to a given entry (depth 1-3)
- rekall_similar: Find semantically similar entries (requires embeddings)
- rekall_info: Get knowledge base statistics

### Maintenance Tools
- rekall_stale: Find entries not accessed in N days
- rekall_generalize: Create a pattern from multiple entries

### Source Management
- rekall_sources_suggest: Suggest sources for an entry based on tags
- rekall_sources_verify: Check URL accessibility (link rot detection)

## Citation Format
When citing entries: [Title](rekall://entry_id)

## Tips
- Use --context for better semantic matching
- Check suggestions with rekall_suggest()
- Link related entries to build knowledge graph
- Use rekall_info() to get an overview of the knowledge base
- Use rekall_stale(days=90) to find maintenance candidates
"""


def get_db() -> Database:
    """Get database instance for MCP server."""
    from rekall.config import get_config
    from rekall.db import Database

    config = get_config()
    db = Database(config.db_path)
    db.init()
    return db


def create_mcp_server() -> Any:
    """Create and configure the MCP server.

    Returns:
        Configured MCP Server instance

    Raises:
        MCPNotAvailable: If MCP SDK is not installed
    """
    if not MCP_AVAILABLE:
        raise MCPNotAvailable(
            "MCP SDK not installed. Install with: pip install mcp"
        )

    server = Server("rekall")

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        """List available Rekall tools."""
        return [
            Tool(
                name="rekall_help",
                description="Get Rekall usage guide. Call this first to understand how to use Rekall effectively.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "topic": {
                            "type": "string",
                            "description": "Optional topic: search, add, links, all",
                            "enum": ["search", "add", "links", "all"],
                        }
                    },
                },
            ),
            Tool(
                name="rekall_search",
                description="Search the knowledge base. Returns compact results - use rekall_show for full content.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query",
                        },
                        "context": {
                            "type": "string",
                            "description": "Conversation context for better semantic matching",
                        },
                        "type": {
                            "type": "string",
                            "description": "Filter by type: bug, pattern, decision, pitfall, config, reference",
                        },
                        "project": {
                            "type": "string",
                            "description": "Filter by project name",
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Max results (default: 10)",
                            "default": 10,
                        },
                    },
                    "required": ["query"],
                },
            ),
            Tool(
                name="rekall_show",
                description="Get full details of an entry by ID. Use after search to get complete content.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "id": {
                            "type": "string",
                            "description": "Entry ID (full or prefix)",
                        },
                    },
                    "required": ["id"],
                },
            ),
            Tool(
                name="rekall_add",
                description="""Add a new knowledge entry with REQUIRED structured context.

## When to call rekall_add
AUTOMATICALLY after:
- Resolving a bug → type="bug"
- Discovering a reusable pattern → type="pattern"
- Making an architecture decision → type="decision"
- Avoiding a pitfall → type="pitfall"
- Configuring something tricky → type="config"

## Example call
rekall_add(
  type="bug",
  title="Fix 504 Gateway Timeout nginx",
  content="## Problem\\n504 on long requests...\\n## Solution\\n...",
  context={
    "situation": "API timeout on requests > 30s",
    "solution": "nginx proxy_read_timeout 120s",
    "trigger_keywords": ["504", "nginx", "timeout"],
    "what_failed": "Client-side timeout increase"
  }
)""",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "type": {
                            "type": "string",
                            "description": "Entry type",
                            "enum": ["bug", "pattern", "decision", "pitfall", "config", "reference"],
                        },
                        "title": {
                            "type": "string",
                            "description": "Entry title - concise, searchable",
                        },
                        "content": {
                            "type": "string",
                            "description": "Entry content (markdown) - detailed explanation",
                        },
                        "context": {
                            "type": "object",
                            "description": "REQUIRED: Structured context for disambiguation",
                            "properties": {
                                "situation": {
                                    "type": "string",
                                    "description": "What was the initial problem/context?",
                                },
                                "solution": {
                                    "type": "string",
                                    "description": "How was it resolved?",
                                },
                                "trigger_keywords": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "Keywords to find this entry later (3-5 recommended)",
                                },
                                "what_failed": {
                                    "type": "string",
                                    "description": "What was tried but didn't work?",
                                },
                                "conversation_excerpt": {
                                    "type": "string",
                                    "description": "Relevant excerpt from conversation",
                                },
                                "files_modified": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "Files that were modified",
                                },
                                "error_messages": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "Error messages encountered",
                                },
                            },
                            "required": ["situation", "solution", "trigger_keywords"],
                        },
                        "tags": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Tags for the entry",
                        },
                        "project": {
                            "type": "string",
                            "description": "Project name",
                        },
                        "confidence": {
                            "type": "integer",
                            "description": "Confidence level (0-5)",
                            "default": 2,
                        },
                    },
                    "required": ["type", "title", "context"],
                },
            ),
            Tool(
                name="rekall_link",
                description="Create a link between two entries to build knowledge graph. IMPORTANT: Always provide a reason to justify the relation_type choice.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "source_id": {
                            "type": "string",
                            "description": "Source entry ID",
                        },
                        "target_id": {
                            "type": "string",
                            "description": "Target entry ID",
                        },
                        "relation_type": {
                            "type": "string",
                            "description": "Relation type",
                            "enum": ["related", "supersedes", "derived_from", "contradicts"],
                            "default": "related",
                        },
                        "reason": {
                            "type": "string",
                            "description": "Justification for choosing this relation type. Example: 'B is a fix for bug A' or 'Pattern extracted from multiple bug fixes'",
                        },
                    },
                    "required": ["source_id", "target_id", "reason"],
                },
            ),
            Tool(
                name="rekall_suggest",
                description="Get pending suggestions for links and generalizations.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "type": {
                            "type": "string",
                            "description": "Filter by type: link, generalize",
                            "enum": ["link", "generalize"],
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Max suggestions (default: 10)",
                            "default": 10,
                        },
                    },
                },
            ),
            Tool(
                name="rekall_get_context",
                description="Get compressed context for entries. Use to verify if suggestion entries are truly related by reading their original context.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "entry_ids": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of entry IDs to get context for",
                        },
                    },
                    "required": ["entry_ids"],
                },
            ),
            # ===== Feature 015: MCP Tools Expansion =====
            Tool(
                name="rekall_unlink",
                description="Remove an existing link between two entries. Use to correct the knowledge graph.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "source_id": {
                            "type": "string",
                            "description": "Source entry ID of the link to remove",
                        },
                        "target_id": {
                            "type": "string",
                            "description": "Target entry ID of the link to remove",
                        },
                    },
                    "required": ["source_id", "target_id"],
                },
            ),
            Tool(
                name="rekall_related",
                description="Explore entries related to a given entry through links (incoming and outgoing).",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "entry_id": {
                            "type": "string",
                            "description": "Entry ID to explore relationships for",
                        },
                        "depth": {
                            "type": "integer",
                            "description": "Depth of graph traversal (default: 1, max: 3)",
                            "default": 1,
                        },
                    },
                    "required": ["entry_id"],
                },
            ),
            Tool(
                name="rekall_similar",
                description="Find semantically similar entries using embeddings. Requires smart_embeddings to be enabled.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "entry_id": {
                            "type": "string",
                            "description": "Reference entry ID to find similar entries for",
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of similar entries (default: 5)",
                            "default": 5,
                        },
                    },
                    "required": ["entry_id"],
                },
            ),
            Tool(
                name="rekall_sources_suggest",
                description="Suggest relevant web sources to enrich an entry based on its content and tags.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "entry_id": {
                            "type": "string",
                            "description": "Entry ID to suggest sources for",
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of suggestions (default: 5)",
                            "default": 5,
                        },
                    },
                    "required": ["entry_id"],
                },
            ),
            Tool(
                name="rekall_info",
                description="Get statistics about the knowledge base: entry counts, types, projects, links.",
                inputSchema={
                    "type": "object",
                    "properties": {},
                },
            ),
            Tool(
                name="rekall_stale",
                description="Find entries that haven't been accessed recently, suggesting maintenance candidates.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "days": {
                            "type": "integer",
                            "description": "Threshold in days of inactivity (default: 90)",
                            "default": 90,
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of results (default: 20)",
                            "default": 20,
                        },
                    },
                },
            ),
            Tool(
                name="rekall_generalize",
                description="Create a generalized pattern entry from multiple similar entries.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "entry_ids": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "IDs of entries to generalize (minimum 2)",
                        },
                        "title": {
                            "type": "string",
                            "description": "Title for the new pattern entry (auto-generated if omitted)",
                        },
                        "type": {
                            "type": "string",
                            "description": "Type of the new entry (default: pattern)",
                            "enum": ["pattern", "reference", "decision"],
                            "default": "pattern",
                        },
                    },
                    "required": ["entry_ids"],
                },
            ),
            Tool(
                name="rekall_sources_verify",
                description="Check accessibility of source URLs to detect link rot.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of URLs to check (default: 10)",
                            "default": 10,
                        },
                    },
                },
            ),
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict) -> list[TextContent]:
        """Handle tool calls."""
        try:
            if name == "rekall_help":
                return [TextContent(type="text", text=REKALL_HELP)]

            elif name == "rekall_search":
                return await _handle_search(arguments)

            elif name == "rekall_show":
                return await _handle_show(arguments)

            elif name == "rekall_add":
                return await _handle_add(arguments)

            elif name == "rekall_link":
                return await _handle_link(arguments)

            elif name == "rekall_suggest":
                return await _handle_suggest(arguments)

            elif name == "rekall_get_context":
                return await _handle_get_context(arguments)

            # ===== Feature 015: MCP Tools Expansion =====
            elif name == "rekall_unlink":
                return await _handle_unlink(arguments)

            elif name == "rekall_related":
                return await _handle_related(arguments)

            elif name == "rekall_similar":
                return await _handle_similar(arguments)

            elif name == "rekall_sources_suggest":
                return await _handle_sources_suggest(arguments)

            elif name == "rekall_info":
                return await _handle_info(arguments)

            elif name == "rekall_stale":
                return await _handle_stale(arguments)

            elif name == "rekall_generalize":
                return await _handle_generalize(arguments)

            elif name == "rekall_sources_verify":
                return await _handle_sources_verify(arguments)

            else:
                return [TextContent(type="text", text=f"Unknown tool: {name}")]

        except Exception as e:
            logger.exception(f"Error in tool {name}")
            return [TextContent(type="text", text=f"Error: {e}")]

    return server


async def _handle_search(args: dict) -> list:
    """Handle rekall_search tool call."""
    from mcp.types import TextContent

    db = get_db()
    query = args["query"]
    context = args.get("context")
    entry_type = args.get("type")
    project = args.get("project")
    limit = args.get("limit", 10)

    # Use hybrid search if context provided
    from rekall.config import get_config

    cfg = get_config()

    if cfg.smart_embeddings_enabled and context:
        from rekall.embeddings import get_embedding_service

        service = get_embedding_service()
        results = service.hybrid_search(
            query, db, context=context, limit=limit,
            entry_type=entry_type, project=project,
        )

        # Format results
        output = []
        for entry, _score, sem_score, matched_kws in results:
            snippet = (entry.content or "")[:100] + "..." if entry.content else ""
            # Build relevance info string
            info_parts = []
            if sem_score:
                info_parts.append(f"semantic: {sem_score:.0%}")
            if matched_kws:
                info_parts.append(f"keywords: {', '.join(matched_kws)}")
            relevance_info = f" ({'; '.join(info_parts)})" if info_parts else ""

            output.append(
                f"- [{entry.id}] {entry.type}: {entry.title}{relevance_info}\n"
                f"  Tags: {', '.join(entry.tags) if entry.tags else 'none'}\n"
                f"  {snippet}"
            )
    else:
        # FTS search
        results = db.search(query, entry_type=entry_type, project=project, limit=limit)
        output = []
        for result in results:
            entry = result.entry
            snippet = (entry.content or "")[:100] + "..." if entry.content else ""
            output.append(
                f"- [{entry.id}] {entry.type}: {entry.title}\n"
                f"  Tags: {', '.join(entry.tags) if entry.tags else 'none'}\n"
                f"  {snippet}"
            )

    db.close()

    if not output:
        return [TextContent(type="text", text="No results found.")]

    text = f"Found {len(output)} result(s):\n\n" + "\n\n".join(output)
    text += "\n\nHint: Use rekall_show(id) for full content."
    return [TextContent(type="text", text=text)]


async def _handle_show(args: dict) -> list:
    """Handle rekall_show tool call."""
    from mcp.types import TextContent

    db = get_db()
    entry_id = args["id"]

    entry = db.get(entry_id)
    if entry is None:
        # Try prefix match
        all_entries = db.list_all(limit=1000)
        matches = [e for e in all_entries if e.id.startswith(entry_id)]
        if len(matches) == 1:
            entry = matches[0]
        elif len(matches) > 1:
            db.close()
            return [TextContent(type="text", text=f"Multiple entries match '{entry_id}'. Be more specific.")]
        else:
            db.close()
            return [TextContent(type="text", text=f"Entry not found: {entry_id}")]

    # Get links
    outgoing = db.get_links(entry.id, direction="outgoing")
    incoming = db.get_links(entry.id, direction="incoming")
    db.close()

    output = f"""# {entry.title}

**ID:** {entry.id}
**Type:** {entry.type}
**Memory:** {entry.memory_type}
**Confidence:** {'★' * entry.confidence}{'☆' * (5 - entry.confidence)}
**Tags:** {', '.join(entry.tags) if entry.tags else 'none'}
**Project:** {entry.project or 'none'}
**Created:** {entry.created_at.strftime('%Y-%m-%d %H:%M')}

## Content

{entry.content or '(no content)'}
"""

    if outgoing or incoming:
        output += "\n## Links\n"
        for link in outgoing:
            output += f"- → [{link.relation_type}] {link.target_id}\n"
        for link in incoming:
            output += f"- ← [{link.relation_type}] {link.source_id}\n"

    return [TextContent(type="text", text=output)]


async def _handle_add(args: dict) -> list:
    """Handle rekall_add tool call."""
    from mcp.types import TextContent

    from rekall.config import get_config
    from rekall.models import Entry, StructuredContext, generate_ulid

    db = get_db()
    cfg = get_config()

    # Parse structured context (required in new schema)
    context_arg = args.get("context")
    structured_context = None
    context_text = None  # For legacy context compression

    if context_arg:
        # Handle structured context (dict) or legacy string
        if isinstance(context_arg, dict):
            # Validate required fields
            if not context_arg.get("situation"):
                db.close()
                return [TextContent(
                    type="text",
                    text="Error: context.situation is required. Describe the initial problem."
                )]
            if not context_arg.get("solution"):
                db.close()
                return [TextContent(
                    type="text",
                    text="Error: context.solution is required. Describe how it was resolved."
                )]
            # Auto-extract keywords if not provided
            trigger_keywords = context_arg.get("trigger_keywords", [])
            extraction_method = "manual"

            if not trigger_keywords:
                from rekall.context_extractor import extract_keywords

                # Extract from title, content, situation, solution
                text_for_extraction = " ".join([
                    args.get("title", ""),
                    args.get("content", ""),
                    context_arg.get("situation", ""),
                    context_arg.get("solution", ""),
                ])
                trigger_keywords = extract_keywords(
                    args.get("title", ""),
                    text_for_extraction,
                    max_keywords=5,
                )
                extraction_method = "auto"

            if not trigger_keywords:
                db.close()
                return [TextContent(
                    type="text",
                    text="Error: Could not extract keywords automatically. Provide trigger_keywords manually."
                )]

            try:
                structured_context = StructuredContext(
                    situation=context_arg["situation"],
                    solution=context_arg["solution"],
                    trigger_keywords=trigger_keywords,
                    what_failed=context_arg.get("what_failed"),
                    conversation_excerpt=context_arg.get("conversation_excerpt"),
                    files_modified=context_arg.get("files_modified"),
                    error_messages=context_arg.get("error_messages"),
                    extraction_method=extraction_method,
                )
                # Also create text for legacy compression
                context_text = f"Situation: {structured_context.situation}\nSolution: {structured_context.solution}"
            except ValueError as e:
                db.close()
                return [TextContent(type="text", text=f"Error in context: {e}")]
        else:
            # Legacy: string context (backwards compatibility)
            context_text = str(context_arg)
    else:
        # Context not provided - check if required
        context_mode = cfg.smart_embeddings_context_mode
        if context_mode == "required":
            db.close()
            return [TextContent(
                type="text",
                text="Error: context parameter is required. Provide structured context with situation, solution, and trigger_keywords."
            )]

    entry = Entry(
        id=generate_ulid(),
        title=args["title"],
        type=args["type"],
        content=args.get("content", ""),
        tags=args.get("tags", []),
        project=args.get("project"),
        confidence=args.get("confidence", 2),
    )

    db.add(entry)

    # Store structured context if provided (Feature 006)
    if structured_context:
        db.store_structured_context(entry.id, structured_context)

    # Store compressed context for legacy compatibility
    if context_text:
        db.store_context(entry.id, context_text)

    # Calculate embeddings if enabled
    similar_entries = []
    if cfg.smart_embeddings_enabled:
        from rekall.embeddings import get_embedding_service
        from rekall.models import Embedding

        service = get_embedding_service(
            dimensions=cfg.smart_embeddings_dimensions,
        )

        if service.available:
            embeddings = service.calculate_for_entry(entry, context=context_text)

            if embeddings["summary"] is not None:
                emb = Embedding.from_numpy(
                    entry.id, "summary", embeddings["summary"], service.model_name
                )
                db.add_embedding(emb)

            if embeddings["context"] is not None:
                emb = Embedding.from_numpy(
                    entry.id, "context", embeddings["context"], service.model_name
                )
                db.add_embedding(emb)

            # Find similar entries
            similar = service.find_similar(entry.id, db, limit=3)
            similar_entries = [(e.id, e.title, score) for e, score in similar]

    db.close()

    output = f"Entry created: {entry.id}\n"
    output += f"Type: {entry.type}\n"
    output += f"Title: {entry.title}\n"

    if similar_entries:
        output += "\nSimilar entries found:\n"
        for eid, title, score in similar_entries:
            output += f"- [{eid}] {title} ({score:.0%} similar)\n"
        output += "\nConsider using rekall_link to connect related entries."

    # Add info about structured context
    if structured_context:
        kw_info = ", ".join(structured_context.trigger_keywords[:3])
        if structured_context.extraction_method == "auto":
            output += f"\n✓ Structured context stored (auto-extracted keywords: {kw_info})"
        else:
            output += f"\n✓ Structured context stored with {len(structured_context.trigger_keywords)} keywords"
    elif not context_arg:
        output += "\n⚠ No context provided. Consider using structured context for better search."

    return [TextContent(type="text", text=output)]


async def _handle_link(args: dict) -> list:
    """Handle rekall_link tool call."""
    from mcp.types import TextContent

    db = get_db()
    source_id = args["source_id"]
    target_id = args["target_id"]
    relation_type = args.get("relation_type", "related")
    reason = args.get("reason")

    try:
        db.add_link(source_id, target_id, relation_type, reason=reason)
        db.close()
        output = f"Link created: {source_id} → [{relation_type}] → {target_id}"
        if reason:
            output += f"\nReason: {reason}"
        return [TextContent(type="text", text=output)]
    except ValueError as e:
        db.close()
        return [TextContent(type="text", text=f"Error: {e}")]


async def _handle_suggest(args: dict) -> list:
    """Handle rekall_suggest tool call."""
    from mcp.types import TextContent

    db = get_db()
    suggestion_type = args.get("type")
    limit = args.get("limit", 10)
    include_consolidation = args.get("include_consolidation", True)

    output_parts = []

    # Get existing suggestions from database
    suggestions = db.get_suggestions(
        status="pending",
        suggestion_type=suggestion_type,
        limit=limit,
    )

    if suggestions:
        output_parts.append("Pending suggestions:\n")
        for s in suggestions:
            entries = []
            for eid in s.entry_ids[:3]:
                entry = db.get(eid, update_access=False)
                if entry:
                    entries.append(f"{eid[:8]}...: {entry.title[:30]}")

            output_parts.append(f"- [{s.id}] {s.suggestion_type} ({s.score:.0%})")
            output_parts.append(f"  Entries: {', '.join(entries)}")
            if s.reason:
                output_parts.append(f"  Reason: {s.reason}")
            output_parts.append("")

    # Add keyword-based consolidation opportunities
    if include_consolidation:
        from rekall.consolidation import find_consolidation_opportunities

        opportunities = find_consolidation_opportunities(
            db, min_cluster_size=2, min_score=0.4
        )

        if opportunities:
            output_parts.append("Consolidation opportunities (by keywords):\n")
            for i, analysis in enumerate(opportunities[:5]):
                kw_list = ", ".join(analysis.common_keywords[:5])
                entry_titles = [e.title[:25] for e in analysis.entries[:3]]
                output_parts.append(
                    f"- Cluster {i+1} ({analysis.consolidation_score:.0%}): "
                    f"{analysis.suggested_title[:40]}"
                )
                output_parts.append(f"  Keywords: {kw_list}")
                output_parts.append(
                    f"  Entries ({len(analysis.entries)}): "
                    f"{', '.join(entry_titles)}"
                )
                output_parts.append("")

    db.close()

    if not output_parts:
        return [TextContent(type="text", text="No suggestions or consolidation opportunities found.")]

    output = "\n".join(output_parts)
    output += "\nUse rekall suggest --accept ID to accept a suggestion."
    return [TextContent(type="text", text=output)]


async def _handle_get_context(args: dict) -> list:
    """Handle rekall_get_context tool call."""
    from mcp.types import TextContent

    db = get_db()
    entry_ids = args["entry_ids"]

    contexts = db.get_contexts_for_verification(entry_ids)
    db.close()

    if not any(contexts.values()):
        return [TextContent(
            type="text",
            text="No context stored for these entries. Context is stored when entries are created with --context parameter."
        )]

    output = "Entry contexts for verification:\n\n"
    for entry_id in entry_ids:
        context = contexts.get(entry_id)
        if context:
            # Truncate very long contexts
            display_ctx = context[:2000] + "..." if len(context) > 2000 else context
            output += f"## Entry {entry_id[:12]}...\n"
            output += f"{display_ctx}\n\n"
        else:
            output += f"## Entry {entry_id[:12]}...\n"
            output += "(No context stored)\n\n"

    return [TextContent(type="text", text=output)]


# =============================================================================
# Feature 015: MCP Tools Expansion - Handlers
# =============================================================================


async def _handle_unlink(args: dict) -> list:
    """Handle rekall_unlink tool call - Remove a link between entries."""
    from mcp.types import TextContent

    db = get_db()
    source_id = args["source_id"]
    target_id = args["target_id"]

    try:
        success = db.delete_link(source_id, target_id)
        db.close()

        if success:
            return [TextContent(
                type="text",
                text=f"Link removed: {source_id} → {target_id}"
            )]
        else:
            return [TextContent(
                type="text",
                text=f"No link found between {source_id} and {target_id}"
            )]
    except Exception as e:
        db.close()
        return [TextContent(type="text", text=f"Error removing link: {e}")]


async def _handle_related(args: dict) -> list:
    """Handle rekall_related tool call - Explore related entries."""
    from mcp.types import TextContent

    db = get_db()
    entry_id = args["entry_id"]
    depth = min(args.get("depth", 1), 3)  # Cap at 3

    # Verify entry exists
    entry = db.get(entry_id, update_access=False)
    if not entry:
        db.close()
        return [TextContent(type="text", text=f"Entry not found: {entry_id}")]

    try:
        related = db.get_related_entries(entry_id, depth=depth)
        db.close()

        if not related:
            return [TextContent(
                type="text",
                text=f"No related entries found for {entry_id[:12]}..."
            )]

        output = f"Related entries for [{entry_id[:12]}...] {entry.title}:\n\n"

        for rel_entry, relation_type, direction in related:
            arrow = "→" if direction == "outgoing" else "←"
            output += f"- {arrow} [{relation_type}] [{rel_entry.id[:12]}...] {rel_entry.title}\n"
            output += f"    Type: {rel_entry.type} | Tags: {', '.join(rel_entry.tags[:3]) if rel_entry.tags else 'none'}\n"

        output += f"\nTotal: {len(related)} related entries (depth={depth})"
        return [TextContent(type="text", text=output)]

    except Exception as e:
        db.close()
        return [TextContent(type="text", text=f"Error exploring relationships: {e}")]


async def _handle_similar(args: dict) -> list:
    """Handle rekall_similar tool call - Find semantically similar entries."""
    from mcp.types import TextContent

    from rekall.config import get_config

    cfg = get_config()

    if not cfg.smart_embeddings_enabled:
        return [TextContent(
            type="text",
            text="Embeddings not enabled. Enable with: rekall config set smart_embeddings.enabled true\n"
                 "Then calculate embeddings: rekall embeddings calculate"
        )]

    db = get_db()
    entry_id = args["entry_id"]
    limit = args.get("limit", 5)

    # Verify entry exists
    entry = db.get(entry_id, update_access=False)
    if not entry:
        db.close()
        return [TextContent(type="text", text=f"Entry not found: {entry_id}")]

    try:
        from rekall.embeddings import get_embedding_service

        service = get_embedding_service(dimensions=cfg.smart_embeddings_dimensions)

        if not service.available:
            db.close()
            return [TextContent(
                type="text",
                text="Embedding service not available. Check model installation."
            )]

        similar = service.find_similar(entry_id, db, limit=limit)
        db.close()

        if not similar:
            return [TextContent(
                type="text",
                text=f"No similar entries found for [{entry_id[:12]}...] {entry.title}"
            )]

        output = f"Entries similar to [{entry_id[:12]}...] {entry.title}:\n\n"

        for sim_entry, score in similar:
            output += f"- [{sim_entry.id[:12]}...] {sim_entry.title} ({score:.0%} similar)\n"
            output += f"    Type: {sim_entry.type} | Tags: {', '.join(sim_entry.tags[:3]) if sim_entry.tags else 'none'}\n"

        output += f"\nTotal: {len(similar)} similar entries"
        return [TextContent(type="text", text=output)]

    except Exception as e:
        db.close()
        return [TextContent(type="text", text=f"Error finding similar entries: {e}")]


async def _handle_sources_suggest(args: dict) -> list:
    """Handle rekall_sources_suggest tool call - Suggest sources for an entry."""
    from mcp.types import TextContent

    db = get_db()
    entry_id = args["entry_id"]
    limit = args.get("limit", 5)

    # Get the entry
    entry = db.get(entry_id, update_access=False)
    if not entry:
        db.close()
        return [TextContent(type="text", text=f"Entry not found: {entry_id}")]

    try:
        # Get sources matching entry tags
        sources = []
        if entry.tags:
            for tag in entry.tags[:5]:  # Limit tag search
                tag_sources = db.get_sources_by_tags([tag], limit=limit)
                sources.extend(tag_sources)

        # Deduplicate by source ID
        seen_ids = set()
        unique_sources = []
        for source in sources:
            if source.id not in seen_ids:
                seen_ids.add(source.id)
                unique_sources.append(source)
                if len(unique_sources) >= limit:
                    break

        db.close()

        if not unique_sources:
            return [TextContent(
                type="text",
                text=f"No sources found matching tags for [{entry_id[:12]}...] {entry.title}\n"
                     f"Tags searched: {', '.join(entry.tags) if entry.tags else 'none'}"
            )]

        output = f"Suggested sources for [{entry_id[:12]}...] {entry.title}:\n\n"

        for source in unique_sources:
            score_display = f" (score: {source.score:.0f})" if source.score else ""
            output += f"- [{source.id[:12]}...] {source.title or source.domain}{score_display}\n"
            output += f"    URL: {source.url}\n"
            output += f"    Tier: {source.tier} | Tags: {', '.join(source.tags[:3]) if source.tags else 'none'}\n"

        output += f"\nTotal: {len(unique_sources)} suggested sources"
        return [TextContent(type="text", text=output)]

    except Exception as e:
        db.close()
        return [TextContent(type="text", text=f"Error suggesting sources: {e}")]


async def _handle_info(args: dict) -> list:
    """Handle rekall_info tool call - Get knowledge base statistics."""
    from mcp.types import TextContent

    db = get_db()

    try:
        # Get all entries for aggregation
        all_entries = db.list_all(limit=10000)

        # Count by type
        type_counts: dict[str, int] = {}
        project_counts: dict[str, int] = {}
        for entry in all_entries:
            type_counts[entry.type] = type_counts.get(entry.type, 0) + 1
            proj = entry.project or "(no project)"
            project_counts[proj] = project_counts.get(proj, 0) + 1

        # Get source statistics
        source_stats = db.get_source_statistics()

        # Count links
        link_count = 0
        try:
            cursor = db.conn.execute("SELECT COUNT(*) FROM links")
            link_count = cursor.fetchone()[0]
        except Exception:
            pass

        db.close()

        output = "# Rekall Knowledge Base Statistics\n\n"

        output += f"## Entries: {len(all_entries)}\n\n"
        output += "**By Type:**\n"
        for entry_type, count in sorted(type_counts.items(), key=lambda x: -x[1]):
            output += f"- {entry_type}: {count}\n"

        output += "\n**By Project:**\n"
        for project, count in sorted(project_counts.items(), key=lambda x: -x[1])[:10]:
            output += f"- {project}: {count}\n"

        output += f"\n## Links: {link_count}\n"

        output += f"\n## Sources: {source_stats.get('total', 0)}\n"
        output += f"- Bronze: {source_stats.get('bronze', 0)}\n"
        output += f"- Silver: {source_stats.get('silver', 0)}\n"
        output += f"- Gold: {source_stats.get('gold', 0)}\n"

        return [TextContent(type="text", text=output)]

    except Exception as e:
        db.close()
        return [TextContent(type="text", text=f"Error getting statistics: {e}")]


async def _handle_stale(args: dict) -> list:
    """Handle rekall_stale tool call - Find stale entries."""
    from mcp.types import TextContent

    db = get_db()
    days = args.get("days", 90)
    limit = args.get("limit", 20)

    try:
        stale_entries = db.get_stale_entries(days=days, limit=limit)
        db.close()

        if not stale_entries:
            return [TextContent(
                type="text",
                text=f"No entries inactive for more than {days} days. Knowledge base is well-maintained!"
            )]

        output = f"Entries not accessed in {days}+ days:\n\n"

        for entry in stale_entries:
            last_access = entry.last_accessed.strftime("%Y-%m-%d") if entry.last_accessed else "never"
            output += f"- [{entry.id[:12]}...] {entry.title}\n"
            output += f"    Type: {entry.type} | Last accessed: {last_access}\n"

        output += f"\nTotal: {len(stale_entries)} stale entries"
        output += "\n\nConsider: rekall deprecate <id> to mark obsolete entries"
        return [TextContent(type="text", text=output)]

    except Exception as e:
        db.close()
        return [TextContent(type="text", text=f"Error finding stale entries: {e}")]


async def _handle_generalize(args: dict) -> list:
    """Handle rekall_generalize tool call - Create pattern from entries."""
    from mcp.types import TextContent

    from rekall.models import Entry, generate_ulid

    entry_ids = args["entry_ids"]

    if len(entry_ids) < 2:
        return [TextContent(
            type="text",
            text="Error: At least 2 entry IDs are required for generalization"
        )]

    db = get_db()

    try:
        # Get all source entries
        source_entries = []
        for eid in entry_ids:
            entry = db.get(eid, update_access=False)
            if entry:
                source_entries.append(entry)
            else:
                db.close()
                return [TextContent(type="text", text=f"Entry not found: {eid}")]

        # Generate title if not provided
        title = args.get("title")
        if not title:
            # Combine keywords from titles
            words = set()
            for e in source_entries:
                words.update(e.title.split()[:3])
            title = f"Pattern: {' '.join(list(words)[:5])}"

        # Determine type
        entry_type = args.get("type", "pattern")

        # Create content summarizing sources
        content = f"## Generalized from {len(source_entries)} entries\n\n"
        content += "### Source Entries:\n"
        for e in source_entries:
            content += f"- [{e.id[:12]}...] {e.title} ({e.type})\n"

        # Collect common tags
        all_tags: dict[str, int] = {}
        for e in source_entries:
            for tag in e.tags:
                all_tags[tag] = all_tags.get(tag, 0) + 1
        common_tags = [t for t, c in all_tags.items() if c >= 2][:5]

        # Create the new entry
        new_entry = Entry(
            id=generate_ulid(),
            title=title,
            type=entry_type,
            content=content,
            tags=common_tags,
            project=source_entries[0].project if source_entries else None,
            confidence=3,
        )

        db.add(new_entry)

        # Create derived_from links
        for source in source_entries:
            db.add_link(
                new_entry.id,
                source.id,
                "derived_from",
                reason=f"Generalized from {len(source_entries)} entries"
            )

        db.close()

        output = f"Created generalized entry: {new_entry.id}\n"
        output += f"Title: {new_entry.title}\n"
        output += f"Type: {new_entry.type}\n"
        output += f"Tags: {', '.join(new_entry.tags) if new_entry.tags else 'none'}\n"
        output += f"\nLinked to {len(source_entries)} source entries via 'derived_from'"

        return [TextContent(type="text", text=output)]

    except Exception as e:
        db.close()
        return [TextContent(type="text", text=f"Error creating generalized entry: {e}")]


async def _handle_sources_verify(args: dict) -> list:
    """Handle rekall_sources_verify tool call - Check source URL accessibility."""
    from mcp.types import TextContent

    db = get_db()
    limit = args.get("limit", 10)

    try:
        # Get sources to verify
        sources_to_check = db.get_sources_to_verify(limit=limit)

        if not sources_to_check:
            db.close()
            return [TextContent(
                type="text",
                text="No sources need verification. All sources were checked recently."
            )]

        # Import link rot checker
        from rekall.link_rot import LinkRotChecker

        checker = LinkRotChecker()
        results = []

        for source in sources_to_check:
            is_accessible, status_msg = checker.check_url(source.url)
            results.append({
                "source": source,
                "accessible": is_accessible,
                "status": status_msg,
            })

            # Update source status in DB
            new_status = "accessible" if is_accessible else "broken"
            db.update_source_status(source.id, new_status)

        db.close()

        # Format output
        accessible_count = sum(1 for r in results if r["accessible"])
        broken_count = len(results) - accessible_count

        output = f"# Link Rot Check Results\n\n"
        output += f"Checked: {len(results)} URLs\n"
        output += f"Accessible: {accessible_count} | Broken: {broken_count}\n\n"

        if broken_count > 0:
            output += "## Broken URLs:\n"
            for r in results:
                if not r["accessible"]:
                    source = r["source"]
                    output += f"- [{source.id[:12]}...] {source.title or source.domain}\n"
                    output += f"    URL: {source.url}\n"
                    output += f"    Status: {r['status']}\n"

        if accessible_count > 0:
            output += "\n## Accessible URLs:\n"
            for r in results:
                if r["accessible"]:
                    source = r["source"]
                    output += f"- [{source.id[:12]}...] {source.title or source.domain} ✓\n"

        return [TextContent(type="text", text=output)]

    except Exception as e:
        db.close()
        return [TextContent(type="text", text=f"Error verifying sources: {e}")]


async def run_server() -> None:
    """Run the MCP server."""
    if not MCP_AVAILABLE:
        raise MCPNotAvailable(
            "MCP SDK not installed. Install with: pip install mcp"
        )

    server = create_mcp_server()
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())
