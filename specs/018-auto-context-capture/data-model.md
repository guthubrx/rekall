# Data Model - Feature 018: Auto-Capture Contexte Enrichi

**Date**: 2025-12-12
**Branche**: `018-auto-context-capture`

## Entités Nouvelles

### TranscriptFormat (Enum)

```python
class TranscriptFormat(str, Enum):
    """Formats de transcript supportés."""
    CLAUDE_JSONL = "claude-jsonl"      # Claude Code CLI
    CLINE_JSON = "cline-json"          # Cline VS Code extension
    CONTINUE_JSON = "continue-json"    # Continue.dev
    RAW_JSON = "raw-json"              # Format générique
    # v2
    SQLITE = "sqlite"                  # Cursor, Amazon Q
    LMDB = "lmdb"                      # Zed IDE
```

### TranscriptMessage (Dataclass)

```python
@dataclass
class TranscriptMessage:
    """Message normalisé depuis n'importe quel format transcript."""
    role: Literal["human", "assistant"]
    content: str
    timestamp: Optional[datetime] = None
    index: int = 0  # Position dans le transcript original

    def to_dict(self) -> dict:
        return {
            "role": self.role,
            "content": self.content[:500] + "..." if len(self.content) > 500 else self.content,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "index": self.index
        }
```

### CandidateExchanges (Dataclass)

```python
@dataclass
class CandidateExchanges:
    """Réponse Mode 2 - Échanges candidats pour filtrage par l'agent."""
    session_id: str
    total_exchanges: int
    candidates: list[TranscriptMessage]  # Max 20
    transcript_path: str
    transcript_format: TranscriptFormat

    def to_mcp_response(self) -> dict:
        return {
            "status": "candidates_ready",
            "session_id": self.session_id,
            "total_exchanges": self.total_exchanges,
            "candidates": [c.to_dict() for c in self.candidates],
            "instruction": "Reply with conversation_excerpt_indices to select pertinent exchanges"
        }
```

### TemporalMarkers (Dataclass)

```python
@dataclass
class TemporalMarkers:
    """Marqueurs temporels auto-générés ou manuels."""
    time_of_day: Literal["morning", "afternoon", "evening", "night"]
    day_of_week: Literal["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    created_at: datetime

    @classmethod
    def from_datetime(cls, dt: Optional[datetime] = None) -> "TemporalMarkers":
        dt = dt or datetime.now()
        hour = dt.hour

        if 5 <= hour < 12:
            time_of_day = "morning"
        elif 12 <= hour < 17:
            time_of_day = "afternoon"
        elif 17 <= hour < 21:
            time_of_day = "evening"
        else:
            time_of_day = "night"

        day_of_week = dt.strftime("%A").lower()

        return cls(
            time_of_day=time_of_day,
            day_of_week=day_of_week,
            created_at=dt
        )
```

### HookConfig (Dataclass)

```python
@dataclass
class HookConfig:
    """Configuration du hook de rappel proactif."""
    cli: Literal["claude", "cline", "continue", "generic"]
    hook_type: Literal["stop", "post_tool_use"]
    patterns: list[str]  # Regex patterns de résolution
    cooldown_seconds: int = 300  # 5 min entre rappels
    enabled: bool = True

    # Chemins d'installation par CLI
    INSTALL_PATHS = {
        "claude": "~/.claude/hooks/",
        "cline": "~/.config/Code/User/globalStorage/saoudrizwan.claude-dev/hooks/",
        "continue": ".continue/hooks/",
        "generic": "~/.config/rekall/hooks/"
    }
```

---

## Modifications Entités Existantes

### StructuredContext (Extension)

```python
# Ajouts au StructuredContext existant (models.py)

@dataclass
class StructuredContext:
    # Champs existants (Feature 006)
    situation: str
    solution: str
    trigger_keywords: list[str]
    what_failed: Optional[str] = None
    conversation_excerpt: Optional[str] = None  # Mode 1: fourni directement
    files_modified: Optional[list[str]] = None
    error_messages: Optional[list[str]] = None

    # NOUVEAUX champs Feature 018
    time_of_day: Optional[str] = None          # morning|afternoon|evening|night
    day_of_week: Optional[str] = None          # monday..sunday
    extraction_method: Optional[str] = None    # "manual"|"auto_mode1"|"auto_mode2"|"auto_git"
    transcript_format: Optional[str] = None    # Format utilisé si Mode 2
```

---

## Relations et Flux de Données

```
┌─────────────────────────────────────────────────────────────────┐
│                        rekall_add MCP                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────┐     ┌──────────────────────────────────┐  │
│  │ Mode 1 Direct   │     │ Mode 2 Assisté                   │  │
│  │                 │     │                                  │  │
│  │ conversation_   │     │ auto_capture_conversation: true  │  │
│  │ excerpt fourni  │     │ _transcript_path                 │  │
│  │ directement     │     │ _transcript_format               │  │
│  └────────┬────────┘     └─────────────┬────────────────────┘  │
│           │                            │                       │
│           │                            ▼                       │
│           │              ┌─────────────────────────┐           │
│           │              │ TranscriptParser        │           │
│           │              │ (Strategy Pattern)      │           │
│           │              │ - ClaudeParser          │           │
│           │              │ - ClineParser           │           │
│           │              │ - ContinueParser        │           │
│           │              │ - GenericParser         │           │
│           │              └────────────┬────────────┘           │
│           │                           │                        │
│           │                           ▼                        │
│           │              ┌─────────────────────────┐           │
│           │              │ CandidateExchanges      │           │
│           │              │ (20 derniers échanges)  │           │
│           │              └────────────┬────────────┘           │
│           │                           │                        │
│           │                           ▼                        │
│           │              ┌─────────────────────────┐           │
│           │              │ Agent filtre            │           │
│           │              │ (conversation_excerpt_  │           │
│           │              │  indices: [3,7,12,15])  │           │
│           │              └────────────┬────────────┘           │
│           │                           │                        │
│           ▼                           ▼                        │
│  ┌────────────────────────────────────────────────────────┐    │
│  │                StructuredContext                       │    │
│  │  + conversation_excerpt (string)                       │    │
│  │  + files_modified (auto_detect_files)                  │    │
│  │  + time_of_day, day_of_week (auto ou manuel)           │    │
│  │  + extraction_method (traçabilité)                     │    │
│  └────────────────────────────────────────────────────────┘    │
│                              │                                 │
│                              ▼                                 │
│  ┌────────────────────────────────────────────────────────┐    │
│  │                    db.py                               │    │
│  │  store_structured_context()                            │    │
│  │  → zlib compress → context_blob                        │    │
│  │  → extract keywords → context_keywords table           │    │
│  └────────────────────────────────────────────────────────┘    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Validation et Contraintes

### TranscriptMessage
- `role` : Obligatoire, enum strict
- `content` : Obligatoire, non vide
- `index` : ≥ 0

### CandidateExchanges
- `candidates` : Max 20 éléments
- `session_id` : ULID format

### TemporalMarkers
- `time_of_day` : Enum 4 valeurs
- `day_of_week` : Enum 7 valeurs (anglais lowercase)

### HookConfig
- `cooldown_seconds` : ≥ 60 (évite spam)
- `patterns` : Au moins 1 pattern valide

---

## Migrations DB Requises

**Aucune migration DB requise** - Les nouveaux champs sont stockés dans le JSON compressé `context_blob` (schema v7+).

Les champs `time_of_day`, `day_of_week`, `extraction_method`, `transcript_format` sont ajoutés au JSON sans modification de schema.
