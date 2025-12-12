# Recherche Technique : Intégration Sources & Souvenirs

**Date** : 2025-12-11
**Phase** : 0 (Technical Research)
**Recherche UX/Business** : [docs/research-sources-souvenirs-integration.md](../../docs/research-sources-souvenirs-integration.md)

---

## Questions Techniques Résolues

### Q1 : Stratégie de migration schéma SQLite v7 → v8

**Décision** : Utiliser le pattern migrations séquentielles existant dans `db.py`

**Rationale** :
- Pattern éprouvé : 7 migrations déjà implémentées avec succès
- PRAGMA user_version pour tracking automatique
- Idempotence via gestion des erreurs "duplicate column"
- Vérification post-migration (EXPECTED_TABLES, EXPECTED_COLUMNS)

**Alternatives considérées** :
- Alembic : Trop lourd pour SQLite single-file
- Migration manuelle : Risque d'incohérence

**Migration v8** :
```python
MIGRATIONS[8] = [
    # Table sources
    """CREATE TABLE IF NOT EXISTS sources (
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
    )""",
    # Table entry_sources (liaison many-to-many)
    """CREATE TABLE IF NOT EXISTS entry_sources (
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
    )""",
    "CREATE INDEX IF NOT EXISTS idx_entry_sources_entry ON entry_sources(entry_id)",
    "CREATE INDEX IF NOT EXISTS idx_entry_sources_source ON entry_sources(source_id)",
    "CREATE INDEX IF NOT EXISTS idx_sources_domain ON sources(domain)",
    "CREATE INDEX IF NOT EXISTS idx_sources_score ON sources(personal_score DESC)",
]
```

---

### Q2 : Algorithme de calcul du score personnel

**Décision** : Score composite avec déclin exponentiel

**Rationale** :
- Inspiré du système Admiralty (fiabilité dynamique)
- Decay rates confirmés par recherche (fast=3mo, medium=6mo, slow=12mo)
- Formule simple mais représentative de l'usage réel

**Formule** :
```python
def calculate_source_score(
    usage_count: int,
    days_since_last_use: int,
    decay_rate: str,  # 'fast', 'medium', 'slow'
    reliability: str,  # 'A', 'B', 'C'
) -> float:
    """
    Score personnel 0-100 basé sur usage + fraîcheur.

    Composantes:
    - Base usage (0-60): sqrt(usage_count) × 10, cap 60
    - Recency bonus (0-30): 30 × decay_factor
    - Reliability bonus (0-10): A=10, B=5, C=0
    """
    # Demi-vies en jours
    HALF_LIVES = {'fast': 90, 'medium': 180, 'slow': 365}
    half_life = HALF_LIVES.get(decay_rate, 180)

    # Base usage score (sqrt pour diminishing returns)
    usage_score = min(60, math.sqrt(usage_count) * 10)

    # Recency avec déclin exponentiel
    decay_factor = 0.5 ** (days_since_last_use / half_life)
    recency_score = 30 * decay_factor

    # Reliability bonus
    reliability_bonus = {'A': 10, 'B': 5, 'C': 0}.get(reliability, 0)

    return min(100, usage_score + recency_score + reliability_bonus)
```

**Exemple** :
| Source | Usage | Days | Decay | Reliability | Score |
|--------|-------|------|-------|-------------|-------|
| pinecone.io | 25 | 30 | medium | A | ~78 |
| medium.com | 3 | 180 | fast | C | ~22 |
| arxiv.org | 10 | 90 | slow | B | ~54 |

---

### Q3 : Stratégie de vérification Link Rot

**Décision** : HTTP HEAD asynchrone avec urllib (pas de dépendance externe)

**Rationale** :
- Pas de nouvelle dépendance (requests, httpx)
- HEAD au lieu de GET : économie de bande passante
- Timeout court (10s) pour éviter blocage
- Vérification quotidienne (FR-021)

**Implémentation** :
```python
import urllib.request
from urllib.error import URLError, HTTPError

def check_url_accessibility(url: str, timeout: int = 10) -> tuple[bool, str]:
    """
    Vérifie si une URL est accessible via HTTP HEAD.

    Returns:
        (is_accessible, status_message)
    """
    try:
        req = urllib.request.Request(url, method='HEAD')
        req.add_header('User-Agent', 'Rekall/0.3 LinkChecker')
        with urllib.request.urlopen(req, timeout=timeout) as response:
            if response.status < 400:
                return (True, f"OK ({response.status})")
            return (False, f"HTTP {response.status}")
    except HTTPError as e:
        return (False, f"HTTP {e.code}")
    except URLError as e:
        return (False, f"Network error: {e.reason}")
    except Exception as e:
        return (False, f"Error: {str(e)}")
```

**Considérations** :
- Certains sites bloquent HEAD → fallback GET avec Range header
- Rate limiting implicite : max 10 vérifications/minute
- Stockage `last_verified` et `status` dans table `sources`

---

### Q4 : Pattern d'extraction de domaine depuis URL

**Décision** : urllib.parse avec normalisation

**Rationale** :
- Bibliothèque standard Python
- Gestion http/https, www/sans www
- Extraction du domaine principal

**Implémentation** :
```python
from urllib.parse import urlparse

def extract_domain(url: str) -> str:
    """
    Extrait le domaine normalisé d'une URL.

    Examples:
        'https://www.pinecone.io/learn/rag/' -> 'pinecone.io'
        'http://docs.python.org/3/' -> 'docs.python.org'
    """
    parsed = urlparse(url.lower())
    domain = parsed.netloc or parsed.path.split('/')[0]

    # Supprimer www. si présent
    if domain.startswith('www.'):
        domain = domain[4:]

    return domain

def normalize_url(url: str) -> str:
    """
    Normalise une URL pour éviter les doublons.

    - http:// → https://
    - www. supprimé
    - trailing slash supprimé
    """
    url = url.lower().strip()
    if url.startswith('http://'):
        url = 'https://' + url[7:]

    parsed = urlparse(url)
    domain = parsed.netloc
    if domain.startswith('www.'):
        domain = domain[4:]

    path = parsed.path.rstrip('/')
    return f"https://{domain}{path}"
```

---

### Q5 : Stratégie de tests

**Décision** : Tests unitaires + intégration DB avec fixtures pytest

**Rationale** :
- Pattern existant dans `tests/test_db.py`
- Fixtures pour base de données temporaire
- Tests d'intégration pour les flux complets

**Structure tests** :
```text
tests/
├── test_db.py           # Étendre avec:
│   ├── test_add_source
│   ├── test_get_sources_by_score
│   ├── test_link_entry_to_source
│   ├── test_backlinks_count
│   └── test_calculate_source_score
├── test_models.py       # Étendre avec:
│   ├── test_source_model
│   └── test_entry_source_model
└── test_link_rot.py     # Nouveau:
    ├── test_check_url_accessible
    ├── test_check_url_404
    └── test_extract_domain
```

**Fixtures clés** :
```python
@pytest.fixture
def db_with_sources(tmp_path):
    """DB temporaire avec sources et souvenirs pré-remplis."""
    db_path = tmp_path / "test.db"
    db = Database(db_path)
    db.init()

    # Ajouter sources de test
    db.add_source(Source(
        id=generate_ulid(),
        domain="pinecone.io",
        usage_count=10,
        personal_score=75.0,
        reliability='A',
    ))

    yield db
    db.close()
```

---

## Décisions d'Architecture

### Modèle de données

```
entries (existant)
    ├── 1:N → entry_sources (nouveau)
    │            └── N:1 → sources (nouveau, optionnel)
    └── 1:N → links (existant)
```

**Relation entry_sources → sources** :
- `source_id` peut être NULL si la source est une URL non curée
- Permet de lier un souvenir à une URL sans créer de source formelle
- Les sources "curées" ont un enregistrement dans `sources`

### UI/TUI

**Modifications TUI prévues** :
1. `AddEntryScreen` : Ajouter champ "Sources" (autocomplete)
2. `EntryDetailScreen` : Afficher sources liées
3. `SourceListScreen` : Nouvelle vue dashboard sources
4. `SourceDetailScreen` : Vue source avec backlinks

**Widgets réutilisables** :
- `SourceSuggester` : Input avec autocomplete thèmes/URLs
- `BacklinksWidget` : Liste cliquable de souvenirs liés

---

## Risques Techniques Identifiés

| Risque | Probabilité | Impact | Mitigation |
|--------|-------------|--------|------------|
| Migration DB casse données | Faible | Critique | Backup automatique avant migration |
| Link rot false positives | Moyenne | Faible | Retry 2x avant marquer inaccessible |
| Score non intuitif | Moyenne | Moyenne | Valeurs par défaut conservatrices |
| Performance recherche | Faible | Moyenne | Index sur score, domain |

---

## Sources Techniques Consultées

- [SQLite PRAGMA user_version](https://sqlite.org/pragma.html#pragma_user_version)
- [Python urllib.request](https://docs.python.org/3/library/urllib.request.html)
- [pytest fixtures](https://docs.pytest.org/en/stable/explanation/fixtures.html)
- Existant : `rekall/db.py` (pattern migrations)
- Existant : `tests/conftest.py` (fixtures)
