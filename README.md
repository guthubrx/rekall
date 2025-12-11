<div align="center">

<!-- LOGO: Uncomment when logo.png is ready
<img src="docs/images/logo.png" alt="Rekall Logo" width="120">
-->

# Rekall

**Your developer knowledge, instantly recalled.**

<p>
  <img src="https://img.shields.io/badge/100%25-Local-blue?style=flat-square" alt="100% Local">
  <img src="https://img.shields.io/badge/No_API_Keys-green?style=flat-square" alt="No API Keys">
  <img src="https://img.shields.io/badge/MCP-Compatible-purple?style=flat-square" alt="MCP Compatible">
  <img src="https://img.shields.io/badge/Python-3.9+-yellow?style=flat-square" alt="Python 3.9+">
</p>

*"Get your ass to Mars. Quaid... crush those bugs"*

[Documentation](#contents) · [Install](#getting-started) · [MCP Integration](#mcp-server-works-with-any-ai-assistant)

**Translations:** [Français](README.fr.md) | [Español](README.es.md) | [Deutsch](README.de.md) | [中文](README.zh-CN.md)

</div>

---

## Contents

- [TL;DR](#tldr)
- [The Problem](#youve-already-solved-this-problem)
- [The Solution](#what-if-your-ai-assistant-remembered-for-you)
- [How It Works](#how-it-works-in-practice)
- [Interface](#the-interface)
- [What It Automates](#what-rekall-does-for-you)
- [Entry Types](#what-can-you-capture)
- [Sources](#track-your-sources)
- [Privacy](#100-local-100-yours)
- [Getting Started](#getting-started)
- [MCP Server](#mcp-server-works-with-any-ai-assistant)
- [Speckit Integration](#speckit-integration)
- [Under the Hood](#under-the-hood-how-search-works) *(technical)*
- [Built on Science](#built-on-science) *(research)*

---

### TL;DR

**The problem:** Every developer has solved the same bug twice. Not because they're careless — because humans forget. Research shows Fortune 500 companies lose $31.5 billion annually to knowledge that's never captured.

**Our approach:** Rekall is a personal knowledge base built on cognitive science research. We studied how human memory actually works — episodic vs semantic memory, spaced repetition, knowledge graphs — and applied it to developer workflows.

**What it does:** Capture bugs, patterns, decisions, configs as you work. Search by meaning, not just keywords — Rekall uses optional local embeddings (EmbeddingGemma) combined with full-text search to find relevant entries even when your words don't match exactly. Store rich context (situation, solution, what failed) to disambiguate similar problems later.

**Works with your tools:** Rekall exposes an MCP server compatible with most AI-powered development tools — Claude Code, Claude Desktop, Cursor, Windsurf, Continue.dev, and any MCP-compatible client. One command (`rekall mcp`) and your AI consults your knowledge before every fix.

**What it automates:** Keyword extraction, consolidation scoring, pattern detection, link suggestions, review scheduling (SM-2 spaced repetition). You focus on capturing — Rekall handles the rest.

```bash
# Install
uv tool install git+https://github.com/guthubrx/rekall.git

# Capture (interactive mode guides you)
rekall add bug "CORS fails on Safari" --context-interactive

# Search (understands meaning, not just keywords)
rekall search "browser blocking API"

# Connect to AI (one command, works with Claude/Cursor/Windsurf)
rekall mcp
```

---

<br>

## You've already solved this problem.

Three months ago, you spent two hours debugging a cryptic error. You found the fix. You moved on.

Today, the same error appears. You stare at it. It looks familiar. But where was that solution again?

You start from scratch. Another two hours gone.

**This happens to every developer.** According to research, Fortune 500 companies lose $31.5 billion annually because lessons learned are never captured. Not because people are careless — but because we're human, and humans forget.

<br>

## What if your AI assistant remembered for you?

Imagine this: you ask Claude or Cursor to fix a bug. Before writing a single line of code, it checks your personal knowledge base:

```
🔍 Searching your knowledge...

Found 2 relevant entries:

[1] bug: CORS error on Safari (85% match)
    "Add credentials: include and proper Access-Control headers"
    → You solved this 3 months ago

[2] pattern: Cross-origin request handling (72% match)
    "Always test on Safari - it has stricter CORS enforcement"
    → Pattern extracted from 4 similar bugs
```

Your AI assistant now has context. It knows what worked before. It won't reinvent the wheel — it'll build on your past experience.

**That's Rekall.**

<p align="center">
  <img src="docs/screenshots/demo.gif" alt="Rekall in action" width="700">
</p>

<!--
Screenshots placeholder - add your images to docs/screenshots/
Options:
- demo.gif: Animated GIF showing the workflow (recommended)
- tui.png: Terminal UI screenshot
- search.png: Search results
- mcp.png: MCP integration with Claude/Cursor
-->

<br>

## A second brain that thinks like you do

> **Key idea:** Rekall is built on how human memory actually works — connecting related knowledge, extracting patterns from episodes, and surfacing forgotten information before it fades.

Rekall isn't just a note-taking app. It's built on how human memory actually works:

### Your knowledge, connected

When you solve something, related knowledge surfaces automatically. Fixed a timeout bug? Rekall shows you the three other timeout issues you've solved and the retry pattern you extracted from them.

```
              ┌──────────────┐
              │ Auth Timeout │
              │   (today)    │
              └──────┬───────┘
                     │ similar to...
        ┌────────────┼────────────┐
        ▼            ▼            ▼
  ┌──────────┐ ┌──────────┐ ┌──────────┐
  │ DB #47   │ │ API #52  │ │ Cache #61│
  │ (2 weeks)│ │ (1 month)│ │(3 months)│
  └────┬─────┘ └────┬─────┘ └──────────┘
       └──────┬─────┘
              ▼
     ┌─────────────────┐
     │ PATTERN: Retry  │
     │ with backoff    │
     └─────────────────┘
```

### Events become wisdom

Every bug you fix is an **episode** — a specific event with context. But patterns emerge. After fixing three similar timeout bugs, Rekall helps you extract the **principle**: "Always add retry with exponential backoff for external APIs."

Episodes are raw material. Patterns are reusable knowledge.

<br>

### Forgotten knowledge resurfaces

Rekall tracks what you access and when. Knowledge you haven't touched in months? It'll remind you before it fades completely. Think of it as spaced repetition for your dev brain.

---

## How it works in practice

### 1. Capture knowledge as you work

After solving something tricky, capture it in 10 seconds:

```bash
rekall add bug "CORS fails on Safari" --context-interactive
```

Rekall asks: *What was happening? What fixed it? What keywords should trigger this?*

```
> Situation: Safari blocks requests even with CORS headers set
> Solution: Add credentials: 'include' and explicit Allow-Origin
> Keywords: cors, safari, cross-origin, fetch, credentials
```

Done. Your future self will thank you.

### 2. Search by meaning, not just keywords

Can't remember if you called it "CORS" or "cross-origin"? Doesn't matter.

```bash
rekall search "browser blocking my API calls"
```

Rekall understands meaning. It finds relevant entries even when your words don't match exactly.

### 3. Let your AI assistant use it

Connect Rekall to Claude, Cursor, or any AI that supports MCP:

```bash
rekall mcp  # Start the server
```

Now your AI consults your knowledge before every fix. It cites your past solutions. It suggests saving new ones. Your knowledge compounds over time.

---

## The interface

### Terminal UI
```bash
rekall  # Launch the visual interface
```

```
┌─ Rekall ────────────────────────────────────────────────┐
│     Search: cors safari                                 │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  [1] bug: CORS fails on Safari              85% ██████  │
│      safari, cors, fetch  •  3 months ago               │
│      "Add credentials: include..."                      │
│                                                         │
│  [2] pattern: Cross-origin handling         72% █████   │
│      architecture  •  1 month ago                       │
│      "Safari has stricter CORS enforcement"             │
│                                                         │
│  [3] reference: MDN CORS guide              68% ████    │
│      docs, mdn  •  6 months ago                         │
│                                                         │
├─────────────────────────────────────────────────────────┤
│  [/] Search  [a] Add  [Enter] View  [q] Quit            │
└─────────────────────────────────────────────────────────┘
```

### Command line
```bash
rekall add bug "Fix: null pointer in auth" -t auth,null
rekall search "authentication error"
rekall show 01HX7...
rekall link 01HX7 01HY2 --type related
rekall review  # Spaced repetition session
```

<br>

## What Rekall does for you

> **Philosophy:** You focus on capturing knowledge. Rekall handles everything else.

### On every entry you add

- **Keyword extraction** — Analyzes your title and content, suggests relevant keywords
- **Context validation** — Warns if situation/solution is too vague or generic
- **Embedding generation** — Creates semantic vectors for intelligent search (if enabled)
- **Automatic indexing** — Full-text search index updated in real-time

### On every search

- **Hybrid matching** — Combines exact words (FTS5) + meaning (embeddings) + triggers (keywords)
- **No configuration** — Works out of the box, no tuning needed
- **Related entries** — Shows linked knowledge automatically

### In the background (you do nothing)

- **Access tracking** — Every view updates frequency and recency stats
- **Consolidation scoring** — Calculates how "stable" each memory is (60% frequency + 40% freshness)
- **Pattern detection** — Finds clusters of similar entries, suggests creating a pattern
- **Link suggestions** — Detects related entries, proposes connections
- **Review scheduling** — SM-2 algorithm plans optimal review times (spaced repetition)
- **Context compression** — Stores verbose context at 70-85% smaller size

### When you run `rekall review`

- **Loads due entries** — Based on SM-2 scheduling, not arbitrary dates
- **Adjusts difficulty** — Your rating (0-5) updates the ease factor automatically
- **Reschedules** — Calculates next optimal review date

---

## What can you capture?

| Type | For | Example |
|------|-----|---------|
| `bug` | Problems you've solved | "Safari CORS with credentials" |
| `pattern` | Reusable approaches | "Retry with exponential backoff" |
| `decision` | Why you chose X over Y | "PostgreSQL over MongoDB for this project" |
| `pitfall` | Mistakes to avoid | "Never use SELECT * in production" |
| `config` | Setup that works | "VS Code Python debugging config" |
| `reference` | Useful docs/links | "That one StackOverflow answer" |
| `snippet` | Code worth keeping | "Generic debounce function" |
| `til` | Quick learnings | "Git rebase -i can reorder commits" |

---

## Track your sources

> **Philosophy:** Every piece of knowledge came from somewhere. Rekall helps you track *where* — so you can evaluate reliability, revisit original sources, and see which sources are most valuable to you.

### Link entries to their sources

When you capture knowledge, you can attach sources:

```bash
# Add a bug with a URL source
rekall add bug "Safari CORS fix" -t cors,safari
# Then link the source URL
rekall source link 01HX7... --url "https://stackoverflow.com/q/12345"

# Or use the TUI: open entry → Add source
rekall
```

### Three source types

| Type | For | Example |
|------|-----|---------|
| `url` | Web pages, documentation | Stack Overflow, MDN, blog posts |
| `theme` | Recurring topics or mentors | "Code reviews with Alice", "Architecture meetings" |
| `file` | Local documents | PDFs, internal docs, notes |

### Reliability ratings (Admiralty System)

Not all sources are equally trustworthy. Rekall uses a simplified **Admiralty System**:

| Rating | Meaning | Examples |
|--------|---------|----------|
| **A** | Highly reliable, authoritative | Official docs, peer-reviewed, known experts |
| **B** | Generally reliable | Reputable blogs, SO accepted answers |
| **C** | Questionable or unverified | Random forum posts, untested suggestions |

### Personal score: What matters *to you*

Each source gets a **personal score** (0-100) based on:

```
Score = Usage × Recency × Reliability

- Usage: How often you cite this source
- Recency: When you last used it (decays over time)
- Reliability: A=1.0, B=0.8, C=0.6
```

Sources you use frequently and recently rank higher — regardless of how "authoritative" they are globally. Your personal experience matters.

### Backlinks: See all entries from a source

Click any source to see all entries that reference it:

```
┌─ Source: stackoverflow.com/questions/* ─────────────────┐
│  Reliability: B  │  Score: 85  │  Used: 12 times        │
├─────────────────────────────────────────────────────────┤
│  Entries citing this source:                            │
│                                                         │
│  [1] bug: CORS fails on Safari                          │
│  [2] bug: Fetch timeout on slow networks                │
│  [3] pattern: Error handling for API calls              │
└─────────────────────────────────────────────────────────┘
```

### Link rot detection

Web sources can go offline. Rekall periodically checks URL sources and flags inaccessible ones:

```bash
rekall sources --verify  # Check all sources
rekall sources --status inaccessible  # List broken links
```

The TUI Sources dashboard shows:
- **Top sources** by personal score
- **Emerging sources** (recently cited multiple times)
- **Dormant sources** (not used in 6+ months)
- **Inaccessible sources** (link rot detected)

---

## 100% local. 100% yours.

```
Your machine
     │
     ▼
┌─────────────────────────────────────┐
│  ~/.local/share/rekall/             │
│                                     │
│  Everything stays here.             │
│  No cloud. No account. No tracking. │
│                                     │
└─────────────────────────────────────┘
     │
     ▼
  Nowhere else. Ever.
```

Your knowledge is yours. Rekall doesn't phone home. It doesn't require an account. It works offline. Your debugging history, your architectural decisions, your hard-won wisdom — all private, all local.

---

## Getting started

### Install

```bash
# With uv (recommended)
uv tool install git+https://github.com/guthubrx/rekall.git

# With pipx
pipx install git+https://github.com/guthubrx/rekall.git
```

### Try it

```bash
# Add your first entry
rekall add bug "My first captured bug" -t test

# Search it
rekall search "first"

# Open the visual interface
rekall
```

---

## MCP Server: Works with any AI assistant

Rekall exposes your knowledge base via the **Model Context Protocol (MCP)** — the open standard for connecting AI assistants to external tools.

### One command, universal access

```bash
rekall mcp  # Start the MCP server
```

### Compatible with major AI tools

| Tool | Status | Configuration |
|------|--------|---------------|
| **Claude Code** | ✅ Native | Auto-detected |
| **Claude Desktop** | ✅ Native | Add to `claude_desktop_config.json` |
| **Cursor** | ✅ Supported | MCP settings |
| **Windsurf** | ✅ Supported | MCP settings |
| **Continue.dev** | ✅ Supported | MCP configuration |
| **Any MCP client** | ✅ Compatible | Standard MCP protocol |

### Configuration example (Claude Desktop)

Add to your `claude_desktop_config.json`:

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

### What your AI can do

Once connected, your AI assistant can:

- **Search** your knowledge base before answering
- **Cite** your past solutions in its responses
- **Suggest** capturing new knowledge after solving problems
- **Link** related entries automatically
- **Surface** patterns across your debugging history

Your knowledge compounds automatically — the more you use it, the smarter it gets.

---

## Integrate with Speckit

[Speckit](https://github.com/YOUR_USERNAME/speckit) is a specification-driven development toolkit. Combined with Rekall, it creates a powerful workflow where your specifications feed your knowledge base.

### Why integrate?

- **Specs become searchable knowledge**: Decisions made during spec writing are captured
- **Patterns emerge**: Common architectural choices surface across projects
- **Context preserved**: The "why" behind specs is never lost

### Setup

1. Install both tools:
```bash
uv tool install git+https://github.com/guthubrx/rekall.git
uv tool install git+https://github.com/YOUR_USERNAME/speckit.git
```

2. Configure Speckit to use Rekall (in your `.speckit/config.yaml`):
```yaml
integrations:
  rekall:
    enabled: true
    auto_capture: true  # Automatically capture decisions
    types:
      - decision
      - pattern
      - pitfall
```

3. During spec work, Speckit will:
   - Query Rekall for relevant past decisions
   - Suggest capturing new architectural choices
   - Link specs to related knowledge entries

### Example workflow

```bash
# Start specifying a feature
speckit specify "User authentication system"

# Speckit queries Rekall: "Have you made auth decisions before?"
# → Shows your past OAuth vs JWT decision from another project

# After finalizing the spec
speckit plan

# Rekall captures: decision "JWT for stateless auth in microservices"
```

<br>

<details>
<summary><h2>Under the hood: How search works</h2></summary>

> **TL;DR:** Hybrid search combining FTS5 (50%) + semantic embeddings (30%) + keywords (20%). Optional local model, no API keys.

Rekall doesn't just do keyword matching. It understands what you mean.

### The problem with simple search

You captured a bug about "CORS error on Safari." Later, you search for "browser blocking API calls." A simple keyword search finds nothing — the words don't match.

### Hybrid search: exhaustive AND fast

Rekall combines three search strategies:

```
┌──────────────────────────────────────────────────────────────┐
│                     YOUR QUERY                               │
│              "browser blocking API calls"                    │
└──────────────────────────────────┬───────────────────────────┘
                                   │
           ┌───────────────────────┼───────────────────────┐
           ▼                       ▼                       ▼
    ┌─────────────┐        ┌─────────────┐        ┌─────────────┐
    │   FTS5      │        │  Semantic   │        │  Keywords   │
    │  (50%)      │        │   (30%)     │        │   (20%)     │
    │             │        │             │        │             │
    │ Exact word  │        │ Meaning via │        │ Structured  │
    │ matching    │        │ embeddings  │        │ triggers    │
    └──────┬──────┘        └──────┬──────┘        └──────┬──────┘
           │                      │                      │
           └───────────────────────┼───────────────────────┘
                                   ▼
                        ┌─────────────────┐
                        │  FINAL SCORE    │
                        │  85% match      │
                        └─────────────────┘
```

- **Full-text search (50%)**: SQLite FTS5 finds exact and partial word matches
- **Semantic search (30%)**: Embeddings find conceptually similar content — "browser" matches "Safari", "blocking" matches "CORS error"
- **Keywords index (20%)**: Your structured context keywords provide explicit triggers

### Local embeddings: Optional but powerful

Semantic search is **optional**. Rekall works perfectly with FTS5 full-text search alone — no model required.

But if you want semantic understanding, Rekall uses **EmbeddingGemma** (308M parameters), a state-of-the-art embedding model that runs entirely on your machine:

- **100% local**: No data leaves your computer, no API keys, no cloud
- **Multilingual**: Works in 100+ languages
- **Fast**: ~500ms per embedding on a standard laptop CPU
- **Small**: ~200MB RAM with int8 quantization

```bash
# FTS-only mode (default, no model needed)
rekall search "CORS error"

# Enable semantic search (downloads model on first use)
rekall config set embeddings.enabled true
```

### Double embedding: Context matters

When you capture knowledge, Rekall stores two embeddings:

1. **Summary embedding**: Title + content + tags — for focused searches
2. **Context embedding**: The full situation/solution — for exploratory searches

This solves a fundamental problem in retrieval: summaries lose context. If you search "stack trace Safari", the summary "Fix CORS" won't match — but the full context you captured (which mentions the stack trace) will.

### Structured context: Disambiguation that works

You've fixed 5 different "timeout" bugs. How do you find the right one later? Keywords alone won't help — they're all tagged "timeout".

Rekall captures **structured context** for each entry:

```
┌──────────────────────────────────────────────────────────────┐
│  situation        │  "API calls timeout after deploy"        │
│  solution         │  "Increased connection pool size"        │
│  what_failed      │  "Retry logic didn't help"               │
│  trigger_keywords │  ["timeout", "deploy", "connection pool"]│
│  error_messages   │  "ETIMEDOUT after 30s"                   │
│  files_modified   │  ["config/database.yml"]                 │
└──────────────────────────────────────────────────────────────┘
```

When you search, Rekall uses this context to disambiguate:

- **"timeout after deploy"** → Finds the connection pool bug (matches situation)
- **"ETIMEDOUT"** → Finds entries with that exact error message
- **"retry didn't work"** → Finds entries where retry was tried and failed

The `--context-interactive` flag guides you through capturing this:

```bash
rekall add bug "Timeout in prod" --context-interactive
# Rekall asks: What was happening? What fixed it? What didn't work?
# Your answers become searchable disambiguation context
```

### Compressed storage

Context can be verbose. Rekall compresses structured context with zlib and maintains a separate keywords index for fast searching:

```
┌───────────────────────────────────────────────────────────────┐
│                    ENTRY STORAGE                              │
├───────────────────────────────────────────────────────────────┤
│  context_blob     │  Compressed JSON (zlib)    │  ~70% smaller│
│  context_keywords │  Indexed table for search  │  O(1) lookup │
│  emb_summary      │  768-dim vector (summary)  │  Semantic    │
│  emb_context      │  768-dim vector (context)  │  Semantic    │
└───────────────────────────────────────────────────────────────┘
```

The result: **exhaustive** search (nothing is missed) with **speed** (sub-second responses on thousands of entries).

</details>

<br>

<details>
<summary><h2>Built on science</h2></summary>

> **TL;DR:** Knowledge graphs (+20% accuracy), spaced repetition (+6-9% retention), contextual retrieval (-67% failures), all backed by peer-reviewed research.

Rekall isn't a collection of hunches — it's built on peer-reviewed cognitive science and information retrieval research. Here's what we learned and how we applied it:

### Knowledge graphs: +20% retrieval accuracy

**Research**: Studies on knowledge graphs in RAG systems show that connected information is easier to retrieve than isolated facts.

**Application**: Rekall lets you link entries with typed relationships (`related`, `supersedes`, `derived_from`, `contradicts`). When you search, linked entries boost each other's scores. When you fix a new timeout bug, Rekall surfaces the three other timeout issues you've solved — and the pattern you extracted from them.

### Episodic vs semantic memory: How your brain organizes

**Research**: Tulving (1972) established that human memory has two distinct systems — episodic (specific events: "I fixed this bug on Tuesday") and semantic (general knowledge: "Always add retry for external APIs").

**Application**: Rekall distinguishes `episodic` entries (what happened) from `semantic` entries (what you learned). The `generalize` command helps you extract patterns from episodes. This mirrors how expertise develops: you accumulate experiences, then distill them into principles.

### Spaced repetition: +6-9% retention

**Research**: The spacing effect (Ebbinghaus, 1885) and SM-2 algorithm show that reviewing information at increasing intervals dramatically improves retention.

**Application**: Rekall tracks when you access each entry and calculates a consolidation score. The `review` command surfaces knowledge that's about to fade. The `stale` command finds entries you haven't touched in months — before they become forgotten.

### Contextual retrieval: -67% search failures

**Research**: Anthropic's Contextual Retrieval paper showed that traditional RAG systems fail because they strip context when encoding. Adding 50-100 tokens of context reduces retrieval failures by 67%.

**Application**: Rekall's structured context (situation, solution, keywords) preserves the "why" alongside the "what." The double embedding strategy ensures both focused queries and exploratory searches find relevant entries.

### Progressive disclosure: -98% token usage

**Research**: Anthropic's engineering blog documented that returning compact summaries instead of full content reduces token usage by 98% while maintaining task success.

**Application**: Rekall's MCP server returns compact results (id, title, score, snippet) with a hint to fetch full details. Your AI assistant gets what it needs without blowing its context window.

### Consolidation score: Modeling forgetting

**Research**: The forgetting curve shows that memories decay exponentially without reinforcement. Access frequency and recency both matter.

**Application**: Rekall calculates a consolidation score for each entry:

```python
score = 0.6 × frequency_factor + 0.4 × freshness_factor
```

Entries you access often and recently have high consolidation (stable knowledge). Entries you haven't touched in months have low consolidation (at risk of being forgotten).

**We read the papers so you don't have to. Then we built a tool that applies them.**

</details>

<br>

## Learn more

| Resource | Description |
|----------|-------------|
| [Getting Started](docs/getting-started.md) | Installation and first steps |
| [CLI Reference](docs/usage.md) | Complete command documentation |
| [MCP Integration](docs/mcp-integration.md) | Connect to AI assistants |
| [Architecture](docs/architecture.md) | Technical diagrams and internals |
| [Contributing](CONTRIBUTING.md) | How to contribute |
| [Changelog](CHANGELOG.md) | Release history |

---

## Requirements

- Python 3.9+
- That's it. No cloud services. No API keys. No accounts.

---

## License

MIT — Do what you want with it.

---

<p align="center">
<strong>Stop losing knowledge. Start remembering.</strong>
<br><br>

```bash
uv tool install git+https://github.com/guthubrx/rekall.git
rekall
```
</p>
