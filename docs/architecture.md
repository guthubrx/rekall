# Rekall Architecture

This document provides detailed technical diagrams of Rekall's architecture.

## System Overview

```mermaid
flowchart TB
    subgraph User["User Interfaces"]
        CLI["CLI Commands<br/>rekall add/search/show"]
        TUI["Terminal UI<br/>rekall (interactive)"]
        MCP["MCP Server<br/>rekall mcp"]
    end

    subgraph Core["Core Engine"]
        DB[(SQLite<br/>+ FTS5)]
        EMB["EmbeddingGemma<br/>(optional)"]
        SM2["SM-2<br/>Scheduler"]
        CTX["Context<br/>Processor"]
    end

    subgraph Storage["Data Storage"]
        ENTRIES["Entries Table"]
        FTS["FTS5 Index"]
        VECTORS["Embedding Vectors"]
        LINKS["Entry Links"]
    end

    subgraph External["External Integrations"]
        CLAUDE["Claude Code<br/>Claude Desktop"]
        CURSOR["Cursor"]
        WIND["Windsurf"]
        OTHER["Other MCP Clients"]
    end

    CLI --> Core
    TUI --> Core
    MCP --> Core

    Core --> Storage
    DB --> ENTRIES
    DB --> FTS
    EMB --> VECTORS

    MCP <--> CLAUDE
    MCP <--> CURSOR
    MCP <--> WIND
    MCP <--> OTHER
```

## Hybrid Search Pipeline

```mermaid
flowchart LR
    Q["Search Query<br/>'browser blocking API'"]

    subgraph Search["Parallel Search"]
        FTS["FTS5<br/>Full-text<br/>**50%**"]
        SEM["Semantic<br/>Embeddings<br/>**30%**"]
        KW["Keywords<br/>Triggers<br/>**20%**"]
    end

    FUSION["Score<br/>Fusion"]
    RANK["Ranked<br/>Results"]

    Q --> FTS
    Q --> SEM
    Q --> KW

    FTS --> FUSION
    SEM --> FUSION
    KW --> FUSION

    FUSION --> RANK
```

### Search Strategy Details

| Strategy | Weight | How it works |
|----------|--------|--------------|
| **FTS5** | 50% | SQLite full-text search with BM25 ranking. Finds exact and partial word matches. |
| **Semantic** | 30% | EmbeddingGemma creates 768-dim vectors. Cosine similarity finds conceptually related content. |
| **Keywords** | 20% | Structured context keywords provide explicit triggers (`cors`, `safari`, `timeout`). |

## Entry Data Flow

```mermaid
flowchart TD
    subgraph Input["Entry Creation"]
        ADD["rekall add bug 'CORS Safari'"]
        CTX["--context-interactive"]
    end

    subgraph Processing["Processing Pipeline"]
        PARSE["Parse Title<br/>& Content"]
        KWEXT["Keyword<br/>Extraction"]
        EMBGEN["Generate<br/>Embeddings"]
        COMPRESS["Compress<br/>Context (zlib)"]
    end

    subgraph Storage["Storage"]
        MAIN["entries table<br/>(id, title, content, type)"]
        FTSIDX["entries_fts<br/>(FTS5 index)"]
        CTXBLOB["context_blob<br/>(compressed JSON)"]
        CTXKW["context_keywords<br/>(indexed table)"]
        EMBSUM["emb_summary<br/>(768-dim vector)"]
        EMBCTX["emb_context<br/>(768-dim vector)"]
    end

    ADD --> PARSE
    CTX --> PARSE
    PARSE --> KWEXT
    PARSE --> EMBGEN
    PARSE --> COMPRESS

    KWEXT --> CTXKW
    EMBGEN --> EMBSUM
    EMBGEN --> EMBCTX
    COMPRESS --> CTXBLOB
    PARSE --> MAIN
    MAIN --> FTSIDX
```

## Memory Consolidation Model

```mermaid
flowchart LR
    subgraph Access["Access Tracking"]
        FREQ["Frequency<br/>How often accessed"]
        FRESH["Freshness<br/>How recently accessed"]
    end

    subgraph Score["Consolidation Score"]
        CALC["score = 0.6×freq + 0.4×fresh"]
    end

    subgraph Outcome["Memory State"]
        STABLE["High Score<br/>Stable Knowledge"]
        RISK["Low Score<br/>At Risk of Forgetting"]
    end

    FREQ --> CALC
    FRESH --> CALC
    CALC --> STABLE
    CALC --> RISK
```

## SM-2 Spaced Repetition

```mermaid
flowchart TD
    REVIEW["rekall review"]

    subgraph SM2["SM-2 Algorithm"]
        DUE["Load entries<br/>due for review"]
        SHOW["Present entry<br/>to user"]
        RATE["User rates<br/>recall (0-5)"]
        UPDATE["Update:<br/>- easiness factor<br/>- interval<br/>- next review date"]
    end

    NEXT["Schedule<br/>next review"]

    REVIEW --> DUE
    DUE --> SHOW
    SHOW --> RATE
    RATE --> UPDATE
    UPDATE --> NEXT
    NEXT -.->|"time passes"| DUE
```

## MCP Server Protocol

```mermaid
sequenceDiagram
    participant AI as AI Assistant
    participant MCP as Rekall MCP Server
    participant DB as SQLite Database

    AI->>MCP: search("browser API error")
    MCP->>DB: Hybrid search
    DB-->>MCP: Matching entries
    MCP-->>AI: Compact results (id, title, score, snippet)

    AI->>MCP: get_entry("01HX7...")
    MCP->>DB: Full entry lookup
    DB-->>MCP: Complete entry + context
    MCP-->>AI: Full details

    AI->>MCP: add_entry(type, title, content, context)
    MCP->>DB: Insert + index + embed
    DB-->>MCP: Entry ID
    MCP-->>AI: Confirmation + ID
```

## Knowledge Graph Structure

```mermaid
flowchart TD
    subgraph Episodes["Episodic Memory"]
        E1["bug: CORS Safari<br/>3 months ago"]
        E2["bug: DB timeout<br/>2 weeks ago"]
        E3["bug: API timeout<br/>1 month ago"]
    end

    subgraph Semantic["Semantic Memory"]
        P1["pattern: Retry with backoff"]
        D1["decision: JWT for auth"]
    end

    E1 -->|"related"| E2
    E2 -->|"similar"| E3
    E2 -->|"derived_from"| P1
    E3 -->|"derived_from"| P1
    P1 -->|"supports"| D1
```

## File Structure

```
~/.local/share/rekall/
├── rekall.db              # SQLite database
│   ├── entries            # Main entries table
│   ├── entries_fts        # FTS5 full-text index
│   ├── entry_links        # Entry relationships
│   ├── context_keywords   # Keyword index
│   └── embeddings         # Vector storage (if enabled)
├── config.toml            # User configuration
└── backups/               # Automatic backups
```

## Configuration Options

```toml
# ~/.local/share/rekall/config.toml

[embeddings]
enabled = false              # Enable semantic search
model = "embedding-gemma"    # Model to use

[search]
fts_weight = 0.5            # Full-text search weight
semantic_weight = 0.3       # Semantic search weight
keyword_weight = 0.2        # Keyword trigger weight

[review]
algorithm = "sm2"           # Spaced repetition algorithm
default_easiness = 2.5      # Starting easiness factor
```
