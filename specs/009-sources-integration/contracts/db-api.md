# Database API Contract: Sources Integration

**Date** : 2025-12-11
**Module** : `rekall/db.py`

---

## Nouvelles Méthodes Database

### Sources CRUD

#### `add_source(source: Source) -> None`

Ajoute une nouvelle source documentaire.

**Input** :
```python
source = Source(
    id="01JERK...",           # ULID (auto-généré si vide)
    domain="pinecone.io",     # Required
    url_pattern="https://pinecone.io/learn/*",  # Optional
    reliability='B',          # Default 'B'
    decay_rate='medium',      # Default 'medium'
)
```

**Comportement** :
- Génère ULID si `id` vide
- Initialise `created_at` à maintenant
- Initialise `personal_score` à 50.0
- Initialise `status` à 'active'

**Erreurs** :
- `ValueError` si `domain` vide
- `sqlite3.IntegrityError` si `id` dupliqué

---

#### `get_source(source_id: str) -> Optional[Source]`

Récupère une source par ID.

**Input** : `source_id` (ULID)

**Output** : `Source` ou `None` si non trouvée

---

#### `get_source_by_domain(domain: str) -> Optional[Source]`

Récupère une source par domaine normalisé.

**Input** : `domain` (ex: "pinecone.io")

**Output** : `Source` ou `None` si non trouvée

---

#### `update_source(source: Source) -> None`

Met à jour une source existante.

**Input** : `Source` avec `id` existant

**Comportement** :
- Ne modifie pas `created_at`
- Recalcule `personal_score` si `usage_count` ou `last_used` modifié

---

#### `delete_source(source_id: str) -> bool`

Supprime une source.

**Input** : `source_id` (ULID)

**Output** : `True` si supprimée, `False` si non trouvée

**Comportement** :
- Les `entry_sources.source_id` passent à NULL (SET NULL)

---

### Sources Listing

#### `list_sources(limit: int = 100, offset: int = 0, status: Optional[str] = None) -> list[Source]`

Liste les sources avec pagination.

**Input** :
- `limit`: Max résultats (défaut 100)
- `offset`: Pagination
- `status`: Filtre optionnel ('active', 'inaccessible', 'archived')

**Output** : Liste de `Source` triée par `personal_score DESC`

---

#### `get_top_sources(limit: int = 20) -> list[Source]`

Récupère les sources les mieux notées.

**Input** : `limit` (défaut 20, max 100)

**Output** : Liste de `Source` actives triée par `personal_score DESC`

---

#### `get_dormant_sources(months: int = 6, limit: int = 20) -> list[Source]`

Récupère les sources dormantes (non utilisées depuis X mois).

**Input** :
- `months`: Seuil en mois (défaut 6)
- `limit`: Max résultats

**Output** : Liste de `Source` triée par `last_used ASC`

---

#### `get_emerging_sources(days: int = 30, min_citations: int = 3) -> list[tuple[Source, int]]`

Récupère les sources émergentes (nouvellement populaires).

**Input** :
- `days`: Fenêtre temporelle (défaut 30)
- `min_citations`: Seuil minimum (défaut 3)

**Output** : Liste de `(Source, citation_count)` triée par count DESC

---

### Entry-Source Links

#### `link_entry_to_source(entry_id: str, source_type: str, source_ref: str, source_id: Optional[str] = None, note: Optional[str] = None) -> EntrySource`

Crée un lien entre un souvenir et une source.

**Input** :
- `entry_id`: ULID du souvenir (required)
- `source_type`: 'theme', 'url', 'file' (required)
- `source_ref`: Référence (required)
- `source_id`: ULID source curée (optional)
- `note`: Note contextuelle (optional)

**Output** : `EntrySource` créé

**Comportement** :
- Génère ULID pour le lien
- Si `source_id` fourni, incrémente `usage_count` de la source
- Met à jour `last_used` de la source

**Erreurs** :
- `ValueError` si `entry_id` inexistant
- `ValueError` si `source_id` fourni mais inexistant

---

#### `unlink_entry_from_source(entry_source_id: str) -> bool`

Supprime un lien entry-source.

**Input** : `entry_source_id` (ULID du lien)

**Output** : `True` si supprimé, `False` si non trouvé

**Note** : Ne décrémente pas `usage_count` (historique conservé)

---

#### `get_entry_sources(entry_id: str) -> list[EntrySource]`

Récupère les sources liées à un souvenir.

**Input** : `entry_id` (ULID souvenir)

**Output** : Liste de `EntrySource` avec données source jointes

---

#### `get_source_backlinks(source_id: str) -> list[tuple[Entry, EntrySource]]`

Récupère les souvenirs citant une source (backlinks).

**Input** : `source_id` (ULID source)

**Output** : Liste de `(Entry, EntrySource)` triée par date DESC

---

#### `count_source_backlinks(source_id: str) -> int`

Compte le nombre de backlinks d'une source.

**Input** : `source_id` (ULID source)

**Output** : Nombre de liens

---

### Scoring

#### `recalculate_source_score(source_id: str) -> float`

Recalcule le score d'une source.

**Input** : `source_id` (ULID source)

**Output** : Nouveau score (0-100)

**Comportement** :
- Utilise formule : `usage_score + recency_score + reliability_bonus`
- Met à jour `personal_score` dans la base
- Retourne le nouveau score

---

#### `update_source_usage(source_id: str) -> None`

Met à jour les métriques d'usage après une citation.

**Input** : `source_id` (ULID source)

**Comportement** :
- Incrémente `usage_count`
- Met à jour `last_used` à maintenant
- Recalcule `personal_score`
- Promeut `reliability` si seuil atteint (C→B à 1, B→A à 5)

---

### Link Rot

#### `update_source_status(source_id: str, is_accessible: bool, status_message: str) -> None`

Met à jour le statut d'accessibilité d'une source.

**Input** :
- `source_id`: ULID source
- `is_accessible`: Résultat de la vérification
- `status_message`: Message de statut (ex: "HTTP 404")

**Comportement** :
- Met à jour `status` à 'active' ou 'inaccessible'
- Met à jour `last_verified` à maintenant

---

#### `get_sources_to_verify(limit: int = 50) -> list[Source]`

Récupère les sources à vérifier (non vérifiées depuis 24h).

**Input** : `limit` (défaut 50)

**Output** : Liste de `Source` avec `url_pattern` non NULL, triée par `last_verified ASC`

---

## Modèles Dataclass

### Source

```python
@dataclass
class Source:
    id: str = ""
    domain: str = ""
    url_pattern: Optional[str] = None
    usage_count: int = 0
    last_used: Optional[datetime] = None
    personal_score: float = 50.0
    reliability: str = 'B'  # A, B, C
    decay_rate: str = 'medium'  # fast, medium, slow
    last_verified: Optional[datetime] = None
    status: str = 'active'  # active, inaccessible, archived
    created_at: datetime = field(default_factory=datetime.now)
```

### EntrySource

```python
@dataclass
class EntrySource:
    id: str = ""
    entry_id: str = ""
    source_id: Optional[str] = None
    source_type: str = ""  # theme, url, file
    source_ref: str = ""
    note: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)

    # Données jointes (non persistées)
    source: Optional[Source] = None
```

---

## Exemples d'Utilisation

### Lier un souvenir à une source

```python
# Créer source si nouvelle
source = db.get_source_by_domain("pinecone.io")
if not source:
    source = Source(domain="pinecone.io", url_pattern="https://pinecone.io/*")
    db.add_source(source)

# Lier au souvenir
link = db.link_entry_to_source(
    entry_id="01JERK123...",
    source_type="url",
    source_ref="https://pinecone.io/learn/rag/",
    source_id=source.id,
    note="Section sur chunking"
)
```

### Obtenir les top sources pour une recherche

```python
top_sources = db.get_top_sources(limit=10)
for source in top_sources:
    print(f"site:{source.domain} (score: {source.personal_score:.0f})")
```

### Vérifier les backlinks

```python
count = db.count_source_backlinks(source.id)
print(f"Cité par {count} souvenirs")

backlinks = db.get_source_backlinks(source.id)
for entry, link in backlinks:
    print(f"  - {entry.title}")
    if link.note:
        print(f"    Note: {link.note}")
```
