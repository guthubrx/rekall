# Changelog

All notable changes to Rekall will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.3.0] - 2025-12-10

### Added
- **Feature 007: Migration & Maintenance**
  - `rekall migrate` command with automatic backup
  - `rekall migrate --dry-run` for preview mode
  - `rekall migrate --enrich-context` to add structured context to legacy entries
  - `rekall changelog` command to display version history
  - Schema version display in `rekall version`
  - Migration detection in `rekall version`
  - TUI migration overlay with one-click upgrade
  - TUI Settings screen (context_mode, max_context_size)
  - Context compression with zlib for storage optimization
  - Keywords index table for fast search on compressed data

### Changed
- Database schema version 7 (from 6)
- Default `context_mode` is now `required` (was `optional`)
- CLI and MCP Server enforce context requirement by default
- Structured context stored as compressed BLOB

## [0.2.0] - 2025-12-09

### Added
- **Feature 006: Enriched Context System**
  - `StructuredContext` model with situation, solution, trigger_keywords
  - `--context-json` flag for CLI entries
  - `--context-interactive` mode for guided context input
  - Hybrid search with keyword matching (FTS 50% + Semantic 30% + Keywords 20%)
  - `context_extractor.py` module for keyword extraction
  - `consolidation.py` module for cluster analysis

- **Feature 005: Smart Embeddings**
  - Local EmbeddingGemma-2B-v1 model support
  - Semantic search with cosine similarity
  - `rekall embeddings --status` and `--migrate` commands
  - Suggestion system for links and generalizations

- **Cognitive Memory System**
  - Memory types: episodic (events) and semantic (patterns)
  - Consolidation scoring for knowledge retention
  - Spaced repetition with SM-2 algorithm
  - `rekall review` command for review sessions
  - `rekall stale` command to find forgotten knowledge

- **Knowledge Graph**
  - Entry linking with relation types (related, supersedes, derived_from, contradicts)
  - `rekall link`, `rekall unlink`, `rekall related` commands
  - `rekall graph` for ASCII visualization
  - Reason field for link justification

- **MCP Server**
  - Model Context Protocol integration for AI agents
  - Tools: rekall_search, rekall_add, rekall_show, rekall_link, rekall_suggest
  - Smart suggestions based on embeddings

### Changed
- Database schema version 6 (from 0)
- Enhanced TUI with structured context display
- Improved search with multi-component scoring

## [0.1.0] - 2025-12-08

### Added
- Initial release
- Core entry management (add, search, show, browse)
- Entry types: bug, pattern, decision, pitfall, config, reference
- Full-text search with FTS5
- Tags and project filtering
- Export/Import with .rekall.zip archives
- XDG Base Directory support
- TUI interface with Textual
- IDE integrations (Cursor, Claude, Copilot)
- Research documents browser

---

## Schema Versions

| Version | Changes |
|---------|---------|
| 7 | Context BLOB compression + keywords index table |
| 6 | Structured context JSON (context_structured) |
| 5 | Link reason field |
| 4 | Context compression (context_compressed) |
| 3 | Embeddings, suggestions, metadata tables |
| 2 | Links table for knowledge graph |
| 1 | Cognitive memory fields (memory_type, access tracking) |
| 0 | Initial schema (entries, tags, FTS5) |
