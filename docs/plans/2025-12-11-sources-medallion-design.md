# Design: Sources Medallion Architecture

**Date**: 2025-12-11
**Status**: Validated
**Feature**: 013-sources-medallion

---

## Overview

Architecture en 3 couches (Bronze/Silver/Gold) pour capturer automatiquement les URLs citées dans les conversations avec les CLIs IA, les enrichir progressivement, et les promouvoir vers les sources curées.

## Architecture Globale

```
┌─────────────────────────────────────────────────────────────────┐
│                    SOURCES MEDALLION                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐       │
│  │   BRONZE    │ ──► │   SILVER    │ ──► │    GOLD     │       │
│  │  (inbox)    │     │ (enriched)  │     │  (curated)  │       │
│  └──────┬──────┘     └──────┬──────┘     └─────────────┘       │
│         │                   │                   ▲               │
│         │                   │                   │               │
│  ┌──────┴──────┐     ┌──────┴──────┐     ┌──────┴──────┐       │
│  │  Capture    │     │ Enrichment  │     │  Promotion  │       │
│  │  - MCP push │     │  (background)│     │  (seuil +   │       │
│  │  - Import   │     │  - title    │     │   manuel)   │       │
│  │    history  │     │  - dedup    │     │             │       │
│  └─────────────┘     │  - verify   │     └─────────────┘       │
│                      └─────────────┘                            │
└─────────────────────────────────────────────────────────────────┘
```

## Mécanismes de Capture

### 1. Push Temps Réel (MCP)

Le serveur MCP existant (`rekall/mcp_server.py`) sera étendu avec un nouvel outil :

```python
rekall_capture_url(url, context)  # Ajoute en Bronze
```

### 2. Import Historique (Connecteurs Plugin)

Architecture plugin permettant d'ajouter progressivement des connecteurs :

- **Claude CLI** : Parse `~/.claude/projects/{project}/*.jsonl`
- **Cursor** : À implémenter (format à déterminer)
- Autres CLIs : Ajoutés progressivement

---

## Schéma des Tables

### Bronze : `sources_inbox`

```sql
CREATE TABLE sources_inbox (
    id TEXT PRIMARY KEY,           -- ULID
    url TEXT NOT NULL,
    domain TEXT,                   -- Extrait de l'URL

    -- Contexte de capture
    cli_source TEXT NOT NULL,      -- 'claude', 'cursor', 'windsurf'...
    project TEXT,                  -- Projet où l'URL a été citée
    conversation_id TEXT,          -- ID session/conversation
    user_query TEXT,               -- Question de l'utilisateur
    assistant_snippet TEXT,        -- Extrait réponse assistant
    surrounding_text TEXT,         -- Contexte autour de l'URL

    -- Métadonnées
    captured_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    import_source TEXT,            -- 'realtime' ou 'history_import'
    raw_json TEXT                  -- Données brutes pour debug
);

CREATE INDEX idx_inbox_url ON sources_inbox(url);
CREATE INDEX idx_inbox_domain ON sources_inbox(domain);
CREATE INDEX idx_inbox_cli ON sources_inbox(cli_source);
CREATE INDEX idx_inbox_captured ON sources_inbox(captured_at);
```

### Silver : `sources_staging`

```sql
CREATE TABLE sources_staging (
    id TEXT PRIMARY KEY,           -- ULID
    url TEXT NOT NULL UNIQUE,      -- Dédupliqué
    domain TEXT NOT NULL,

    -- Enrichissement
    title TEXT,                    -- Extrait de la page
    description TEXT,              -- Meta description
    last_verified TIMESTAMP,       -- Dernière vérif accessibilité
    is_accessible BOOLEAN DEFAULT TRUE,

    -- Score de promotion
    citation_count INTEGER DEFAULT 1,
    project_count INTEGER DEFAULT 1,
    first_seen TIMESTAMP,
    last_seen TIMESTAMP,
    promotion_score REAL DEFAULT 0.0,

    -- Tracking
    inbox_ids TEXT,                -- JSON array des IDs bronze fusionnés
    enriched_at TIMESTAMP,
    promoted_at TIMESTAMP,         -- NULL si pas encore promu
    promoted_to TEXT,              -- ID de la source Gold si promu

    UNIQUE(url)
);

CREATE INDEX idx_staging_domain ON sources_staging(domain);
CREATE INDEX idx_staging_score ON sources_staging(promotion_score);
CREATE INDEX idx_staging_promoted ON sources_staging(promoted_at);
```

### Gold : `sources` (existante)

Table inchangée. Les sources promues y sont ajoutées avec :
- `is_promoted = TRUE`
- `promoted_at = timestamp`
- Lien vers `sources_staging.id` pour traçabilité

---

## Connecteurs d'Import

### Structure Plugin

```
rekall/connectors/
├── __init__.py          # Registry des connecteurs
├── base.py              # Classe abstraite BaseConnector
├── claude_cli.py        # Connecteur Claude Code
└── cursor.py            # Connecteur Cursor
```

### Interface BaseConnector

```python
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Iterator
from dataclasses import dataclass

@dataclass
class InboxEntry:
    url: str
    cli_source: str
    project: str | None
    conversation_id: str | None
    user_query: str | None
    assistant_snippet: str | None
    surrounding_text: str | None
    captured_at: datetime
    raw_json: str | None = None

class BaseConnector(ABC):
    """Base pour tous les connecteurs d'import."""

    name: str              # 'claude_cli', 'cursor'
    description: str

    @abstractmethod
    def get_history_paths(self) -> list[Path]:
        """Retourne les chemins des fichiers d'historique."""

    @abstractmethod
    def extract_urls(self, path: Path, since: datetime | None = None) -> Iterator[InboxEntry]:
        """Extrait les URLs d'un fichier d'historique."""

    def get_last_import_marker(self, db) -> datetime | None:
        """Retourne le timestamp du dernier import pour ce connecteur."""
        return db.get_connector_last_import(self.name)

    def set_last_import_marker(self, db, timestamp: datetime):
        """Enregistre le timestamp du dernier import."""
        db.set_connector_last_import(self.name, timestamp)
```

### Connecteur Claude CLI

```python
class ClaudeCLIConnector(BaseConnector):
    name = "claude_cli"
    description = "Import depuis Claude Code CLI"

    def get_history_paths(self) -> list[Path]:
        base = Path.home() / ".claude" / "projects"
        return list(base.glob("*/*.jsonl"))

    def extract_urls(self, path: Path, since: datetime | None = None) -> Iterator[InboxEntry]:
        project = self._extract_project_name(path)

        with open(path) as f:
            for line in f:
                entry = json.loads(line)

                # Filtrer par date si spécifié
                if since and entry.get("timestamp", 0) < since.timestamp() * 1000:
                    continue

                # Extraire URLs des tool_calls WebFetch
                urls = self._extract_urls_from_entry(entry)

                for url, context in urls:
                    yield InboxEntry(
                        url=url,
                        cli_source=self.name,
                        project=project,
                        conversation_id=path.stem,
                        user_query=context.get("user_query"),
                        assistant_snippet=context.get("assistant_snippet"),
                        surrounding_text=context.get("surrounding_text"),
                        captured_at=datetime.fromtimestamp(entry["timestamp"] / 1000),
                        raw_json=json.dumps(entry),
                    )
```

---

## Enrichissement & Promotion

### Enrichissement Background (Bronze → Silver)

```python
def enrich_inbox_entries():
    """Job d'enrichissement des entrées Bronze vers Silver."""

    pending = db.get_inbox_not_enriched()

    for entry in pending:
        # 1. Extraction domaine
        domain = extract_domain(entry.url)

        # 2. Déduplication - chercher URL existante en Silver
        existing = db.get_staging_by_url(entry.url)

        if existing:
            # Fusionner : incrémenter compteurs
            existing.citation_count += 1
            projects = json.loads(existing.inbox_ids or "[]")
            if entry.project and entry.project not in projects:
                existing.project_count += 1
            existing.last_seen = datetime.now()
            existing.inbox_ids = json.dumps(projects + [entry.id])
            existing.promotion_score = calculate_promotion_score(existing)
            db.update_staging(existing)
        else:
            # 3. Fetch métadonnées (titre, description)
            title, description = fetch_page_metadata(entry.url)

            # 4. Créer entrée Silver
            staging = StagingEntry(
                url=entry.url,
                domain=domain,
                title=title,
                description=description,
                citation_count=1,
                project_count=1,
                first_seen=entry.captured_at,
                last_seen=datetime.now(),
                inbox_ids=json.dumps([entry.id]),
                enriched_at=datetime.now(),
            )
            staging.promotion_score = calculate_promotion_score(staging)
            db.add_staging(staging)

        # Marquer Bronze comme traité
        db.mark_inbox_enriched(entry.id)
```

### Score de Promotion (Configurable)

```python
# Config par défaut
DEFAULT_PROMOTION_WEIGHTS = {
    "citation": 1.0,      # × nombre de citations
    "project": 2.0,       # × nombre de projets distincts
    "recency": 0.5,       # × boost si vu récemment (0-1)
}
DEFAULT_PROMOTION_THRESHOLD = 5.0

def calculate_promotion_score(staging: StagingEntry) -> float:
    """Calcule le score de promotion d'une source."""
    config = get_config()
    weights = config.promotion_weights or DEFAULT_PROMOTION_WEIGHTS

    # Calcul récence (1.0 si vu aujourd'hui, décroît)
    days_since = (datetime.now() - staging.last_seen).days
    recency_factor = max(0, 1.0 - (days_since / 30))

    return (
        staging.citation_count * weights["citation"] +
        staging.project_count * weights["project"] +
        recency_factor * weights["recency"]
    )
```

### Promotion Automatique (Silver → Gold)

```python
def check_auto_promotion():
    """Vérifie et promeut les sources éligibles."""
    config = get_config()
    threshold = config.promotion_threshold or DEFAULT_PROMOTION_THRESHOLD

    candidates = db.get_staging_above_threshold(threshold)

    for staging in candidates:
        if staging.promoted_at:
            continue  # Déjà promu

        # Créer source Gold
        gold_source = Source(
            domain=staging.domain,
            url_pattern=staging.url,
            personal_score=50.0,  # Score initial
            is_promoted=True,
            promoted_at=datetime.now(),
        )
        source_id = db.add_source(gold_source)

        # Marquer Silver comme promu
        db.mark_staging_promoted(staging.id, source_id)

        logger.info(f"Auto-promoted: {staging.url} (score={staging.promotion_score})")
```

### Dépromouvoir (Gold → Silver)

```python
def demote_source(source_id: str) -> bool:
    """Dépromeut une source Gold vers Silver."""
    source = db.get_source(source_id)
    if not source or not source.is_promoted:
        return False

    # Retrouver l'entrée Silver
    staging = db.get_staging_by_promoted_id(source_id)
    if staging:
        staging.promoted_at = None
        staging.promoted_to = None
        db.update_staging(staging)

    # Supprimer la source Gold
    db.delete_source(source_id)

    return True
```

---

## Interface CLI

```bash
# === INBOX (Bronze) ===
rekall sources inbox                     # TUI: voir inbox
rekall sources inbox import              # Import tous les connecteurs
rekall sources inbox import --cli claude # Import Claude uniquement
rekall sources inbox import --since 7d   # Derniers 7 jours
rekall sources inbox stats               # Compteurs par CLI/projet
rekall sources inbox clear               # Vider inbox (après enrichissement)

# === STAGING (Silver) ===
rekall sources staging                   # TUI: voir staging avec scores
rekall sources staging enrich            # Forcer enrichissement maintenant
rekall sources staging promote URL       # Promotion manuelle → Gold
rekall sources staging drop URL          # Supprimer du staging

# === SOURCES (Gold) - existant + extensions ===
rekall sources                           # TUI existant (DataTable)
rekall sources demote ID                 # Dépromouvoir → Silver

# === CONFIG ===
rekall config promotion-threshold 5.0    # Modifier seuil
rekall config promotion-weights ...      # Modifier poids
```

---

## Interface TUI

### Menu Sources (modifié)

```
Sources
├── Toutes les sources (Gold)      # Existant
├── Parcourir par tag              # Existant
├── Recherche avancée              # Existant
├── ──────────────────
├── Inbox (Bronze)                 # NOUVEAU
├── Staging (Silver)               # NOUVEAU
├── Import historique              # NOUVEAU
└── ──────────────────
    Mes vues                       # Existant
```

### TUI Inbox (Bronze)

```
┌─ Sources Inbox (23 nouvelles) ─────────────────────────────────┐
│                                                                 │
│  URL                          CLI      Projet        Capturé   │
│  ─────────────────────────────────────────────────────────────  │
│  docs.python.org/3/lib...     claude   rekall        il y a 2h │
│  github.com/anthropics/...    claude   rekall        il y a 3h │
│  stackoverflow.com/q/123...   cursor   bigmind       hier      │
│                                                                 │
│  [i] Import  [e] Enrichir  [d] Supprimer  [Esc] Retour         │
└─────────────────────────────────────────────────────────────────┘
```

### TUI Staging (Silver)

```
┌─ Sources Staging (12 enrichies) ────────────────────────────────┐
│                                                                  │
│  Domaine              Titre           Citations  Projets  Score │
│  ──────────────────────────────────────────────────────────────  │
│  docs.python.org      Python Docs          5        3     8.5 ⬆ │
│  github.com           Anthropic SDK        3        2     5.0 → │
│  stackoverflow.com    SQLite UPSERT        2        1     2.5   │
│                                                                  │
│  [p] Promouvoir  [d] Supprimer  [r] Refresh  [Esc] Retour       │
└──────────────────────────────────────────────────────────────────┘

# Indicateurs: ⬆ = éligible promotion (≥ seuil), → = proche seuil (≥ 80%)
```

---

## Migration

### Version 11

```python
MIGRATIONS[11] = """
-- Bronze: Sources inbox
CREATE TABLE IF NOT EXISTS sources_inbox (
    id TEXT PRIMARY KEY,
    url TEXT NOT NULL,
    domain TEXT,
    cli_source TEXT NOT NULL,
    project TEXT,
    conversation_id TEXT,
    user_query TEXT,
    assistant_snippet TEXT,
    surrounding_text TEXT,
    captured_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    import_source TEXT,
    raw_json TEXT,
    enriched_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_inbox_url ON sources_inbox(url);
CREATE INDEX IF NOT EXISTS idx_inbox_cli ON sources_inbox(cli_source);
CREATE INDEX IF NOT EXISTS idx_inbox_captured ON sources_inbox(captured_at);

-- Silver: Sources staging
CREATE TABLE IF NOT EXISTS sources_staging (
    id TEXT PRIMARY KEY,
    url TEXT NOT NULL UNIQUE,
    domain TEXT NOT NULL,
    title TEXT,
    description TEXT,
    last_verified TIMESTAMP,
    is_accessible BOOLEAN DEFAULT TRUE,
    citation_count INTEGER DEFAULT 1,
    project_count INTEGER DEFAULT 1,
    first_seen TIMESTAMP,
    last_seen TIMESTAMP,
    promotion_score REAL DEFAULT 0.0,
    inbox_ids TEXT,
    enriched_at TIMESTAMP,
    promoted_at TIMESTAMP,
    promoted_to TEXT
);

CREATE INDEX IF NOT EXISTS idx_staging_score ON sources_staging(promotion_score);

-- Tracking des imports par connecteur
CREATE TABLE IF NOT EXISTS connector_imports (
    connector TEXT PRIMARY KEY,
    last_import TIMESTAMP,
    entries_count INTEGER DEFAULT 0
);
"""
```

---

## Fichiers à Créer/Modifier

| Fichier | Action | Description |
|---------|--------|-------------|
| `rekall/connectors/__init__.py` | Créer | Registry connecteurs |
| `rekall/connectors/base.py` | Créer | Classe abstraite |
| `rekall/connectors/claude_cli.py` | Créer | Connecteur Claude |
| `rekall/connectors/cursor.py` | Créer | Connecteur Cursor (stub) |
| `rekall/db.py` | Modifier | Migration v11 + fonctions CRUD |
| `rekall/tui.py` | Modifier | TUI Inbox + Staging + menu |
| `rekall/cli.py` | Modifier | Commandes inbox/staging |
| `rekall/mcp_server.py` | Modifier | Tool capture_url |
| `rekall/config.py` | Modifier | Config promotion weights/threshold |
| `rekall/i18n.py` | Modifier | Traductions |

---

## Phases d'Implémentation

### Phase 1: Foundation
- Migration v11 (tables Bronze + Silver)
- Fonctions DB CRUD pour inbox et staging
- Traductions

### Phase 2: Connecteurs
- Architecture plugin base
- Connecteur Claude CLI
- Stub Cursor (à compléter plus tard)

### Phase 3: Enrichissement
- Job d'enrichissement Bronze → Silver
- Calcul score de promotion
- Fetch métadonnées (titre, description)

### Phase 4: Promotion
- Promotion automatique sur seuil
- Promotion manuelle
- Dépromouvoir

### Phase 5: Interface
- TUI Inbox (Bronze)
- TUI Staging (Silver)
- Commandes CLI
- Extension MCP

### Phase 6: Polish
- Tests unitaires
- Documentation
- Config UI pour poids/seuil
