# Data Model: DevKMS

**Date**: 2025-12-07
**Phase**: 1 - Design

## Schéma Base de Données

```
~/.devkms/
├── knowledge.db    # SQLite principal (FTS5 + WAL)
├── config.toml     # Configuration utilisateur (optionnel)
└── backups/        # Backups automatiques (optionnel)
```

---

## Tables SQLite

### Table `entries` (Principale)

```sql
CREATE TABLE entries (
    id TEXT PRIMARY KEY,              -- ULID (26 chars)
    title TEXT NOT NULL,              -- Titre court
    content TEXT,                     -- Contenu détaillé (markdown)
    type TEXT NOT NULL,               -- bug|pattern|decision|pitfall|config|reference
    project TEXT,                     -- Nom du projet (optionnel)
    confidence INTEGER DEFAULT 2,     -- 0-5
    status TEXT DEFAULT 'active',     -- active|obsolete
    superseded_by TEXT,               -- ID de l'entrée remplaçante (si obsolete)
    created_at TEXT NOT NULL,         -- ISO 8601
    updated_at TEXT NOT NULL,         -- ISO 8601

    FOREIGN KEY (superseded_by) REFERENCES entries(id),
    CHECK (type IN ('bug', 'pattern', 'decision', 'pitfall', 'config', 'reference')),
    CHECK (confidence BETWEEN 0 AND 5),
    CHECK (status IN ('active', 'obsolete'))
);

CREATE INDEX idx_entries_type ON entries(type);
CREATE INDEX idx_entries_project ON entries(project);
CREATE INDEX idx_entries_status ON entries(status);
CREATE INDEX idx_entries_created ON entries(created_at);
```

### Table `tags` (Many-to-Many)

```sql
CREATE TABLE tags (
    entry_id TEXT NOT NULL,
    tag TEXT NOT NULL,

    PRIMARY KEY (entry_id, tag),
    FOREIGN KEY (entry_id) REFERENCES entries(id) ON DELETE CASCADE
);

CREATE INDEX idx_tags_tag ON tags(tag);
```

### Table Virtuelle FTS5 (Full-Text Search)

```sql
CREATE VIRTUAL TABLE entries_fts USING fts5(
    id UNINDEXED,          -- Pas indexé pour FTS (juste pour jointure)
    title,                  -- Indexé
    content,                -- Indexé
    tags,                   -- Tags concaténés, indexés
    tokenize = 'porter unicode61'
);

-- Triggers pour synchronisation automatique
CREATE TRIGGER entries_ai AFTER INSERT ON entries BEGIN
    INSERT INTO entries_fts(id, title, content, tags)
    SELECT NEW.id, NEW.title, NEW.content,
           (SELECT GROUP_CONCAT(tag, ' ') FROM tags WHERE entry_id = NEW.id);
END;

CREATE TRIGGER entries_ad AFTER DELETE ON entries BEGIN
    DELETE FROM entries_fts WHERE id = OLD.id;
END;

CREATE TRIGGER entries_au AFTER UPDATE ON entries BEGIN
    DELETE FROM entries_fts WHERE id = OLD.id;
    INSERT INTO entries_fts(id, title, content, tags)
    SELECT NEW.id, NEW.title, NEW.content,
           (SELECT GROUP_CONCAT(tag, ' ') FROM tags WHERE entry_id = NEW.id);
END;
```

---

## Entités Python

### Entry (Dataclass)

```python
from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal, Optional

EntryType = Literal['bug', 'pattern', 'decision', 'pitfall', 'config', 'reference']
EntryStatus = Literal['active', 'obsolete']

@dataclass
class Entry:
    id: str                                    # ULID
    title: str
    type: EntryType
    content: str = ""
    project: Optional[str] = None
    tags: list[str] = field(default_factory=list)
    confidence: int = 2                        # 0-5
    status: EntryStatus = 'active'
    superseded_by: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        if not 0 <= self.confidence <= 5:
            raise ValueError("confidence must be 0-5")
        if self.type not in ('bug', 'pattern', 'decision', 'pitfall', 'config', 'reference'):
            raise ValueError(f"invalid type: {self.type}")
```

### SearchResult (Pour affichage)

```python
@dataclass
class SearchResult:
    entry: Entry
    rank: float          # Score BM25 (plus bas = plus pertinent)
    snippet: str = ""    # Extrait avec termes surlignés
```

### Config (Settings)

```python
@dataclass
class Config:
    db_path: Path = Path.home() / ".devkms" / "knowledge.db"
    editor: Optional[str] = None           # $EDITOR ou vim/notepad
    default_project: Optional[str] = None
    embeddings_provider: Optional[str] = None  # ollama|openai (P3)
    embeddings_model: Optional[str] = None     # nomic-embed-text (P3)
```

---

## Requêtes Clés

### Recherche Full-Text

```sql
-- Recherche simple
SELECT e.*, rank
FROM entries_fts
JOIN entries e ON entries_fts.id = e.id
WHERE entries_fts MATCH ?
  AND e.status = 'active'
ORDER BY rank
LIMIT 20;

-- Avec filtre type
SELECT e.*, rank
FROM entries_fts
JOIN entries e ON entries_fts.id = e.id
WHERE entries_fts MATCH ?
  AND e.type = ?
  AND e.status = 'active'
ORDER BY rank
LIMIT 20;
```

### Entrées par Projet

```sql
SELECT e.*, GROUP_CONCAT(t.tag, ', ') as tags
FROM entries e
LEFT JOIN tags t ON e.id = t.entry_id
WHERE e.project = ?
  AND e.status = 'active'
GROUP BY e.id
ORDER BY e.created_at DESC;
```

### Historique Obsolescence

```sql
-- Trouver la chaîne de remplacement
WITH RECURSIVE chain AS (
    SELECT id, title, superseded_by, 0 as depth
    FROM entries
    WHERE id = ?

    UNION ALL

    SELECT e.id, e.title, e.superseded_by, c.depth + 1
    FROM entries e
    JOIN chain c ON e.id = c.superseded_by
    WHERE c.depth < 10  -- Limite profondeur
)
SELECT * FROM chain;
```

---

## Validation Rules

| Champ | Règle | Message d'erreur |
|-------|-------|------------------|
| id | ULID 26 chars | "Invalid ULID format" |
| title | Non vide, max 200 chars | "Title required (max 200 chars)" |
| type | Enum validé | "Invalid type. Valid: bug, pattern, decision, pitfall, config, reference" |
| confidence | 0-5 | "Confidence must be 0-5" |
| tags | Alphanum + hyphen, max 50 chars chacun | "Invalid tag format" |
| project | Alphanum + hyphen, max 100 chars | "Invalid project name" |

---

## Migrations

### v1 → v2 (Future)

```sql
-- Exemple : ajout colonne
ALTER TABLE entries ADD COLUMN embedding BLOB;

-- Track version
CREATE TABLE IF NOT EXISTS schema_version (version INTEGER);
INSERT INTO schema_version VALUES (2);
```

**Stratégie** : Migration automatique au démarrage via `db.py`
