# Quickstart: Sources Medallion Architecture

**Feature**: 013-sources-medallion
**Date**: 2025-12-11

Guide de démarrage rapide pour les développeurs implémentant cette feature.

---

## Prérequis

### Environnement
- Python 3.9+ installé
- Repo rekall cloné et installable (`pip install -e .`)
- Base de données rekall initialisée (`rekall version`)

### Nouvelles dépendances à ajouter
```bash
# Dans pyproject.toml, section [project.dependencies]
pip install httpx beautifulsoup4
```

---

## Architecture en 5 Minutes

```
BRONZE (inbox)          SILVER (staging)        GOLD (sources)
─────────────────       ─────────────────       ──────────────
│ URL brute      │      │ URL unique     │      │ Source curée│
│ + contexte CLI │  ──► │ + métadonnées  │  ──► │ + score     │
│ + quarantine   │      │ + score promo  │      │ + decay     │
─────────────────       ─────────────────       ──────────────
     import()              enrich()              promote()
```

**Flux de données**:
1. **Import** : CLI history → Bronze (N URLs par conversation)
2. **Enrich** : Bronze → Silver (dédup, fetch métadonnées)
3. **Promote** : Silver → Gold (si score ≥ seuil)

---

## Structure des Fichiers à Créer

```
rekall/
├── connectors/              # NOUVEAU
│   ├── __init__.py          # Registry: get_connector(), list_connectors()
│   ├── base.py              # BaseConnector ABC
│   ├── claude_cli.py        # ClaudeCLIConnector
│   └── cursor.py            # CursorConnector
├── enrichment.py            # NOUVEAU: enrich_inbox_entries()
├── promotion.py             # NOUVEAU: calculate_score(), promote()
├── db.py                    # MODIFIER: +Migration v11, +CRUD inbox/staging
├── models.py                # MODIFIER: +InboxEntry, +StagingEntry
├── cli.py                   # MODIFIER: +commandes sources inbox/staging
├── tui.py                   # MODIFIER: +TUI inbox/staging
└── i18n.py                  # MODIFIER: +traductions
```

---

## Étape 1: Modèles de Données

### Fichier: `rekall/models.py`

```python
# Ajouter après les imports existants

@dataclass
class InboxEntry:
    """URL capturée depuis un CLI IA (Bronze layer)."""

    id: str
    url: str
    domain: str | None = None
    cli_source: str = ""
    project: str | None = None
    conversation_id: str | None = None
    user_query: str | None = None
    assistant_snippet: str | None = None
    captured_at: datetime = field(default_factory=datetime.now)
    import_source: str = "history_import"
    raw_json: str | None = None
    is_valid: bool = True
    validation_error: str | None = None
    enriched_at: datetime | None = None


@dataclass
class StagingEntry:
    """URL enrichie avec métadonnées (Silver layer)."""

    id: str
    url: str
    domain: str
    title: str | None = None
    description: str | None = None
    content_type: str | None = None  # 'documentation', 'repository', etc.
    language: str | None = None
    is_accessible: bool = True
    http_status: int | None = None
    citation_count: int = 1
    project_count: int = 1
    projects_list: str | None = None  # JSON array
    first_seen: datetime | None = None
    last_seen: datetime | None = None
    promotion_score: float = 0.0
    inbox_ids: str | None = None  # JSON array
    enriched_at: datetime | None = None
    promoted_at: datetime | None = None
    promoted_to: str | None = None
```

---

## Étape 2: Migration Database

### Fichier: `rekall/db.py`

```python
# Incrémenter la version
CURRENT_SCHEMA_VERSION = 11

# Ajouter la migration
MIGRATIONS[11] = [
    # Bronze: sources_inbox
    """CREATE TABLE IF NOT EXISTS sources_inbox (
        id TEXT PRIMARY KEY,
        url TEXT NOT NULL,
        domain TEXT,
        cli_source TEXT NOT NULL,
        project TEXT,
        conversation_id TEXT,
        user_query TEXT,
        assistant_snippet TEXT,
        captured_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        import_source TEXT,
        raw_json TEXT,
        is_valid BOOLEAN DEFAULT TRUE,
        validation_error TEXT,
        enriched_at TIMESTAMP
    )""",
    "CREATE INDEX IF NOT EXISTS idx_inbox_url ON sources_inbox(url)",
    "CREATE INDEX IF NOT EXISTS idx_inbox_cli ON sources_inbox(cli_source)",
    "CREATE INDEX IF NOT EXISTS idx_inbox_valid ON sources_inbox(is_valid)",
    "CREATE INDEX IF NOT EXISTS idx_inbox_enriched ON sources_inbox(enriched_at)",

    # Silver: sources_staging
    """CREATE TABLE IF NOT EXISTS sources_staging (
        id TEXT PRIMARY KEY,
        url TEXT NOT NULL UNIQUE,
        domain TEXT NOT NULL,
        title TEXT,
        description TEXT,
        content_type TEXT,
        language TEXT,
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
    )""",
    "CREATE INDEX IF NOT EXISTS idx_staging_url ON sources_staging(url)",
    "CREATE INDEX IF NOT EXISTS idx_staging_score ON sources_staging(promotion_score DESC)",

    # CDC Tracking
    """CREATE TABLE IF NOT EXISTS connector_imports (
        connector TEXT PRIMARY KEY,
        last_import TIMESTAMP,
        last_file_marker TEXT,
        entries_imported INTEGER DEFAULT 0,
        errors_count INTEGER DEFAULT 0
    )""",
]
```

---

## Étape 3: Connecteur de Base

### Fichier: `rekall/connectors/base.py`

```python
"""Base class for CLI history connectors."""

from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Iterator

from rekall.models import InboxEntry


class BaseConnector(ABC):
    """Interface pour tous les connecteurs d'import."""

    name: str
    description: str

    @abstractmethod
    def is_available(self) -> bool:
        """Vérifie si le CLI est installé/accessible."""
        pass

    @abstractmethod
    def get_history_paths(self) -> list[Path]:
        """Retourne les chemins des fichiers d'historique."""
        pass

    @abstractmethod
    def extract_urls(
        self,
        path: Path,
        since: datetime | None = None
    ) -> Iterator[InboxEntry]:
        """Extrait les URLs d'un fichier d'historique."""
        pass

    def validate_url(self, url: str) -> tuple[bool, str | None]:
        """Valide une URL (méthode par défaut)."""
        if not url or not url.startswith(('http://', 'https://')):
            return False, "Invalid URL scheme"

        skip_patterns = ['localhost', '127.0.0.1', 'file://', '192.168.']
        for pattern in skip_patterns:
            if pattern in url.lower():
                return False, f"Skipped: {pattern}"

        return True, None
```

---

## Étape 4: Connecteur Claude CLI

### Fichier: `rekall/connectors/claude_cli.py`

```python
"""Connecteur pour Claude Code CLI history."""

import json
from datetime import datetime
from pathlib import Path
from typing import Iterator

from rekall.models import InboxEntry, generate_ulid
from .base import BaseConnector


class ClaudeCLIConnector(BaseConnector):
    name = "claude_cli"
    description = "Import depuis Claude Code CLI (~/.claude/projects/)"

    def is_available(self) -> bool:
        return (Path.home() / ".claude" / "projects").exists()

    def get_history_paths(self) -> list[Path]:
        base = Path.home() / ".claude" / "projects"
        return sorted(base.glob("*/*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True)

    def extract_urls(self, path: Path, since: datetime | None = None) -> Iterator[InboxEntry]:
        project = self._extract_project_name(path)
        conversation_id = path.stem
        current_user_query = None

        with open(path) as f:
            for line in f:
                try:
                    entry = json.loads(line.strip())
                except json.JSONDecodeError:
                    continue

                # Track user messages
                if entry.get("type") == "user":
                    msg = entry.get("message", {})
                    content = msg.get("content", "")
                    if isinstance(content, str):
                        current_user_query = content[:500]

                # Find WebFetch tool_use
                if entry.get("type") == "assistant":
                    content = entry.get("message", {}).get("content", [])
                    if isinstance(content, list):
                        for block in content:
                            if block.get("type") == "tool_use" and block.get("name") == "WebFetch":
                                url = block.get("input", {}).get("url")
                                if url:
                                    is_valid, error = self.validate_url(url)
                                    ts = entry.get("timestamp", 0)
                                    if ts > 1e12:
                                        ts = ts / 1000
                                    captured_at = datetime.fromtimestamp(ts) if ts else datetime.now()

                                    if since and captured_at < since:
                                        continue

                                    yield InboxEntry(
                                        id=generate_ulid(),
                                        url=url,
                                        domain=self._extract_domain(url),
                                        cli_source=self.name,
                                        project=project,
                                        conversation_id=conversation_id,
                                        user_query=current_user_query,
                                        captured_at=captured_at,
                                        is_valid=is_valid,
                                        validation_error=error,
                                    )

    def _extract_project_name(self, path: Path) -> str:
        return path.parent.name.replace("-", "/").lstrip("/")

    def _extract_domain(self, url: str) -> str | None:
        from urllib.parse import urlparse
        try:
            return urlparse(url).netloc
        except Exception:
            return None
```

---

## Étape 5: Enrichissement

### Fichier: `rekall/enrichment.py`

```python
"""Bronze → Silver enrichment jobs."""

import json
from datetime import datetime
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup

from rekall.models import StagingEntry, generate_ulid


def enrich_inbox_entries(db, batch_size: int = 50, timeout: float = 5.0):
    """Job d'enrichissement Bronze → Silver."""

    pending = db.get_inbox_not_enriched(limit=batch_size)
    results = {"enriched": 0, "merged": 0, "failed": 0}

    for entry in pending:
        if not entry.is_valid:
            db.mark_inbox_enriched(entry.id)
            continue

        existing = db.get_staging_by_url(entry.url)

        if existing:
            # Merge into existing
            _merge_into_staging(db, existing, entry)
            results["merged"] += 1
        else:
            # Create new staging entry
            _create_staging_entry(db, entry, timeout)
            results["enriched"] += 1

        db.mark_inbox_enriched(entry.id)

    return results


def _merge_into_staging(db, existing: StagingEntry, entry):
    """Fusionne une entrée Bronze dans une Silver existante."""
    existing.citation_count += 1

    projects = json.loads(existing.projects_list or "[]")
    if entry.project and entry.project not in projects:
        projects.append(entry.project)
        existing.project_count = len(projects)
    existing.projects_list = json.dumps(projects)

    existing.last_seen = datetime.now()

    inbox_ids = json.loads(existing.inbox_ids or "[]")
    inbox_ids.append(entry.id)
    existing.inbox_ids = json.dumps(inbox_ids)

    existing.promotion_score = calculate_promotion_score(existing)
    db.update_staging(existing)


def _create_staging_entry(db, entry, timeout: float):
    """Crée une nouvelle entrée Silver avec fetch métadonnées."""
    domain = urlparse(entry.url).netloc
    title, description, content_type, language = fetch_metadata(entry.url, timeout)

    staging = StagingEntry(
        id=generate_ulid(),
        url=entry.url,
        domain=domain,
        title=title,
        description=description,
        content_type=content_type,
        language=language,
        first_seen=entry.captured_at,
        last_seen=datetime.now(),
        inbox_ids=json.dumps([entry.id]),
        enriched_at=datetime.now(),
    )
    staging.promotion_score = calculate_promotion_score(staging)
    db.add_staging(staging)


def fetch_metadata(url: str, timeout: float = 5.0):
    """Fetch et parse les métadonnées d'une page."""
    try:
        resp = httpx.get(url, timeout=timeout, follow_redirects=True)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'html.parser')

        title = soup.title.string if soup.title else None
        if not title:
            og = soup.find("meta", property="og:title")
            title = og["content"] if og else None

        description = None
        meta = soup.find("meta", attrs={"name": "description"})
        if meta:
            description = meta.get("content")

        content_type = classify_content_type(url)
        language = soup.find("html").get("lang", "")[:2] if soup.find("html") else None

        return title[:200] if title else None, description[:500] if description else None, content_type, language

    except Exception:
        return None, None, "other", None


def classify_content_type(url: str) -> str:
    """Classifie le type de contenu par heuristique."""
    url_lower = url.lower()
    if "github.com" in url_lower or "gitlab.com" in url_lower:
        return "repository"
    if "/docs/" in url_lower or "documentation" in url_lower:
        return "documentation"
    if "stackoverflow.com" in url_lower:
        return "forum"
    if "/blog/" in url_lower or "medium.com" in url_lower:
        return "blog"
    return "other"


def calculate_promotion_score(staging: StagingEntry, config=None) -> float:
    """Calcule le score de promotion."""
    config = config or {"citation": 1.0, "project": 2.0, "recency": 0.5, "decay_days": 30}

    days_since = (datetime.now() - (staging.last_seen or datetime.now())).days
    recency = max(0, 1.0 - days_since / config["decay_days"])

    return round(
        staging.citation_count * config["citation"] +
        staging.project_count * config["project"] +
        recency * config["recency"],
        2
    )
```

---

## Vérification

### Test rapide après implémentation

```bash
# 1. Vérifier que la migration passe
rekall version
# → Schema Version: v11 (current)

# 2. Vérifier que le connecteur Claude est détecté
python -c "from rekall.connectors import get_connector; print(get_connector('claude_cli').is_available())"
# → True (si Claude CLI installé)

# 3. Test d'import
rekall sources inbox import --dry-run
# → Devrait lister les URLs sans les insérer

# 4. Import réel
rekall sources inbox import --cli claude
# → Import effectué

# 5. Vérifier l'inbox
rekall sources inbox stats
# → Statistiques affichées
```

---

## Checklist Développeur

- [ ] `models.py`: InboxEntry et StagingEntry ajoutés
- [ ] `db.py`: Migration v11 + CRUD inbox/staging
- [ ] `connectors/base.py`: BaseConnector ABC
- [ ] `connectors/claude_cli.py`: Connecteur fonctionnel
- [ ] `connectors/__init__.py`: Registry
- [ ] `enrichment.py`: Job d'enrichissement
- [ ] `promotion.py`: Calcul score + promotion
- [ ] `cli.py`: Commandes inbox/staging
- [ ] `tui.py`: TUI inbox/staging
- [ ] `i18n.py`: Traductions
- [ ] Tests unitaires passent
- [ ] Tests manuels TUI OK
