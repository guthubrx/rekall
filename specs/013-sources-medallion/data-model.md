# Data Model: Sources Medallion Architecture

**Feature**: 013-sources-medallion
**Date**: 2025-12-11
**Schema Version**: 11 (extension de v10)

---

## Vue d'Ensemble

```
┌─────────────────────────────────────────────────────────────────┐
│                    MEDALLION DATA FLOW                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  BRONZE                    SILVER                   GOLD        │
│  ┌──────────────┐         ┌──────────────┐         ┌──────────┐│
│  │sources_inbox │ ──N:1──►│sources_staging│ ──1:1──►│ sources  ││
│  │              │         │              │         │(existant)││
│  │ - url        │         │ - url UNIQUE │         │ - domain ││
│  │ - cli_source │         │ - title      │         │ - is_prom││
│  │ - project    │         │ - score      │         │ - prom_at││
│  │ - is_valid   │         │ - citation#  │         └──────────┘│
│  └──────────────┘         └──────────────┘              ▲       │
│         ▲                        ▲                      │       │
│         │                        │                      │       │
│  ┌──────┴───────┐         ┌──────┴───────┐       ┌─────┴─────┐ │
│  │connector_    │         │  enrichment  │       │ promotion │ │
│  │imports       │         │  job         │       │ job       │ │
│  │(CDC tracking)│         │              │       │           │ │
│  └──────────────┘         └──────────────┘       └───────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

---

## Entités

### 1. InboxEntry (Bronze Layer)

URL capturée brute avec tout le contexte de capture.

```python
@dataclass
class InboxEntry:
    """URL capturée depuis un CLI IA, non transformée."""

    # Identifiant
    id: str                          # ULID (26 chars, sortable)

    # Donnée principale
    url: str                         # URL complète capturée
    domain: str | None               # Domaine extrait (e.g., "github.com")

    # Contexte de capture (provenance)
    cli_source: str                  # 'claude_cli' | 'cursor' | 'windsurf' | ...
    project: str | None              # Projet où l'URL a été citée
    conversation_id: str | None      # ID session/conversation source
    user_query: str | None           # Question utilisateur (contexte)
    assistant_snippet: str | None    # Extrait réponse (max 500 chars)
    surrounding_text: str | None     # Texte autour de l'URL

    # Métadonnées capture
    captured_at: datetime            # Timestamp de capture
    import_source: str               # 'realtime' | 'history_import'
    raw_json: str | None             # Données brutes pour debug

    # Quarantine (validation)
    is_valid: bool = True            # False si URL invalide
    validation_error: str | None     # Raison si is_valid=False

    # Processing state
    enriched_at: datetime | None     # Timestamp si traité → Silver
```

**Contraintes**:
- `url` NOT NULL
- `cli_source` NOT NULL
- `captured_at` NOT NULL avec default CURRENT_TIMESTAMP

**Index**:
- `idx_inbox_url` ON (url) - Recherche par URL
- `idx_inbox_domain` ON (domain) - Filtrage par domaine
- `idx_inbox_cli` ON (cli_source) - Stats par connecteur
- `idx_inbox_captured` ON (captured_at) - Tri chronologique
- `idx_inbox_valid` ON (is_valid) - Vue quarantine
- `idx_inbox_enriched` ON (enriched_at) - Entrées non traitées

---

### 2. StagingEntry (Silver Layer)

URL enrichie et dédupliquée, candidate à promotion.

```python
@dataclass
class StagingEntry:
    """URL enrichie avec métadonnées, prête pour promotion."""

    # Identifiant
    id: str                          # ULID

    # Donnée principale (dédupliquée)
    url: str                         # URL UNIQUE dans staging
    domain: str                      # Domaine normalisé

    # Enrichissement métadonnées
    title: str | None                # Titre page (from HTML)
    description: str | None          # Meta description
    content_type: str | None         # 'documentation' | 'repository' | 'forum' | ...
    language: str | None             # Code langue (e.g., 'en', 'fr')

    # Accessibilité
    last_verified: datetime | None   # Dernière vérification HTTP
    is_accessible: bool = True       # False si 4xx/5xx
    http_status: int | None          # Dernier code HTTP

    # Compteurs (agrégés depuis Bronze)
    citation_count: int = 1          # Nombre total de citations
    project_count: int = 1           # Nombre de projets distincts
    projects_list: str | None        # JSON array des projets uniques
    first_seen: datetime | None      # Première apparition
    last_seen: datetime | None       # Dernière apparition

    # Score de promotion
    promotion_score: float = 0.0     # Score calculé (voir formule)

    # Traçabilité
    inbox_ids: str | None            # JSON array des IDs Bronze fusionnés
    enriched_at: datetime | None     # Timestamp enrichissement

    # Promotion state
    promoted_at: datetime | None     # Timestamp si promu → Gold
    promoted_to: str | None          # ID de la source Gold
```

**Contraintes**:
- `url` NOT NULL UNIQUE
- `domain` NOT NULL
- `promotion_score` DEFAULT 0.0

**Index**:
- `idx_staging_domain` ON (domain) - Filtrage par domaine
- `idx_staging_score` ON (promotion_score DESC) - Tri par score
- `idx_staging_promoted` ON (promoted_at) - Entrées non promues
- `idx_staging_content_type` ON (content_type) - Filtrage par type

---

### 3. ConnectorImport (CDC Tracking)

Suivi des imports pour le Change Data Capture.

```python
@dataclass
class ConnectorImport:
    """Tracking des imports par connecteur pour CDC."""

    connector: str                   # 'claude_cli' | 'cursor' | ...
    last_import: datetime | None     # Timestamp dernier import réussi
    last_file_marker: str | None     # Marker pour import incrémental
    entries_imported: int = 0        # Total entrées importées
    errors_count: int = 0            # Total erreurs rencontrées
```

**Contraintes**:
- `connector` PRIMARY KEY
- `entries_imported` DEFAULT 0
- `errors_count` DEFAULT 0

---

### 4. Source (Gold Layer - Extension)

La table `sources` existante est étendue avec des champs de promotion.

```python
# Champs existants (inchangés)
@dataclass
class Source:
    id: str
    domain: str
    url_pattern: str | None
    usage_count: int
    last_used: datetime | None
    personal_score: float
    reliability: str  # 'A' | 'B' | 'C'
    decay_rate: str   # 'fast' | 'medium' | 'slow'
    last_verified: datetime | None
    status: str       # 'active' | 'inaccessible' | 'archived'
    created_at: datetime
    # ... autres champs Feature 010 ...

    # NOUVEAU: Champs promotion (Feature 013)
    # Note: is_promoted et promoted_at existent déjà via Feature 010
    # Nous les réutilisons pour marquer les sources promues depuis Silver
```

**Note**: Pas de modification de schema pour `sources`. Les champs `is_promoted` et `promoted_at` ajoutés en v9 sont réutilisés.

---

## Relations

### Bronze → Silver (N:1)
- Plusieurs `InboxEntry` avec la même URL fusionnent en une seule `StagingEntry`
- `StagingEntry.inbox_ids` contient la liste des IDs Bronze fusionnés
- `StagingEntry.citation_count` = nombre d'InboxEntry fusionnées

### Silver → Gold (1:1)
- Une `StagingEntry` promue crée exactement une `Source`
- `StagingEntry.promoted_to` = `Source.id`
- `Source.is_promoted` = TRUE
- `Source.promoted_at` = timestamp de promotion

### Suppression (Cascade)
- Supprimer une `StagingEntry` ne supprime PAS les `InboxEntry` (traçabilité)
- Supprimer une `Source` promue → `StagingEntry.promoted_to` = NULL (SET NULL)

---

## États et Transitions

### InboxEntry States

```
┌──────────────┐
│   CAPTURED   │ ←── Import initial
└──────┬───────┘
       │ validate_url()
       ▼
┌──────┴───────┐
│   is_valid?  │
├──────────────┤
│ TRUE → VALID │ ─────► ENRICHED (enriched_at set)
│ FALSE → QUARANTINE │ ─────► STAY (manual review)
└──────────────┘
```

### StagingEntry States

```
┌──────────────┐
│   PENDING    │ ←── Créé depuis Bronze
└──────┬───────┘
       │ fetch_metadata()
       ▼
┌──────────────┐
│  ENRICHED    │ ←── title/description set
└──────┬───────┘
       │ check_score()
       ▼
┌──────┴───────┐
│ score >= threshold?
├──────────────┤
│ YES → ELIGIBLE │ ─────► PROMOTED (via auto ou manual)
│ NO  → PENDING  │ ─────► STAY (attendre plus de citations)
└──────────────┘
```

---

## Validation Rules

### URL Validation

```python
def validate_url(url: str) -> tuple[bool, str | None]:
    """Valide une URL avant insertion en Bronze."""

    # Doit commencer par http:// ou https://
    if not url.startswith(('http://', 'https://')):
        return False, "Invalid URL scheme"

    # Patterns à exclure
    skip_patterns = [
        'localhost',
        '127.0.0.1',
        '0.0.0.0',
        'file://',
        'chrome://',
        'about:',
        'rekall://',  # URLs internes Rekall
        '192.168.',   # IPs locales
        '10.',        # IPs locales
    ]

    for pattern in skip_patterns:
        if pattern in url.lower():
            return False, f"Skipped pattern: {pattern}"

    return True, None
```

### Promotion Eligibility

```python
def is_eligible_for_promotion(staging: StagingEntry, threshold: float) -> bool:
    """Vérifie si une source Silver est éligible à la promotion."""

    # Déjà promue
    if staging.promoted_at is not None:
        return False

    # Score insuffisant
    if staging.promotion_score < threshold:
        return False

    # Doit être accessible
    if not staging.is_accessible:
        return False

    return True
```

---

## Schéma SQL (Migration v11)

```sql
-- =============================================
-- Migration v11: Sources Medallion Architecture
-- =============================================

-- Bronze: Sources inbox (raw captured URLs)
CREATE TABLE IF NOT EXISTS sources_inbox (
    id TEXT PRIMARY KEY,
    url TEXT NOT NULL,
    domain TEXT,

    -- Capture context
    cli_source TEXT NOT NULL,
    project TEXT,
    conversation_id TEXT,
    user_query TEXT,
    assistant_snippet TEXT,
    surrounding_text TEXT,

    -- Metadata
    captured_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    import_source TEXT,
    raw_json TEXT,

    -- Quarantine
    is_valid BOOLEAN DEFAULT TRUE,
    validation_error TEXT,

    -- Processing
    enriched_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_inbox_url ON sources_inbox(url);
CREATE INDEX IF NOT EXISTS idx_inbox_domain ON sources_inbox(domain);
CREATE INDEX IF NOT EXISTS idx_inbox_cli ON sources_inbox(cli_source);
CREATE INDEX IF NOT EXISTS idx_inbox_captured ON sources_inbox(captured_at);
CREATE INDEX IF NOT EXISTS idx_inbox_valid ON sources_inbox(is_valid);
CREATE INDEX IF NOT EXISTS idx_inbox_enriched ON sources_inbox(enriched_at);

-- Silver: Sources staging (enriched, deduplicated)
CREATE TABLE IF NOT EXISTS sources_staging (
    id TEXT PRIMARY KEY,
    url TEXT NOT NULL UNIQUE,
    domain TEXT NOT NULL,

    -- Enrichment
    title TEXT,
    description TEXT,
    content_type TEXT,
    language TEXT,

    -- Accessibility
    last_verified TIMESTAMP,
    is_accessible BOOLEAN DEFAULT TRUE,
    http_status INTEGER,

    -- Aggregation
    citation_count INTEGER DEFAULT 1,
    project_count INTEGER DEFAULT 1,
    projects_list TEXT,
    first_seen TIMESTAMP,
    last_seen TIMESTAMP,

    -- Scoring
    promotion_score REAL DEFAULT 0.0,

    -- Traceability
    inbox_ids TEXT,
    enriched_at TIMESTAMP,

    -- Promotion
    promoted_at TIMESTAMP,
    promoted_to TEXT,

    FOREIGN KEY (promoted_to) REFERENCES sources(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_staging_domain ON sources_staging(domain);
CREATE INDEX IF NOT EXISTS idx_staging_score ON sources_staging(promotion_score DESC);
CREATE INDEX IF NOT EXISTS idx_staging_promoted ON sources_staging(promoted_at);
CREATE INDEX IF NOT EXISTS idx_staging_content_type ON sources_staging(content_type);

-- CDC Tracking: Import state per connector
CREATE TABLE IF NOT EXISTS connector_imports (
    connector TEXT PRIMARY KEY,
    last_import TIMESTAMP,
    last_file_marker TEXT,
    entries_imported INTEGER DEFAULT 0,
    errors_count INTEGER DEFAULT 0
);
```

---

## Types de Contenu (Énumération)

| Type | Description | Exemples Domaines |
|------|-------------|-------------------|
| `documentation` | Documentation officielle | docs.python.org, react.dev |
| `repository` | Dépôt de code | github.com, gitlab.com |
| `forum` | Q&A, discussions | stackoverflow.com |
| `blog` | Articles techniques | medium.com, dev.to |
| `api` | Documentation API | swagger, openapi |
| `paper` | Papers académiques | arxiv.org |
| `other` | Non classifié | (défaut) |

---

## Scoring Formula

```python
def calculate_promotion_score(
    citation_count: int,
    project_count: int,
    days_since_last_seen: int,
    config: PromotionConfig
) -> float:
    """Calcule le score de promotion d'une source Silver."""

    # Facteur récence avec decay linéaire
    recency_factor = max(0.0, 1.0 - (days_since_last_seen / config.decay_days))

    # Score = somme pondérée
    score = (
        citation_count * config.weights.citation +
        project_count * config.weights.project +
        recency_factor * config.weights.recency
    )

    return round(score, 2)
```

**Configuration par défaut**:
```python
DEFAULT_PROMOTION_CONFIG = {
    "weights": {
        "citation": 1.0,
        "project": 2.0,
        "recency": 0.5,
    },
    "threshold": 5.0,
    "decay_days": 30,
}
```
