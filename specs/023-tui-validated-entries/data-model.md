# Data Model - 023 TUI Enriched Entries Tab

**Date**: 2025-12-13
**Branche**: 023-tui-validated-entries

## Vue d'Ensemble

Cette feature n'introduit pas de nouveaux modeles de donnees. Elle reutilise le modele `Source` existant qui contient deja les colonnes d'enrichissement IA.

## Modele Existant Reutilise

### Table `sources`

```sql
CREATE TABLE sources (
    id TEXT PRIMARY KEY,           -- ULID
    domain TEXT NOT NULL,
    url_pattern TEXT,

    -- Metadonnees enrichissement IA (Feature 021)
    enrichment_status TEXT DEFAULT 'none',  -- 'none' | 'proposed' | 'validated'
    ai_type TEXT,                   -- 'documentation' | 'blog' | 'research' | etc.
    ai_tags TEXT,                   -- JSON array de tags
    ai_summary TEXT,                -- Resume genere par IA
    ai_confidence REAL,             -- Score 0.0 - 1.0
    enrichment_validated_at TEXT,   -- ISO timestamp validation

    -- Autres colonnes existantes
    personal_score REAL DEFAULT 50.0,
    status TEXT DEFAULT 'seed',
    role TEXT DEFAULT 'unclassified',
    reliability TEXT DEFAULT 'B',
    usage_count INTEGER DEFAULT 0,
    created_at TEXT,
    updated_at TEXT
);
```

### Entite Conceptuelle : EnrichedSource

Pas de nouvelle classe - on filtre `Source` avec `enrichment_status != 'none'`.

```python
# Pseudo-code representation
@dataclass
class EnrichedSource:
    """Vue logique d'une Source avec enrichissement IA."""
    # Herite de Source
    id: str
    domain: str

    # Champs enrichissement (obligatoires dans cette vue)
    enrichment_status: Literal["proposed", "validated"]
    ai_type: str
    ai_tags: list[str]  # Parse depuis JSON
    ai_summary: str
    ai_confidence: float
    enrichment_validated_at: datetime | None
```

## Relations

```
┌─────────────────┐
│    sources      │
├─────────────────┤
│ id (PK)         │
│ domain          │
│ enrichment_*    │ ◄── Filtré pour onglet "Enrichies"
└────────┬────────┘
         │
         │ 1:N (entry_sources)
         ▼
┌─────────────────┐
│    entries      │
├─────────────────┤
│ id (PK)         │
│ title           │
└─────────────────┘
```

## Etats et Transitions

### Diagramme d'Etat enrichment_status

```
                    ┌──────────────┐
                    │    none      │ (etat initial)
                    └──────┬───────┘
                           │
                    rekall_enrich_source
                    (confidence < 0.90)
                           │
                           ▼
                    ┌──────────────┐
              ┌─────│   proposed   │─────┐
              │     └──────────────┘     │
              │                          │
        User: Valider              User: Rejeter
        (TUI action)               (TUI action)
              │                          │
              ▼                          ▼
       ┌──────────────┐          ┌──────────────┐
       │  validated   │          │    none      │
       └──────────────┘          └──────────────┘
       (reste visible)           (disparait de
                                  l'onglet)
```

### Auto-validation

Si `ai_confidence >= 0.90` lors de l'enrichissement :
```
none ──── rekall_enrich_source ────► validated
          (auto_validate=true)       (directement)
```

## Requetes SQL Cles

### Lister les sources enrichies (pour l'onglet)

```sql
SELECT * FROM sources
WHERE enrichment_status IN ('validated', 'proposed')
ORDER BY
    CASE enrichment_status
        WHEN 'proposed' THEN 0  -- En premier
        WHEN 'validated' THEN 1
    END,
    ai_confidence DESC,
    domain ASC
LIMIT 500;
```

### Compter par statut (pour le label de l'onglet)

```sql
SELECT
    COUNT(*) as total,
    SUM(CASE WHEN enrichment_status = 'proposed' THEN 1 ELSE 0 END) as proposed,
    SUM(CASE WHEN enrichment_status = 'validated' THEN 1 ELSE 0 END) as validated
FROM sources
WHERE enrichment_status != 'none';
```

### Valider une entree proposed

```sql
UPDATE sources
SET
    enrichment_status = 'validated',
    enrichment_validated_at = datetime('now'),
    updated_at = datetime('now')
WHERE id = ? AND enrichment_status = 'proposed';
```

### Rejeter une entree proposed (FR-009)

```sql
UPDATE sources
SET
    enrichment_status = 'none',
    -- On garde les metadonnees pour permettre re-enrichissement
    updated_at = datetime('now')
WHERE id = ? AND enrichment_status = 'proposed';
```

## Validation des Donnees

| Champ | Contrainte | Validation |
|-------|------------|------------|
| enrichment_status | ENUM | 'none', 'proposed', 'validated' |
| ai_type | ENUM | 'documentation', 'blog', 'research', 'tool', 'reference', 'tutorial' |
| ai_confidence | FLOAT | 0.0 <= x <= 1.0 |
| ai_tags | JSON | Array de strings |
| ai_summary | TEXT | Max 500 caracteres |

## Index Existants

```sql
-- Index utile pour la requete de l'onglet Enrichies
CREATE INDEX IF NOT EXISTS idx_sources_enrichment
ON sources(enrichment_status)
WHERE enrichment_status != 'none';
```

## Changements de Schema

**Aucun changement de schema necessaire.**

La Feature 021 (AI Source Enrichment) a deja ajoute toutes les colonnes requises :
- `enrichment_status`
- `ai_type`
- `ai_tags`
- `ai_summary`
- `ai_confidence`
- `enrichment_validated_at`
