# Data Model: AI Source Enrichment

**Feature**: 021-ai-source-enrichment
**Date**: 2025-12-13

## Schema Changes

### Extension Table `sources` (migration v12)

Ajout de colonnes pour l'enrichissement AI. Pas de nouvelle table.

```sql
-- Migration v12: AI Source Enrichment
ALTER TABLE sources ADD COLUMN ai_tags TEXT;           -- JSON array ["tag1", "tag2"]
ALTER TABLE sources ADD COLUMN ai_summary TEXT;        -- Résumé 2-3 phrases
ALTER TABLE sources ADD COLUMN ai_type TEXT;           -- documentation|blog|research|tool|reference|tutorial
ALTER TABLE sources ADD COLUMN ai_confidence REAL;     -- Score confiance 0.0-1.0
ALTER TABLE sources ADD COLUMN enrichment_status TEXT; -- proposed|validated|rejected|none
ALTER TABLE sources ADD COLUMN enriched_at TEXT;       -- ISO 8601 timestamp
ALTER TABLE sources ADD COLUMN validated_by TEXT;      -- human|auto (qui a validé)
```

### Valeurs par défaut

| Column | Default | Notes |
|--------|---------|-------|
| `ai_tags` | `NULL` | JSON null = pas encore enrichi |
| `ai_summary` | `NULL` | |
| `ai_type` | `NULL` | |
| `ai_confidence` | `NULL` | |
| `enrichment_status` | `'none'` | Statut initial |
| `enriched_at` | `NULL` | |
| `validated_by` | `NULL` | |

### Contraintes

```sql
-- Check constraints (SQLite style)
CHECK (ai_confidence IS NULL OR (ai_confidence >= 0.0 AND ai_confidence <= 1.0))
CHECK (enrichment_status IN ('none', 'proposed', 'validated', 'rejected'))
CHECK (ai_type IS NULL OR ai_type IN ('documentation', 'blog', 'research', 'tool', 'reference', 'tutorial'))
CHECK (validated_by IS NULL OR validated_by IN ('human', 'auto'))
```

### Index recommandé

```sql
-- Index pour requêtes sur sources non enrichies
CREATE INDEX IF NOT EXISTS idx_sources_enrichment_status ON sources(enrichment_status);
```

## Entity Relationships

```
┌─────────────────────────────────────────────────────────────┐
│                         entries                              │
│  id, title, type, content, tags, ...                        │
└──────────────────────┬──────────────────────────────────────┘
                       │ 1:N
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                      entry_sources                           │
│  id, entry_id, source_id, source_type, source_ref, note     │
└──────────────────────┬──────────────────────────────────────┘
                       │ N:1 (optional)
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                         sources                              │
│  id, title, url, domain, ...                                │
│  + ai_tags, ai_summary, ai_type, ai_confidence              │  ← NEW
│  + enrichment_status, enriched_at, validated_by             │  ← NEW
└─────────────────────────────────────────────────────────────┘
```

## Data Flow

### Enrichissement Workflow

```
1. Agent appelle rekall_list_unenriched()
   → Retourne sources avec enrichment_status = 'none'

2. Agent analyse source (lui-même = LLM)
   → Génère: tags, summary, type, confidence

3. Agent appelle rekall_enrich_source(source_id, enrichment)
   → enrichment_status = 'proposed'
   → enriched_at = now()
   → ai_* = valeurs proposées

4. Utilisateur valide/rejette via rekall_validate_enrichment()
   → enrichment_status = 'validated' | 'rejected'
   → validated_by = 'human'
```

### Auto-validation (optionnel)

Si `ai_confidence >= 0.90`, l'enrichissement peut être auto-validé:
- `enrichment_status = 'validated'`
- `validated_by = 'auto'`

## Python Dataclass (optionnel)

```python
from dataclasses import dataclass
from datetime import datetime
from typing import Literal

EnrichmentStatus = Literal['none', 'proposed', 'validated', 'rejected']
SourceType = Literal['documentation', 'blog', 'research', 'tool', 'reference', 'tutorial']
ValidatedBy = Literal['human', 'auto']

@dataclass
class SourceEnrichment:
    """AI enrichment data for a source."""
    ai_tags: list[str] | None = None
    ai_summary: str | None = None
    ai_type: SourceType | None = None
    ai_confidence: float | None = None
    enrichment_status: EnrichmentStatus = 'none'
    enriched_at: datetime | None = None
    validated_by: ValidatedBy | None = None
```

## Migration Strategy

### Backward Compatibility

- Toutes les nouvelles colonnes sont `NULL`able
- Default `enrichment_status = 'none'` pour existant
- Pas de contrainte NOT NULL
- Pas de foreign key nouvelle

### Migration Code (Python)

```python
MIGRATIONS = {
    12: [
        "ALTER TABLE sources ADD COLUMN ai_tags TEXT",
        "ALTER TABLE sources ADD COLUMN ai_summary TEXT",
        "ALTER TABLE sources ADD COLUMN ai_type TEXT",
        "ALTER TABLE sources ADD COLUMN ai_summary TEXT",
        "ALTER TABLE sources ADD COLUMN ai_confidence REAL",
        "ALTER TABLE sources ADD COLUMN enrichment_status TEXT DEFAULT 'none'",
        "ALTER TABLE sources ADD COLUMN enriched_at TEXT",
        "ALTER TABLE sources ADD COLUMN validated_by TEXT",
        "CREATE INDEX IF NOT EXISTS idx_sources_enrichment_status ON sources(enrichment_status)",
    ],
}
```

## Queries Patterns

### Get unenriched sources

```sql
SELECT * FROM sources
WHERE enrichment_status = 'none'
  AND status = 'active'
ORDER BY created_at DESC
LIMIT ?
```

### Get proposed (pending validation)

```sql
SELECT * FROM sources
WHERE enrichment_status = 'proposed'
ORDER BY ai_confidence DESC, enriched_at ASC
```

### Update enrichment

```sql
UPDATE sources SET
  ai_tags = ?,
  ai_summary = ?,
  ai_type = ?,
  ai_confidence = ?,
  enrichment_status = 'proposed',
  enriched_at = ?
WHERE id = ?
```

### Validate enrichment

```sql
UPDATE sources SET
  enrichment_status = ?,
  validated_by = 'human'
WHERE id = ?
```
