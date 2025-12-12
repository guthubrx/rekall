# Data Model : Système de Mémoire Cognitive

**Date** : 2025-12-09
**Feature** : 004-cognitive-memory

---

## Vue d'ensemble

```
┌─────────────────────────────────────────────────────────────┐
│                         ENTRIES                              │
│  (enrichi avec memory_type, tracking, review)               │
└─────────────────────────────────────────────────────────────┘
           │                              │
           │ 1                            │ 1
           │                              │
           ▼ N                            ▼ N
┌─────────────────────┐          ┌─────────────────────┐
│        TAGS         │          │        LINKS        │
│  (existant)         │          │  (nouveau)          │
└─────────────────────┘          └─────────────────────┘
```

---

## Entités

### 1. Entry (enrichi)

**Table** : `entries`

| Colonne | Type | Contraintes | Description |
|---------|------|-------------|-------------|
| `id` | TEXT | PRIMARY KEY | ULID (existant) |
| `title` | TEXT | NOT NULL | Titre (existant) |
| `content` | TEXT | | Contenu markdown (existant) |
| `type` | TEXT | CHECK IN (...) | bug/pattern/decision/pitfall/config/reference (existant) |
| `project` | TEXT | | Projet associé (existant) |
| `confidence` | INTEGER | 0-5 | Niveau de confiance (existant) |
| `status` | TEXT | active/obsolete | Statut (existant) |
| `superseded_by` | TEXT | FK entries(id) | Entrée remplaçante (existant) |
| `created_at` | TEXT | NOT NULL | ISO datetime (existant) |
| `updated_at` | TEXT | NOT NULL | ISO datetime (existant) |
| **`memory_type`** | TEXT | DEFAULT 'episodic' | **NOUVEAU** : episodic/semantic |
| **`last_accessed`** | TEXT | | **NOUVEAU** : ISO datetime dernier accès |
| **`access_count`** | INTEGER | DEFAULT 0 | **NOUVEAU** : Compteur d'accès |
| **`consolidation_score`** | REAL | DEFAULT 0.0 | **NOUVEAU** : Score 0.0-1.0 |
| **`next_review`** | TEXT | | **NOUVEAU** : ISO date prochaine révision |
| **`review_interval`** | INTEGER | DEFAULT 1 | **NOUVEAU** : Intervalle actuel (jours) |
| **`ease_factor`** | REAL | DEFAULT 2.5 | **NOUVEAU** : Facteur SM-2 |

**Contraintes** :
```sql
CHECK (type IN ('bug', 'pattern', 'decision', 'pitfall', 'config', 'reference'))
CHECK (confidence BETWEEN 0 AND 5)
CHECK (status IN ('active', 'obsolete'))
CHECK (memory_type IN ('episodic', 'semantic'))
```

**Index** :
- `idx_entries_type` (existant)
- `idx_entries_project` (existant)
- `idx_entries_status` (existant)
- `idx_entries_created` (existant)
- **`idx_entries_memory_type`** (nouveau)
- **`idx_entries_next_review`** (nouveau)
- **`idx_entries_last_accessed`** (nouveau)

---

### 2. Tags (existant - non modifié)

**Table** : `tags`

| Colonne | Type | Contraintes |
|---------|------|-------------|
| `entry_id` | TEXT | PK, FK entries(id) ON DELETE CASCADE |
| `tag` | TEXT | PK |

---

### 3. Link (nouveau)

**Table** : `links`

| Colonne | Type | Contraintes | Description |
|---------|------|-------------|-------------|
| `id` | TEXT | PRIMARY KEY | ULID |
| `source_id` | TEXT | NOT NULL, FK | Entrée source |
| `target_id` | TEXT | NOT NULL, FK | Entrée cible |
| `relation_type` | TEXT | CHECK IN (...) | Type de relation |
| `created_at` | TEXT | NOT NULL | ISO datetime création |

**Contraintes** :
```sql
FOREIGN KEY (source_id) REFERENCES entries(id) ON DELETE CASCADE
FOREIGN KEY (target_id) REFERENCES entries(id) ON DELETE CASCADE
CHECK (relation_type IN ('related', 'supersedes', 'derived_from', 'contradicts'))
UNIQUE(source_id, target_id, relation_type)
CHECK (source_id != target_id)  -- Pas d'auto-référence
```

**Index** :
- `idx_links_source` ON links(source_id)
- `idx_links_target` ON links(target_id)
- `idx_links_type` ON links(relation_type)

**Types de relation** :
| Type | Signification | Bidirectionnel |
|------|--------------|----------------|
| `related` | Connexion thématique | Oui |
| `supersedes` | A remplace B (obsolescence) | Non (A→B) |
| `derived_from` | Sémantique dérivé d'épisodiques | Non (S→E) |
| `contradicts` | Information conflictuelle | Oui |

---

## Modèles Python

### models.py (enrichi)

```python
from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Literal, Optional

MemoryType = Literal["episodic", "semantic"]
RelationType = Literal["related", "supersedes", "derived_from", "contradicts"]

@dataclass
class Entry:
    """Knowledge entry (enrichi pour mémoire cognitive)."""
    id: str
    title: str
    type: EntryType
    content: str = ""
    project: Optional[str] = None
    tags: list[str] = field(default_factory=list)
    confidence: int = 2
    status: EntryStatus = "active"
    superseded_by: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    # Nouveaux champs cognitifs
    memory_type: MemoryType = "episodic"
    last_accessed: Optional[datetime] = None
    access_count: int = 0
    consolidation_score: float = 0.0
    next_review: Optional[date] = None
    review_interval: int = 1
    ease_factor: float = 2.5


@dataclass
class Link:
    """Connexion entre deux entrées."""
    id: str
    source_id: str
    target_id: str
    relation_type: RelationType
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class ReviewItem:
    """Entrée due pour révision espacée."""
    entry: Entry
    days_overdue: int
    priority: float  # Plus haut = plus urgent
```

---

## Schéma de migration

### V1 → V2 (cognitive memory)

```sql
-- 1. Nouveaux champs Entry
ALTER TABLE entries ADD COLUMN memory_type TEXT DEFAULT 'episodic'
    CHECK (memory_type IN ('episodic', 'semantic'));
ALTER TABLE entries ADD COLUMN last_accessed TEXT;
ALTER TABLE entries ADD COLUMN access_count INTEGER DEFAULT 0;
ALTER TABLE entries ADD COLUMN consolidation_score REAL DEFAULT 0.0;
ALTER TABLE entries ADD COLUMN next_review TEXT;
ALTER TABLE entries ADD COLUMN review_interval INTEGER DEFAULT 1;
ALTER TABLE entries ADD COLUMN ease_factor REAL DEFAULT 2.5;

-- 2. Migration données existantes
UPDATE entries SET
    last_accessed = created_at,
    access_count = 1
WHERE last_accessed IS NULL;

-- 3. Nouveaux index
CREATE INDEX IF NOT EXISTS idx_entries_memory_type ON entries(memory_type);
CREATE INDEX IF NOT EXISTS idx_entries_next_review ON entries(next_review);
CREATE INDEX IF NOT EXISTS idx_entries_last_accessed ON entries(last_accessed);

-- 4. Nouvelle table Links
CREATE TABLE IF NOT EXISTS links (
    id TEXT PRIMARY KEY,
    source_id TEXT NOT NULL,
    target_id TEXT NOT NULL,
    relation_type TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (source_id) REFERENCES entries(id) ON DELETE CASCADE,
    FOREIGN KEY (target_id) REFERENCES entries(id) ON DELETE CASCADE,
    CHECK (relation_type IN ('related', 'supersedes', 'derived_from', 'contradicts')),
    UNIQUE(source_id, target_id, relation_type),
    CHECK (source_id != target_id)
);

CREATE INDEX IF NOT EXISTS idx_links_source ON links(source_id);
CREATE INDEX IF NOT EXISTS idx_links_target ON links(target_id);
CREATE INDEX IF NOT EXISTS idx_links_type ON links(relation_type);
```

---

## Relations et cardinalités

```
Entry 1 ←──────► N Tags        (existant, CASCADE delete)
Entry 1 ←──────► N Links       (source ou target, CASCADE delete)
Entry 1 ──────► 0..1 Entry     (superseded_by, existant)
```

**Clarifications appliquées** :
- Plusieurs liens de types différents autorisés entre mêmes entrées (clarif #1)
- Suppression entrée → Refuser si liens existent, sauf `--force` (clarif #3)
- Types de relation : enum fermé 4 valeurs (clarif #4)
