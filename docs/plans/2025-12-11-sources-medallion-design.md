# Design: Sources Medallion Architecture

**Date**: 2025-12-11
**Status**: Validated + Enriched
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
│  │  - Quarant. │     │  - verify   │     │  Demote ↓   │       │
│  └─────────────┘     │  - classify │     └─────────────┘       │
│                      └─────────────┘                            │
└─────────────────────────────────────────────────────────────────┘
```

---

## Mécanismes de Capture

### 1. Push Temps Réel (MCP)

Le serveur MCP existant (`rekall/mcp_server.py`) sera étendu avec un nouvel outil :

```python
rekall_capture_url(url, context)  # Ajoute en Bronze
```

### 2. Import Historique (Connecteurs Plugin)

Architecture plugin permettant d'ajouter progressivement des connecteurs :

#### Claude CLI
- **Chemin** : `~/.claude/projects/{project-path}/*.jsonl`
- **Format** : JSONL avec messages user/assistant et tool_calls
- **Extraction** : URLs dans les `tool_use` de type `WebFetch`
- **⚠️ Rétention** : 30 jours par défaut (configurable dans `~/.claude/settings.json`)

**Outils de référence** :
- [claude-conversation-extractor](https://github.com/ZeroSumQuant/claude-conversation-extractor)
- [claude-history](https://github.com/thejud/claude-history)

#### Cursor IDE
- **Chemin** : `~/Library/Application Support/Cursor/User/workspaceStorage/{md5-hash}/state.vscdb`
- **Format** : SQLite database
- **Extraction** :
```sql
SELECT value FROM ItemTable
WHERE [key] IN ('aiService.prompts', 'workbench.panel.aichat.view.aichat.chatdata')
```

**Outils de référence** :
- [cursor-chat-export](https://github.com/somogyijanos/cursor-chat-export)
- [CursorChat Downloader](https://marketplace.visualstudio.com/items?itemName=abdelhakakermi.cursorchat-downloader)

---

## Schéma des Tables

### Bronze : `sources_inbox`

```sql
CREATE TABLE sources_inbox (
    id TEXT PRIMARY KEY,           -- ULID
    url TEXT NOT NULL,
    domain TEXT,                   -- Extrait de l'URL

    -- Contexte de capture
    cli_source TEXT NOT NULL,      -- 'claude_cli', 'cursor', 'windsurf'...
    project TEXT,                  -- Projet où l'URL a été citée
    conversation_id TEXT,          -- ID session/conversation
    user_query TEXT,               -- Question de l'utilisateur
    assistant_snippet TEXT,        -- Extrait réponse assistant (500 chars max)
    surrounding_text TEXT,         -- Contexte autour de l'URL

    -- Métadonnées
    captured_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    import_source TEXT,            -- 'realtime' ou 'history_import'
    raw_json TEXT,                 -- Données brutes pour debug

    -- Quarantine mechanism (best practice Databricks)
    is_valid BOOLEAN DEFAULT TRUE,
    validation_error TEXT,         -- Raison si is_valid = FALSE

    -- Processing tracking
    enriched_at TIMESTAMP          -- NULL si pas encore traité
);

CREATE INDEX idx_inbox_url ON sources_inbox(url);
CREATE INDEX idx_inbox_domain ON sources_inbox(domain);
CREATE INDEX idx_inbox_cli ON sources_inbox(cli_source);
CREATE INDEX idx_inbox_captured ON sources_inbox(captured_at);
CREATE INDEX idx_inbox_valid ON sources_inbox(is_valid);
CREATE INDEX idx_inbox_enriched ON sources_inbox(enriched_at);
```

### Silver : `sources_staging`

```sql
CREATE TABLE sources_staging (
    id TEXT PRIMARY KEY,           -- ULID
    url TEXT NOT NULL UNIQUE,      -- Dédupliqué
    domain TEXT NOT NULL,

    -- Enrichissement métadonnées
    title TEXT,                    -- Extrait de la page
    description TEXT,              -- Meta description

    -- Classification contenu (nouveau)
    content_type TEXT,             -- 'documentation', 'blog', 'forum', 'repository', 'api', 'other'
    language TEXT,                 -- 'en', 'fr', etc.

    -- Vérification accessibilité
    last_verified TIMESTAMP,
    is_accessible BOOLEAN DEFAULT TRUE,
    http_status INTEGER,           -- Dernier code HTTP

    -- Score de promotion
    citation_count INTEGER DEFAULT 1,
    project_count INTEGER DEFAULT 1,
    projects_list TEXT,            -- JSON array des projets uniques
    first_seen TIMESTAMP,
    last_seen TIMESTAMP,
    promotion_score REAL DEFAULT 0.0,

    -- Tracking
    inbox_ids TEXT,                -- JSON array des IDs bronze fusionnés
    enriched_at TIMESTAMP,
    promoted_at TIMESTAMP,         -- NULL si pas encore promu
    promoted_to TEXT               -- ID de la source Gold si promu
);

CREATE INDEX idx_staging_domain ON sources_staging(domain);
CREATE INDEX idx_staging_score ON sources_staging(promotion_score);
CREATE INDEX idx_staging_promoted ON sources_staging(promoted_at);
CREATE INDEX idx_staging_content_type ON sources_staging(content_type);
```

### Gold : `sources` (existante)

Table inchangée. Les sources promues y sont ajoutées avec :
- `is_promoted = TRUE`
- `promoted_at = timestamp`
- Lien vers `sources_staging.id` pour traçabilité

### Tracking : `connector_imports`

```sql
CREATE TABLE connector_imports (
    connector TEXT PRIMARY KEY,    -- 'claude_cli', 'cursor'
    last_import TIMESTAMP,         -- Dernier import réussi
    last_file_marker TEXT,         -- Pour import incrémental (CDC)
    entries_imported INTEGER DEFAULT 0,
    errors_count INTEGER DEFAULT 0
);
```

---

## Connecteurs d'Import

### Structure Plugin

```
rekall/connectors/
├── __init__.py          # Registry + discover()
├── base.py              # Classe abstraite BaseConnector
├── claude_cli.py        # Connecteur Claude Code (JSONL)
└── cursor.py            # Connecteur Cursor (SQLite)
```

### Interface BaseConnector

```python
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Iterator
from dataclasses import dataclass
from datetime import datetime

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
    is_valid: bool = True
    validation_error: str | None = None

class BaseConnector(ABC):
    """Base pour tous les connecteurs d'import."""

    name: str              # 'claude_cli', 'cursor'
    description: str

    @abstractmethod
    def is_available(self) -> bool:
        """Vérifie si le CLI/IDE est installé."""

    @abstractmethod
    def get_history_paths(self) -> list[Path]:
        """Retourne les chemins des fichiers/DB d'historique."""

    @abstractmethod
    def extract_urls(
        self,
        path: Path,
        since: datetime | None = None
    ) -> Iterator[InboxEntry]:
        """Extrait les URLs d'un fichier d'historique.

        Args:
            path: Chemin du fichier/DB
            since: Ne retourner que les entrées après cette date (CDC)
        """

    def validate_url(self, url: str) -> tuple[bool, str | None]:
        """Valide une URL avant insertion.

        Returns:
            (is_valid, error_message)
        """
        if not url or not url.startswith(('http://', 'https://')):
            return False, "Invalid URL scheme"
        # Filtrer les URLs internes/inutiles
        skip_patterns = [
            'localhost', '127.0.0.1',
            'file://', 'chrome://', 'about:',
            'rekall://'  # Nos propres URLs internes
        ]
        for pattern in skip_patterns:
            if pattern in url:
                return False, f"Skipped pattern: {pattern}"
        return True, None
```

### Connecteur Claude CLI

```python
import json
from pathlib import Path
from datetime import datetime
from .base import BaseConnector, InboxEntry

class ClaudeCLIConnector(BaseConnector):
    name = "claude_cli"
    description = "Import depuis Claude Code CLI (~/.claude/projects/)"

    def is_available(self) -> bool:
        return (Path.home() / ".claude" / "projects").exists()

    def get_history_paths(self) -> list[Path]:
        base = Path.home() / ".claude" / "projects"
        # Retourne tous les fichiers JSONL, triés par date modif
        return sorted(
            base.glob("*/*.jsonl"),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )

    def extract_urls(self, path: Path, since: datetime | None = None) -> Iterator[InboxEntry]:
        project = self._extract_project_name(path)
        conversation_id = path.stem

        with open(path) as f:
            current_user_query = None

            for line in f:
                try:
                    entry = json.loads(line.strip())
                except json.JSONDecodeError:
                    continue

                # Track user messages pour contexte
                if entry.get("type") == "user":
                    msg = entry.get("message", {})
                    content = msg.get("content", "")
                    if isinstance(content, str):
                        current_user_query = content[:500]

                # Chercher les tool_use WebFetch
                if entry.get("type") == "assistant":
                    msg = entry.get("message", {})
                    content = msg.get("content", [])

                    if isinstance(content, list):
                        for block in content:
                            if block.get("type") == "tool_use":
                                if block.get("name") == "WebFetch":
                                    url = block.get("input", {}).get("url")
                                    if url:
                                        is_valid, error = self.validate_url(url)

                                        # Extraire timestamp
                                        ts = entry.get("timestamp", 0)
                                        if ts > 1e12:  # Millisecondes
                                            ts = ts / 1000
                                        captured_at = datetime.fromtimestamp(ts) if ts else datetime.now()

                                        # Filtrer par date si spécifié
                                        if since and captured_at < since:
                                            continue

                                        yield InboxEntry(
                                            url=url,
                                            cli_source=self.name,
                                            project=project,
                                            conversation_id=conversation_id,
                                            user_query=current_user_query,
                                            assistant_snippet=self._extract_assistant_text(content),
                                            surrounding_text=None,
                                            captured_at=captured_at,
                                            raw_json=json.dumps(entry),
                                            is_valid=is_valid,
                                            validation_error=error,
                                        )

    def _extract_project_name(self, path: Path) -> str:
        """Extrait le nom du projet depuis le chemin."""
        # ~/.claude/projects/-Users-moi-Projects-foo/session.jsonl
        # -> /Users/moi/Projects/foo
        parent = path.parent.name
        return parent.replace("-", "/").lstrip("/")

    def _extract_assistant_text(self, content: list, max_len: int = 500) -> str | None:
        """Extrait le texte de la réponse assistant."""
        for block in content:
            if block.get("type") == "text":
                text = block.get("text", "")
                return text[:max_len] if text else None
        return None
```

### Connecteur Cursor

```python
import sqlite3
import json
from pathlib import Path
from datetime import datetime
from .base import BaseConnector, InboxEntry

class CursorConnector(BaseConnector):
    name = "cursor"
    description = "Import depuis Cursor IDE (SQLite workspaceStorage)"

    def is_available(self) -> bool:
        base = Path.home() / "Library" / "Application Support" / "Cursor" / "User" / "workspaceStorage"
        return base.exists()

    def get_history_paths(self) -> list[Path]:
        base = Path.home() / "Library" / "Application Support" / "Cursor" / "User" / "workspaceStorage"
        # Retourne tous les state.vscdb
        return list(base.glob("*/state.vscdb"))

    def extract_urls(self, path: Path, since: datetime | None = None) -> Iterator[InboxEntry]:
        workspace_hash = path.parent.name

        try:
            conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
            cursor = conn.cursor()

            # Récupérer les données de chat
            cursor.execute("""
                SELECT [key], value FROM ItemTable
                WHERE [key] IN ('aiService.prompts', 'workbench.panel.aichat.view.aichat.chatdata')
            """)

            for key, value in cursor.fetchall():
                try:
                    data = json.loads(value)
                    yield from self._extract_from_chat_data(data, workspace_hash, since)
                except json.JSONDecodeError:
                    continue

            conn.close()
        except sqlite3.Error as e:
            # Log error but don't crash
            pass

    def _extract_from_chat_data(
        self,
        data: dict | list,
        workspace: str,
        since: datetime | None
    ) -> Iterator[InboxEntry]:
        """Parse la structure de données Cursor pour extraire les URLs."""
        # La structure exacte dépend de la version de Cursor
        # Implémentation à affiner selon le format réel

        messages = []
        if isinstance(data, list):
            messages = data
        elif isinstance(data, dict):
            messages = data.get("messages", []) or data.get("chats", [])

        current_user_query = None

        for msg in messages:
            role = msg.get("role", "")
            content = msg.get("content", "") or msg.get("text", "")

            if role == "user":
                current_user_query = content[:500] if isinstance(content, str) else None

            # Chercher les URLs dans le contenu
            if isinstance(content, str):
                urls = self._extract_urls_from_text(content)
                for url in urls:
                    is_valid, error = self.validate_url(url)

                    yield InboxEntry(
                        url=url,
                        cli_source=self.name,
                        project=f"cursor:{workspace}",
                        conversation_id=workspace,
                        user_query=current_user_query,
                        assistant_snippet=content[:500] if role == "assistant" else None,
                        surrounding_text=None,
                        captured_at=datetime.now(),  # Cursor ne stocke pas toujours les timestamps
                        is_valid=is_valid,
                        validation_error=error,
                    )

    def _extract_urls_from_text(self, text: str) -> list[str]:
        """Extrait les URLs d'un texte."""
        import re
        url_pattern = r'https?://[^\s<>"\')\]]+[^\s<>"\')\].,;!?]'
        return list(set(re.findall(url_pattern, text)))
```

---

## Enrichissement & Promotion

### Enrichissement Background (Bronze → Silver)

```python
import httpx
from bs4 import BeautifulSoup

def enrich_inbox_entries(db, batch_size: int = 50):
    """Job d'enrichissement des entrées Bronze vers Silver."""

    pending = db.get_inbox_not_enriched(limit=batch_size)

    for entry in pending:
        if not entry.is_valid:
            # Skip invalid entries, just mark as processed
            db.mark_inbox_enriched(entry.id)
            continue

        domain = extract_domain(entry.url)
        existing = db.get_staging_by_url(entry.url)

        if existing:
            # Fusionner : incrémenter compteurs
            _merge_into_staging(db, existing, entry)
        else:
            # Créer nouvelle entrée Silver
            _create_staging_entry(db, entry, domain)

        db.mark_inbox_enriched(entry.id)


def _merge_into_staging(db, existing: StagingEntry, entry: InboxEntry):
    """Fusionne une entrée Bronze dans une Silver existante."""
    existing.citation_count += 1

    # Tracker les projets uniques
    projects = json.loads(existing.projects_list or "[]")
    if entry.project and entry.project not in projects:
        projects.append(entry.project)
        existing.project_count = len(projects)
    existing.projects_list = json.dumps(projects)

    existing.last_seen = datetime.now()

    # Append inbox ID
    inbox_ids = json.loads(existing.inbox_ids or "[]")
    inbox_ids.append(entry.id)
    existing.inbox_ids = json.dumps(inbox_ids)

    # Recalculer score
    existing.promotion_score = calculate_promotion_score(existing)
    db.update_staging(existing)


def _create_staging_entry(db, entry: InboxEntry, domain: str):
    """Crée une nouvelle entrée Silver."""
    # Fetch métadonnées
    title, description, content_type, language = fetch_page_metadata(entry.url)

    staging = StagingEntry(
        url=entry.url,
        domain=domain,
        title=title,
        description=description,
        content_type=content_type,
        language=language,
        citation_count=1,
        project_count=1,
        projects_list=json.dumps([entry.project] if entry.project else []),
        first_seen=entry.captured_at,
        last_seen=datetime.now(),
        inbox_ids=json.dumps([entry.id]),
        enriched_at=datetime.now(),
    )
    staging.promotion_score = calculate_promotion_score(staging)
    db.add_staging(staging)


def fetch_page_metadata(url: str, timeout: float = 5.0) -> tuple[str, str, str, str]:
    """Fetch et parse les métadonnées d'une page.

    Returns:
        (title, description, content_type, language)
    """
    try:
        resp = httpx.get(url, timeout=timeout, follow_redirects=True)
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, 'html.parser')

        # Title
        title = None
        if soup.title:
            title = soup.title.string
        if not title:
            og_title = soup.find("meta", property="og:title")
            title = og_title["content"] if og_title else None

        # Description
        description = None
        meta_desc = soup.find("meta", attrs={"name": "description"})
        if meta_desc:
            description = meta_desc.get("content")
        if not description:
            og_desc = soup.find("meta", property="og:description")
            description = og_desc["content"] if og_desc else None

        # Content type classification
        content_type = classify_content_type(url, soup)

        # Language
        language = detect_language(soup)

        return (
            title[:200] if title else None,
            description[:500] if description else None,
            content_type,
            language,
        )
    except Exception:
        return None, None, "other", None


def classify_content_type(url: str, soup: BeautifulSoup) -> str:
    """Classifie le type de contenu."""
    url_lower = url.lower()

    # Par domaine/pattern d'URL
    if "github.com" in url_lower or "gitlab.com" in url_lower:
        return "repository"
    if "/docs/" in url_lower or "documentation" in url_lower or ".readthedocs." in url_lower:
        return "documentation"
    if "/api/" in url_lower or "swagger" in url_lower or "openapi" in url_lower:
        return "api"
    if "stackoverflow.com" in url_lower or "stackexchange.com" in url_lower:
        return "forum"
    if "/blog/" in url_lower or "medium.com" in url_lower or "dev.to" in url_lower:
        return "blog"
    if "arxiv.org" in url_lower or "paper" in url_lower:
        return "paper"

    return "other"


def detect_language(soup: BeautifulSoup) -> str | None:
    """Détecte la langue de la page."""
    html_tag = soup.find("html")
    if html_tag and html_tag.get("lang"):
        lang = html_tag["lang"]
        return lang[:2].lower()  # "en-US" -> "en"
    return None
```

### Score de Promotion (Configurable + Decay)

```python
from datetime import datetime, timedelta

# Config par défaut
DEFAULT_PROMOTION_CONFIG = {
    "weights": {
        "citation": 1.0,      # × nombre de citations
        "project": 2.0,       # × nombre de projets distincts
        "recency": 0.5,       # × boost récence (0-1)
    },
    "threshold": 5.0,
    "decay_days": 30,         # Jours avant decay complet
}

def calculate_promotion_score(staging: StagingEntry) -> float:
    """Calcule le score de promotion avec decay temporel."""
    config = get_config().promotion_config or DEFAULT_PROMOTION_CONFIG
    weights = config["weights"]
    decay_days = config.get("decay_days", 30)

    # Calcul récence avec decay
    days_since = (datetime.now() - staging.last_seen).days
    recency_factor = max(0, 1.0 - (days_since / decay_days))

    base_score = (
        staging.citation_count * weights["citation"] +
        staging.project_count * weights["project"]
    )

    # Apply recency boost (pas pénalité, boost)
    final_score = base_score + (recency_factor * weights["recency"])

    return round(final_score, 2)


def get_promotion_indicator(score: float, threshold: float) -> str:
    """Retourne un indicateur visuel pour le TUI."""
    if score >= threshold:
        return "⬆"  # Éligible promotion
    elif score >= threshold * 0.8:
        return "→"  # Proche du seuil
    else:
        return " "  # En dessous
```

### Promotion Silver → Gold

```python
def check_auto_promotion(db):
    """Vérifie et promeut les sources éligibles."""
    config = get_config().promotion_config or DEFAULT_PROMOTION_CONFIG
    threshold = config["threshold"]

    candidates = db.get_staging_above_threshold(threshold)

    promoted = []
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

        promoted.append(staging)
        logger.info(f"Auto-promoted: {staging.url} (score={staging.promotion_score})")

    return promoted


def promote_manually(db, staging_id: str) -> Source | None:
    """Promotion manuelle d'une source Silver."""
    staging = db.get_staging(staging_id)
    if not staging or staging.promoted_at:
        return None

    gold_source = Source(
        domain=staging.domain,
        url_pattern=staging.url,
        personal_score=50.0,
        is_promoted=True,
        promoted_at=datetime.now(),
    )
    source_id = db.add_source(gold_source)
    db.mark_staging_promoted(staging.id, source_id)

    return gold_source


def demote_source(db, source_id: str) -> bool:
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
rekall sources inbox quarantine          # Voir entrées invalides
rekall sources inbox clear               # Vider inbox (après enrichissement)

# === STAGING (Silver) ===
rekall sources staging                   # TUI: voir staging avec scores
rekall sources staging enrich            # Forcer enrichissement maintenant
rekall sources staging promote URL       # Promotion manuelle → Gold
rekall sources staging promote --auto    # Promouvoir tous les éligibles
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
├── 📥 Inbox (Bronze)              # NOUVEAU
├── 📊 Staging (Silver)            # NOUVEAU
├── 🔄 Import historique           # NOUVEAU
└── ──────────────────
    Mes vues                       # Existant
```

### TUI Inbox (Bronze)

```
┌─ 📥 Sources Inbox (23 nouvelles, 2 invalides) ──────────────────┐
│                                                                  │
│  URL                          CLI      Projet        Capturé    │
│  ───────────────────────────────────────────────────────────────│
│  docs.python.org/3/lib...     claude   rekall        il y a 2h  │
│  github.com/anthropics/...    claude   rekall        il y a 3h  │
│  stackoverflow.com/q/123...   cursor   bigmind       hier       │
│  ⚠️ localhost:3000/api...      claude   test          il y a 1h  │
│                                                                  │
│  [i] Import  [e] Enrichir  [q] Quarantine  [d] Drop  [Esc] Back │
└──────────────────────────────────────────────────────────────────┘
```

### TUI Staging (Silver)

```
┌─ 📊 Sources Staging (12 enrichies, 3 éligibles) ─────────────────┐
│                                                                   │
│  Domaine              Titre           Type  Citations Proj Score │
│  ────────────────────────────────────────────────────────────────│
│  docs.python.org      Python Docs     doc       5      3   8.5 ⬆ │
│  github.com           Anthropic SDK   repo      3      2   5.0 → │
│  stackoverflow.com    SQLite UPSERT   forum     2      1   2.5   │
│                                                                   │
│  [p] Promouvoir  [a] Auto-promote  [d] Drop  [r] Refresh  [Esc]  │
└───────────────────────────────────────────────────────────────────┘

# Indicateurs: ⬆ = éligible (≥ seuil), → = proche (≥ 80%)
# Types: doc, repo, forum, blog, api, paper, other
```

### Action Dépromouvoir (Gold)

Ajout binding `[x] Dépromouvoir` dans `SourcesBrowseApp` :
1. Confirmation avec warning
2. Source Gold → supprimée
3. Source Silver → `promoted_at = NULL`
4. Refresh de la liste

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
    is_valid BOOLEAN DEFAULT TRUE,
    validation_error TEXT,
    enriched_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_inbox_url ON sources_inbox(url);
CREATE INDEX IF NOT EXISTS idx_inbox_cli ON sources_inbox(cli_source);
CREATE INDEX IF NOT EXISTS idx_inbox_captured ON sources_inbox(captured_at);
CREATE INDEX IF NOT EXISTS idx_inbox_valid ON sources_inbox(is_valid);
CREATE INDEX IF NOT EXISTS idx_inbox_enriched ON sources_inbox(enriched_at);

-- Silver: Sources staging
CREATE TABLE IF NOT EXISTS sources_staging (
    id TEXT PRIMARY KEY,
    url TEXT NOT NULL UNIQUE,
    domain TEXT NOT NULL,
    title TEXT,
    description TEXT,
    content_type TEXT,
    language TEXT,
    last_verified TIMESTAMP,
    is_accessible BOOLEAN DEFAULT TRUE,
    http_status INTEGER,
    citation_count INTEGER DEFAULT 1,
    project_count INTEGER DEFAULT 1,
    projects_list TEXT,
    first_seen TIMESTAMP,
    last_seen TIMESTAMP,
    promotion_score REAL DEFAULT 0.0,
    inbox_ids TEXT,
    enriched_at TIMESTAMP,
    promoted_at TIMESTAMP,
    promoted_to TEXT
);

CREATE INDEX IF NOT EXISTS idx_staging_domain ON sources_staging(domain);
CREATE INDEX IF NOT EXISTS idx_staging_score ON sources_staging(promotion_score);
CREATE INDEX IF NOT EXISTS idx_staging_promoted ON sources_staging(promoted_at);
CREATE INDEX IF NOT EXISTS idx_staging_content_type ON sources_staging(content_type);

-- Tracking des imports par connecteur
CREATE TABLE IF NOT EXISTS connector_imports (
    connector TEXT PRIMARY KEY,
    last_import TIMESTAMP,
    last_file_marker TEXT,
    entries_imported INTEGER DEFAULT 0,
    errors_count INTEGER DEFAULT 0
);
"""
```

---

## Fichiers à Créer/Modifier

| Fichier | Action | Description |
|---------|--------|-------------|
| `rekall/connectors/__init__.py` | Créer | Registry connecteurs |
| `rekall/connectors/base.py` | Créer | Classe abstraite + validation |
| `rekall/connectors/claude_cli.py` | Créer | Connecteur Claude (JSONL) |
| `rekall/connectors/cursor.py` | Créer | Connecteur Cursor (SQLite) |
| `rekall/db.py` | Modifier | Migration v11 + CRUD inbox/staging |
| `rekall/tui.py` | Modifier | TUI Inbox + Staging + dépromouvoir |
| `rekall/cli.py` | Modifier | Commandes inbox/staging |
| `rekall/mcp_server.py` | Modifier | Tool capture_url |
| `rekall/config.py` | Modifier | Config promotion |
| `rekall/i18n.py` | Modifier | Traductions |
| `rekall/enrichment.py` | Créer | Jobs d'enrichissement |

---

## Phases d'Implémentation

### Phase 1: Foundation
- Migration v11 (tables Bronze + Silver + tracking)
- Fonctions DB CRUD
- Traductions

### Phase 2: Connecteurs
- Architecture plugin base
- Connecteur Claude CLI
- Connecteur Cursor

### Phase 3: Enrichissement
- Job d'enrichissement Bronze → Silver
- Fetch métadonnées (titre, description)
- Classification contenu

### Phase 4: Promotion
- Calcul score avec decay
- Promotion automatique sur seuil
- Promotion/dépromouvoir manuel

### Phase 5: Interface
- TUI Inbox (Bronze)
- TUI Staging (Silver)
- Extension menu sources
- Commandes CLI

### Phase 6: MCP + Polish
- Extension MCP capture_url
- Tests unitaires
- Documentation

---

## Sources de Recherche

### Medallion Architecture
- [Databricks - Medallion Architecture](https://www.databricks.com/glossary/medallion-architecture)
- [Azure Databricks Guide](https://learn.microsoft.com/en-us/azure/databricks/lakehouse/medallion)
- [Piethein Strengholt - Best Practices](https://piethein.medium.com/medallion-architecture-best-practices-for-managing-bronze-silver-and-gold-486de7c90055)

### Claude CLI History
- [claude-conversation-extractor](https://github.com/ZeroSumQuant/claude-conversation-extractor)
- [claude-history](https://github.com/thejud/claude-history)
- [Kent Gigger - Hidden Conversation History](https://kentgigger.com/posts/claude-code-conversation-history)

### Cursor History
- [Cursor Forum - Chat History](https://forum.cursor.com/t/chat-history-folder/7653)
- [cursor-chat-export](https://github.com/somogyijanos/cursor-chat-export)

### Scoring & Recommendation
- [Google ML - Recommendation Scoring](https://developers.google.com/machine-learning/recommendation/dnn/scoring)
- [Evidently AI - Ranking Metrics](https://www.evidentlyai.com/ranking-metrics/evaluating-recommender-systems)

### Data Enrichment
- [Firecrawl - Data Enrichment Guide](https://www.firecrawl.dev/blog/complete-guide-to-data-enrichment)
- [Haystack - Metadata Extraction](https://haystack.deepset.ai/blog/extracting-metadata-filter)
