# Data Model: Sources Autonomes

**Feature**: 010-sources-autonomes
**Date**: 2025-12-11
**Schema Version**: v8 → v9

---

## Overview

Cette feature étend le schéma v8 (Feature 009) avec :
1. Nouveaux attributs sur la table `sources`
2. Nouvelle table de jonction `source_themes`
3. Nouvelle table `known_domains` pour classification automatique

---

## Entities

### Source (extension)

Table existante `sources` avec nouveaux attributs.

| Colonne | Type | Contrainte | Description |
|---------|------|------------|-------------|
| `id` | TEXT | PK | ULID existant |
| `domain` | TEXT | NOT NULL | Domaine (existant) |
| `url_pattern` | TEXT | | Pattern URL (existant) |
| `usage_count` | INTEGER | DEFAULT 0 | Compteur usages (existant) |
| `last_used` | TEXT | | ISO timestamp (existant) |
| `personal_score` | REAL | DEFAULT 0.0 | Score calculé (existant) |
| `reliability` | TEXT | DEFAULT 'B' | A/B/C (existant) |
| `decay_rate` | TEXT | DEFAULT 'medium' | fast/medium/slow (existant) |
| `last_verified` | TEXT | | Timestamp link rot (existant) |
| `status` | TEXT | DEFAULT 'active' | active/inaccessible (existant) |
| `created_at` | TEXT | NOT NULL | ISO timestamp (existant) |
| **`is_seed`** | INTEGER | DEFAULT 0 | **NOUVEAU** - Boolean: source migrée de speckit |
| **`is_promoted`** | INTEGER | DEFAULT 0 | **NOUVEAU** - Boolean: promue automatiquement |
| **`promoted_at`** | TEXT | | **NOUVEAU** - ISO timestamp de promotion |
| **`role`** | TEXT | DEFAULT 'unclassified' | **NOUVEAU** - hub/authority/unclassified |
| **`seed_origin`** | TEXT | | **NOUVEAU** - Chemin fichier speckit source |
| **`citation_quality_factor`** | REAL | DEFAULT 0.0 | **NOUVEAU** - Facteur qualité (0.0-1.0) |

**Index existants** (conservés) :
- `idx_sources_domain` ON sources(domain)
- `idx_sources_score` ON sources(personal_score)

**Nouveaux index** :
- `idx_sources_is_seed` ON sources(is_seed)
- `idx_sources_is_promoted` ON sources(is_promoted)
- `idx_sources_role` ON sources(role)

---

### SourceTheme (nouvelle)

Table de jonction pour relation many-to-many sources ↔ thèmes.

| Colonne | Type | Contrainte | Description |
|---------|------|------------|-------------|
| `source_id` | TEXT | FK sources(id) | Référence source |
| `theme` | TEXT | NOT NULL | Nom du thème (ex: "ai-agents") |

**Contraintes** :
- `PRIMARY KEY (source_id, theme)`
- `FOREIGN KEY (source_id) REFERENCES sources(id) ON DELETE CASCADE`

**Index** :
- `idx_source_themes_theme` ON source_themes(theme)

---

### KnownDomain (nouvelle)

Table de référence pour classification automatique hub/authority.

| Colonne | Type | Contrainte | Description |
|---------|------|------------|-------------|
| `domain` | TEXT | PK | Domaine (ex: "stackoverflow.com") |
| `role` | TEXT | NOT NULL | hub/authority |
| `notes` | TEXT | | Notes optionnelles |
| `created_at` | TEXT | NOT NULL | ISO timestamp |

**Données initiales** (~50 domaines) :

```sql
-- Authorities (documentation officielle, specs)
INSERT INTO known_domains VALUES ('developer.mozilla.org', 'authority', 'MDN Web Docs', datetime('now'));
INSERT INTO known_domains VALUES ('docs.python.org', 'authority', 'Python docs', datetime('now'));
INSERT INTO known_domains VALUES ('tc39.es', 'authority', 'ECMAScript specs', datetime('now'));
INSERT INTO known_domains VALUES ('www.w3.org', 'authority', 'W3C specs', datetime('now'));
INSERT INTO known_domains VALUES ('www.rfc-editor.org', 'authority', 'RFCs', datetime('now'));
INSERT INTO known_domains VALUES ('rust-lang.org', 'authority', 'Rust docs', datetime('now'));
INSERT INTO known_domains VALUES ('go.dev', 'authority', 'Go docs', datetime('now'));
INSERT INTO known_domains VALUES ('react.dev', 'authority', 'React docs', datetime('now'));
INSERT INTO known_domains VALUES ('vuejs.org', 'authority', 'Vue docs', datetime('now'));
INSERT INTO known_domains VALUES ('angular.io', 'authority', 'Angular docs', datetime('now'));
INSERT INTO known_domains VALUES ('nodejs.org', 'authority', 'Node.js docs', datetime('now'));
INSERT INTO known_domains VALUES ('www.typescriptlang.org', 'authority', 'TypeScript docs', datetime('now'));
INSERT INTO known_domains VALUES ('kubernetes.io', 'authority', 'K8s docs', datetime('now'));
INSERT INTO known_domains VALUES ('docs.docker.com', 'authority', 'Docker docs', datetime('now'));
INSERT INTO known_domains VALUES ('www.sqlite.org', 'authority', 'SQLite docs', datetime('now'));
INSERT INTO known_domains VALUES ('www.postgresql.org', 'authority', 'PostgreSQL docs', datetime('now'));

-- Hubs (agrégateurs, forums, news)
INSERT INTO known_domains VALUES ('stackoverflow.com', 'hub', 'Q&A dev', datetime('now'));
INSERT INTO known_domains VALUES ('news.ycombinator.com', 'hub', 'Hacker News', datetime('now'));
INSERT INTO known_domains VALUES ('reddit.com', 'hub', 'Reddit', datetime('now'));
INSERT INTO known_domains VALUES ('github.com', 'hub', 'GitHub repos/issues', datetime('now'));
INSERT INTO known_domains VALUES ('dev.to', 'hub', 'Dev community', datetime('now'));
INSERT INTO known_domains VALUES ('medium.com', 'hub', 'Blog platform', datetime('now'));
INSERT INTO known_domains VALUES ('hashnode.dev', 'hub', 'Blog platform', datetime('now'));
INSERT INTO known_domains VALUES ('lobste.rs', 'hub', 'Tech news', datetime('now'));
INSERT INTO known_domains VALUES ('slashdot.org', 'hub', 'Tech news', datetime('now'));
```

---

## Relationships

```
┌─────────────┐       ┌───────────────┐       ┌──────────────┐
│   sources   │───────│ source_themes │───────│    themes    │
│             │  1:N  │               │  N:1  │  (implicit)  │
└─────────────┘       └───────────────┘       └──────────────┘
       │
       │ domain lookup
       ▼
┌──────────────┐
│ known_domains│
│              │
└──────────────┘

┌─────────────┐       ┌───────────────┐
│   entries   │───────│ entry_sources │
│             │  1:N  │               │
└─────────────┘       └───────────────┘
                             │
                             │ N:1
                             ▼
                      ┌─────────────┐
                      │   sources   │
                      └─────────────┘
```

---

## State Transitions

### Source Lifecycle

```
                    ┌─────────────┐
                    │   CREATED   │
                    └──────┬──────┘
                           │
           ┌───────────────┴───────────────┐
           │                               │
           ▼                               ▼
   ┌───────────────┐               ┌───────────────┐
   │  SEED (migré) │               │    NORMAL     │
   └───────┬───────┘               └───────┬───────┘
           │                               │
           │ (permanent)                   │ (critères atteints)
           │                               ▼
           │                       ┌───────────────┐
           │                       │   PROMOTED    │
           │                       └───────┬───────┘
           │                               │
           │                               │ (critères perdus)
           │                               ▼
           │                       ┌───────────────┐
           │                       │  DEMOTED      │
           │                       │  (= NORMAL)   │
           └───────────────────────┴───────────────┘
```

### Promotion Criteria

| Critère | Seuil | Condition |
|---------|-------|-----------|
| `usage_count` | ≥ 3 | Source citée au moins 3 fois |
| `personal_score` | ≥ 30 | Score dans le top 30% |
| `last_used` | ≤ 180 jours | Utilisée dans les 6 derniers mois |

**Exemption** : Les sources `is_seed=1` ne sont jamais rétrogradées.

---

## Validation Rules

### Source

1. `domain` doit être un domaine valide (regex: `^[a-z0-9.-]+\.[a-z]{2,}$`)
2. `role` doit être dans `('hub', 'authority', 'unclassified')`
3. `reliability` doit être dans `('A', 'B', 'C')`
4. `decay_rate` doit être dans `('fast', 'medium', 'slow')`
5. `status` doit être dans `('active', 'inaccessible')`
6. `is_seed` et `is_promoted` sont mutuellement exclusifs logiquement (seed n'a pas besoin de promotion)

### SourceTheme

1. `theme` doit être en kebab-case (`^[a-z0-9-]+$`)
2. Combinaison `(source_id, theme)` unique

### KnownDomain

1. `domain` unique
2. `role` doit être dans `('hub', 'authority')`

---

## Migration SQL (v8 → v9)

```sql
-- Migration 9: Sources Autonomes
PRAGMA foreign_keys=OFF;

-- 1. Ajouter colonnes à sources
ALTER TABLE sources ADD COLUMN is_seed INTEGER DEFAULT 0;
ALTER TABLE sources ADD COLUMN is_promoted INTEGER DEFAULT 0;
ALTER TABLE sources ADD COLUMN promoted_at TEXT;
ALTER TABLE sources ADD COLUMN role TEXT DEFAULT 'unclassified';
ALTER TABLE sources ADD COLUMN seed_origin TEXT;
ALTER TABLE sources ADD COLUMN citation_quality_factor REAL DEFAULT 0.0;

-- 2. Créer index
CREATE INDEX IF NOT EXISTS idx_sources_is_seed ON sources(is_seed);
CREATE INDEX IF NOT EXISTS idx_sources_is_promoted ON sources(is_promoted);
CREATE INDEX IF NOT EXISTS idx_sources_role ON sources(role);

-- 3. Créer table source_themes
CREATE TABLE IF NOT EXISTS source_themes (
    source_id TEXT NOT NULL,
    theme TEXT NOT NULL,
    PRIMARY KEY (source_id, theme),
    FOREIGN KEY (source_id) REFERENCES sources(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_source_themes_theme ON source_themes(theme);

-- 4. Créer table known_domains
CREATE TABLE IF NOT EXISTS known_domains (
    domain TEXT PRIMARY KEY,
    role TEXT NOT NULL CHECK(role IN ('hub', 'authority')),
    notes TEXT,
    created_at TEXT NOT NULL
);

-- 5. Insérer données initiales known_domains
-- (voir section KnownDomain ci-dessus)

-- 6. Mettre à jour version
UPDATE schema_version SET version = 9;

PRAGMA foreign_keys=ON;
```

---

## Scoring Formula v2

```python
def calculate_source_score_v2(source: Source, db: Database) -> float:
    """
    Score SOTA avec citation quality.

    Composants:
    - usage_factor: log10(usage+1) / log10(100)  # 0-1
    - citation_quality: moyenne scores co-citations  # 0-1
    - freshness: 0.5^(days/half_life)  # decay exponentiel
    - reliability: A=1.0, B=0.8, C=0.6
    - role_bonus: authority=1.2, hub=1.0, unclassified=1.0
    - seed_bonus: +20% si is_seed
    """
    import math

    HALF_LIVES = {'fast': 90, 'medium': 180, 'slow': 365}
    RELIABILITY = {'A': 1.0, 'B': 0.8, 'C': 0.6}
    ROLE_BONUS = {'authority': 1.2, 'hub': 1.0, 'unclassified': 1.0}

    # Usage factor (logarithmique)
    usage_factor = min(math.log10(source.usage_count + 1) / math.log10(100), 1.0)

    # Citation quality (si disponible)
    citation_quality = source.citation_quality_factor or 0.5

    # Freshness (decay)
    if source.last_used:
        days = (datetime.now() - source.last_used).days
        half_life = HALF_LIVES[source.decay_rate]
        freshness = 0.5 ** (days / half_life)
    else:
        freshness = 0.5

    # Facteurs multiplicatifs
    reliability = RELIABILITY.get(source.reliability, 0.6)
    role_bonus = ROLE_BONUS.get(source.role, 1.0)
    seed_bonus = 1.2 if source.is_seed else 1.0

    # Score final (base 50, max ~100)
    score = (
        50 *
        (0.3 + 0.7 * usage_factor) *
        (0.4 + 0.6 * citation_quality) *
        freshness *
        reliability *
        role_bonus *
        seed_bonus
    )

    return min(max(score, 0), 100)
```
