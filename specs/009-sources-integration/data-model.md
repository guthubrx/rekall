# Data Model: Intégration Sources & Souvenirs

**Date** : 2025-12-11
**Version schéma** : v8 (migration depuis v7)

---

## Vue d'Ensemble

```
┌─────────────┐       ┌────────────────┐       ┌─────────────┐
│   entries   │ 1───N │ entry_sources  │ N───1 │   sources   │
│  (existant) │       │   (nouveau)    │       │  (nouveau)  │
└─────────────┘       └────────────────┘       └─────────────┘
                              │
                              │ source_id peut être NULL
                              │ (URL non curée)
                              ▼
```

---

## Entités

### Source (nouvelle)

Représente une source documentaire curée avec métadonnées de scoring.

| Champ | Type | Contrainte | Description |
|-------|------|------------|-------------|
| `id` | TEXT | PK | ULID unique |
| `domain` | TEXT | NOT NULL | Domaine normalisé (ex: "pinecone.io") |
| `url_pattern` | TEXT | | Pattern URL optionnel (ex: "https://pinecone.io/learn/*") |
| `usage_count` | INTEGER | DEFAULT 0 | Nombre de citations dans des souvenirs |
| `last_used` | TEXT | | ISO datetime dernière citation |
| `personal_score` | REAL | DEFAULT 50.0 | Score calculé 0-100 |
| `reliability` | TEXT | CHECK IN ('A','B','C') | Fiabilité Admiralty simplifié |
| `decay_rate` | TEXT | CHECK IN ('fast','medium','slow') | Vitesse de déclin du score |
| `last_verified` | TEXT | | ISO datetime dernière vérification link rot |
| `status` | TEXT | CHECK IN ('active','inaccessible','archived') | État de la source |
| `created_at` | TEXT | NOT NULL | ISO datetime création |

**Index** :
- `idx_sources_domain` sur `domain`
- `idx_sources_score` sur `personal_score DESC`

**Valeurs par défaut** :
- `reliability`: 'B' (neutre)
- `decay_rate`: 'medium' (demi-vie 6 mois)
- `personal_score`: 50.0 (médiane)
- `status`: 'active'

---

### EntrySource (nouvelle)

Représente le lien entre un souvenir et une source.

| Champ | Type | Contrainte | Description |
|-------|------|------------|-------------|
| `id` | TEXT | PK | ULID unique |
| `entry_id` | TEXT | FK → entries(id) CASCADE | Souvenir lié |
| `source_id` | TEXT | FK → sources(id) SET NULL | Source curée (optionnel) |
| `source_type` | TEXT | CHECK IN ('theme','url','file') | Type de référence |
| `source_ref` | TEXT | NOT NULL | Référence (thème, URL, chemin) |
| `note` | TEXT | | Note contextuelle optionnelle |
| `created_at` | TEXT | NOT NULL | ISO datetime création |

**Index** :
- `idx_entry_sources_entry` sur `entry_id`
- `idx_entry_sources_source` sur `source_id`

**Comportement FK** :
- `entry_id` : CASCADE (suppression souvenir → suppression liens)
- `source_id` : SET NULL (suppression source → lien conservé sans source)

---

### Entry (existant - rappel)

Souvenir Rekall existant (pas de modification).

| Champ clé | Type | Description |
|-----------|------|-------------|
| `id` | TEXT | ULID du souvenir |
| `title` | TEXT | Titre |
| `content` | TEXT | Contenu |
| `type` | TEXT | bug, pattern, decision, pitfall, config, reference |
| `project` | TEXT | Projet associé |

---

## Relations

### Entry ↔ EntrySource (1:N)

Un souvenir peut avoir plusieurs sources liées.

```sql
-- Obtenir les sources d'un souvenir
SELECT es.*, s.domain, s.personal_score
FROM entry_sources es
LEFT JOIN sources s ON es.source_id = s.id
WHERE es.entry_id = ?;
```

### Source ↔ EntrySource (1:N) - Backlinks

Une source curée peut être citée par plusieurs souvenirs.

```sql
-- Obtenir les backlinks d'une source
SELECT e.id, e.title, es.note, es.created_at
FROM entry_sources es
JOIN entries e ON es.entry_id = e.id
WHERE es.source_id = ?
ORDER BY es.created_at DESC;
```

### EntrySource sans Source

Une URL peut être liée à un souvenir sans être curée :

```sql
-- Lien vers URL non curée
INSERT INTO entry_sources (id, entry_id, source_id, source_type, source_ref, created_at)
VALUES (?, ?, NULL, 'url', 'https://example.com/article', ?);
```

---

## États et Transitions

### Source.status

```
           ┌──────────────────────────┐
           │                          │
           ▼                          │
    ┌─────────────┐   HTTP OK    ┌────┴────────┐
    │   active    │◄────────────│ inaccessible│
    └──────┬──────┘              └──────┬──────┘
           │                            │
           │ HTTP 4xx/5xx               │ Manuel
           │                            │
           ▼                            ▼
    ┌─────────────┐              ┌─────────────┐
    │inaccessible │              │  archived   │
    └─────────────┘              └─────────────┘
```

- `active` → `inaccessible` : Vérification link rot échoue
- `inaccessible` → `active` : Vérification link rot réussit
- `*` → `archived` : Action manuelle utilisateur

### Source.reliability

```
    ┌───────────────────────────────────┐
    │                                   │
    │   A (usage_count ≥ 5, fiable)     │
    │           ▲                       │
    │           │ +usage                │
    │           │                       │
    │   B (usage_count 1-4, neutre)     │◄── Défaut
    │           ▲                       │
    │           │ +usage                │
    │           │                       │
    │   C (usage_count 0, non prouvé)   │
    │                                   │
    └───────────────────────────────────┘
```

Promotion automatique basée sur `usage_count` :
- C → B : après 1ère citation
- B → A : après 5ème citation

---

## Validation

### Source

```python
def validate_source(source: Source) -> list[str]:
    errors = []

    if not source.domain:
        errors.append("domain is required")

    if source.reliability not in ('A', 'B', 'C'):
        errors.append(f"reliability must be A/B/C, got {source.reliability}")

    if source.decay_rate not in ('fast', 'medium', 'slow'):
        errors.append(f"decay_rate must be fast/medium/slow, got {source.decay_rate}")

    if not 0 <= source.personal_score <= 100:
        errors.append(f"personal_score must be 0-100, got {source.personal_score}")

    return errors
```

### EntrySource

```python
def validate_entry_source(es: EntrySource) -> list[str]:
    errors = []

    if not es.entry_id:
        errors.append("entry_id is required")

    if es.source_type not in ('theme', 'url', 'file'):
        errors.append(f"source_type must be theme/url/file, got {es.source_type}")

    if not es.source_ref:
        errors.append("source_ref is required")

    # Validation spécifique par type
    if es.source_type == 'theme':
        if not es.source_ref.endswith('.md'):
            errors.append("theme source_ref should be a .md filename")
    elif es.source_type == 'url':
        if not es.source_ref.startswith(('http://', 'https://')):
            errors.append("url source_ref must start with http:// or https://")

    return errors
```

---

## Requêtes Clés

### Top sources par score

```sql
SELECT id, domain, personal_score, usage_count, last_used
FROM sources
WHERE status = 'active'
ORDER BY personal_score DESC
LIMIT 20;
```

### Sources dormantes (>6 mois)

```sql
SELECT id, domain, personal_score, last_used
FROM sources
WHERE status = 'active'
AND (last_used IS NULL OR last_used < datetime('now', '-6 months'))
ORDER BY last_used ASC;
```

### Sources émergentes (3+ citations en 30 jours)

```sql
SELECT s.id, s.domain, COUNT(*) as recent_citations
FROM sources s
JOIN entry_sources es ON s.id = es.source_id
WHERE es.created_at > datetime('now', '-30 days')
GROUP BY s.id
HAVING COUNT(*) >= 3
ORDER BY recent_citations DESC;
```

### Backlinks count par source

```sql
SELECT s.id, s.domain, COUNT(es.id) as backlinks_count
FROM sources s
LEFT JOIN entry_sources es ON s.id = es.source_id
GROUP BY s.id
ORDER BY backlinks_count DESC;
```

---

## Migration SQL (v7 → v8)

```sql
-- Version 8 migration
PRAGMA user_version = 8;

-- Table sources
CREATE TABLE IF NOT EXISTS sources (
    id TEXT PRIMARY KEY,
    domain TEXT NOT NULL,
    url_pattern TEXT,
    usage_count INTEGER DEFAULT 0,
    last_used TEXT,
    personal_score REAL DEFAULT 50.0,
    reliability TEXT DEFAULT 'B',
    decay_rate TEXT DEFAULT 'medium',
    last_verified TEXT,
    status TEXT DEFAULT 'active',
    created_at TEXT NOT NULL,
    CHECK (reliability IN ('A', 'B', 'C')),
    CHECK (decay_rate IN ('fast', 'medium', 'slow')),
    CHECK (status IN ('active', 'inaccessible', 'archived'))
);

-- Table entry_sources
CREATE TABLE IF NOT EXISTS entry_sources (
    id TEXT PRIMARY KEY,
    entry_id TEXT NOT NULL,
    source_id TEXT,
    source_type TEXT NOT NULL,
    source_ref TEXT NOT NULL,
    note TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (entry_id) REFERENCES entries(id) ON DELETE CASCADE,
    FOREIGN KEY (source_id) REFERENCES sources(id) ON DELETE SET NULL,
    CHECK (source_type IN ('theme', 'url', 'file'))
);

-- Index
CREATE INDEX IF NOT EXISTS idx_sources_domain ON sources(domain);
CREATE INDEX IF NOT EXISTS idx_sources_score ON sources(personal_score DESC);
CREATE INDEX IF NOT EXISTS idx_entry_sources_entry ON entry_sources(entry_id);
CREATE INDEX IF NOT EXISTS idx_entry_sources_source ON entry_sources(source_id);
```
