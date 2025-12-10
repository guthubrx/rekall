# MCP Integration Guide

Connect Rekall to your AI-powered development tools using the Model Context Protocol (MCP).

## What is MCP?

[Model Context Protocol](https://modelcontextprotocol.io/) is an open standard that lets AI assistants connect to external tools and data sources. Rekall implements an MCP server that exposes your knowledge base to any compatible AI assistant.

## Quick Start

```bash
# Start the MCP server
rekall mcp
```

That's it. Rekall is now available to any MCP-compatible tool.

## Supported Tools

| Tool | Support | Configuration |
|------|---------|---------------|
| **Claude Code** | ✅ Native | Auto-detected via MCP |
| **Claude Desktop** | ✅ Native | Add to config file |
| **Cursor** | ✅ Supported | MCP settings |
| **Windsurf** | ✅ Supported | MCP settings |
| **Continue.dev** | ✅ Supported | MCP configuration |
| **Any MCP client** | ✅ Compatible | Standard MCP protocol |

---

## Claude Desktop

### Configuration

Add Rekall to your Claude Desktop config file:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
**Linux**: `~/.config/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "rekall": {
      "command": "rekall",
      "args": ["mcp"]
    }
  }
}
```

### Restart Claude Desktop

After saving the config, restart Claude Desktop. You should see "rekall" in the MCP servers list.

### Usage

Ask Claude:
- "Search my knowledge for CORS errors"
- "What bugs have I fixed related to authentication?"
- "Save this solution to my knowledge base"

---

## Claude Code (CLI)

Claude Code automatically detects MCP servers. Just ensure Rekall is in your PATH:

```bash
# Verify Rekall is accessible
which rekall

# Claude Code will auto-detect it
claude
```

### Usage in Claude Code

```
You: Fix this CORS error
Claude: Let me check your knowledge base first...

🔍 Searching your knowledge...
Found 2 relevant entries:
[1] bug: CORS fails on Safari (85% match)
    → You solved this 3 months ago

Based on your past experience, you should add credentials: 'include'...
```

---

## Cursor

### Configuration

1. Open Cursor Settings (Cmd/Ctrl + ,)
2. Navigate to "MCP" or "Extensions" section
3. Add new MCP server:

```json
{
  "name": "rekall",
  "command": "rekall",
  "args": ["mcp"]
}
```

### Usage

Use the `@rekall` mention in Cursor to query your knowledge:

```
@rekall search "database connection issues"
```

---

## Windsurf

### Configuration

Add to your Windsurf MCP configuration:

```json
{
  "mcpServers": {
    "rekall": {
      "command": "rekall",
      "args": ["mcp"],
      "transport": "stdio"
    }
  }
}
```

---

## Continue.dev

### Configuration

Add to your Continue config (`~/.continue/config.json`):

```json
{
  "mcpServers": [
    {
      "name": "rekall",
      "command": "rekall",
      "args": ["mcp"]
    }
  ]
}
```

---

## MCP Server Capabilities

Rekall's MCP server exposes these tools to AI assistants:

### `rekall_search`

Search the knowledge base.

**Parameters:**
- `query` (string): Search query
- `type` (string, optional): Filter by entry type
- `limit` (int, optional): Max results (default: 5)

**Returns:**
```json
{
  "entries": [
    {
      "id": "01HX7...",
      "type": "bug",
      "title": "CORS fails on Safari",
      "score": 0.85,
      "snippet": "Add credentials: include...",
      "tags": ["cors", "safari"],
      "created_at": "2024-01-15T14:32:00Z"
    }
  ],
  "hint": "Use rekall_get_entry for full details"
}
```

### `rekall_get_entry`

Get full details of an entry.

**Parameters:**
- `id` (string): Entry ID

**Returns:**
```json
{
  "id": "01HX7...",
  "type": "bug",
  "title": "CORS fails on Safari",
  "content": "Full content...",
  "context": {
    "situation": "Safari blocks requests...",
    "solution": "Add credentials: include...",
    "what_failed": "Just CORS headers alone"
  },
  "tags": ["cors", "safari"],
  "links": ["01HY8..."],
  "created_at": "2024-01-15T14:32:00Z",
  "accessed_count": 12,
  "consolidation_score": 0.85
}
```

### `rekall_add_entry`

Create a new entry.

**Parameters:**
- `type` (string): Entry type
- `title` (string): Entry title
- `content` (string, optional): Entry content
- `tags` (array, optional): Tags
- `context` (object, optional): Structured context

**Returns:**
```json
{
  "id": "01HZ9...",
  "message": "Entry created successfully"
}
```

### `rekall_link_entries`

Link two related entries.

**Parameters:**
- `source_id` (string): Source entry ID
- `target_id` (string): Target entry ID
- `relation` (string): Relation type (`related`, `derived_from`, `supersedes`, `contradicts`)

---

## Token Efficiency

Rekall's MCP server is designed for minimal token usage:

| Operation | Tokens Used |
|-----------|-------------|
| Search (5 results) | ~200 tokens |
| Get entry | ~100-300 tokens |
| Add entry | ~50 tokens |

Compared to including full knowledge in the prompt (~5000+ tokens), MCP integration reduces token usage by **~95%**.

---

## Troubleshooting

### "rekall command not found"

Ensure Rekall is in your PATH:

```bash
# Check if rekall is accessible
which rekall

# If not found, add to PATH or use full path in MCP config
{
  "command": "/full/path/to/rekall",
  "args": ["mcp"]
}
```

### "MCP server not responding"

1. Test the server manually:
   ```bash
   rekall mcp
   # Should start without errors
   ```

2. Check for port conflicts:
   ```bash
   lsof -i :8080  # If using HTTP transport
   ```

3. Try stdio transport:
   ```json
   {
     "command": "rekall",
     "args": ["mcp", "--stdio"]
   }
   ```

### "No entries found"

1. Verify you have entries:
   ```bash
   rekall search ""  # List all entries
   ```

2. Check database location:
   ```bash
   rekall config get data_dir
   ```

---

## Best Practices

### 1. Use Structured Context

When adding entries via AI, include structured context:

```
Save this bug fix: CORS fails on Safari
Situation: Safari blocks fetch even with headers
Solution: Add credentials: 'include'
Tags: cors, safari, fetch
```

### 2. Let AI Suggest Links

Ask your AI to find related entries:

```
"Check if this bug is related to anything in my knowledge base"
```

### 3. Regular Reviews

Ask your AI to remind you about stale knowledge:

```
"What knowledge haven't I reviewed in 3 months?"
```

---

## Security

- **Local only**: MCP server only exposes your local database
- **No network**: By default, MCP uses stdio (no network ports)
- **Read-heavy**: AI can search and read; writes require explicit confirmation
- **No secrets**: Never store API keys or passwords in Rekall
