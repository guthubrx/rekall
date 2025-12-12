# Data Model - Export/Import Sync

## Nouvelles Structures

### Manifest

Métadonnées de l'archive pour validation et compatibilité.

```python
@dataclass
class ArchiveStats:
    """Statistiques du contenu de l'archive."""
    entries_count: int
    projects: list[str]           # Liste des projets distincts
    types: dict[str, int]         # Comptage par type {bug: 50, pattern: 30}

@dataclass
class Manifest:
    """Métadonnées de l'archive .rekall."""
    format_version: str           # "1.0" - pour migration future
    created_at: datetime          # Timestamp ISO8601
    rekall_version: str           # Version de Rekall utilisée
    checksum: str                 # "sha256:<hash>" du contenu
    stats: ArchiveStats

    def to_dict(self) -> dict:
        """Serialize pour JSON."""
        return {
            "format_version": self.format_version,
            "created_at": self.created_at.isoformat(),
            "rekall_version": self.rekall_version,
            "checksum": self.checksum,
            "stats": {
                "entries_count": self.stats.entries_count,
                "projects": self.stats.projects,
                "types": self.stats.types,
            }
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Manifest":
        """Deserialize depuis JSON."""
        return cls(
            format_version=data["format_version"],
            created_at=datetime.fromisoformat(data["created_at"]),
            rekall_version=data["rekall_version"],
            checksum=data["checksum"],
            stats=ArchiveStats(
                entries_count=data["stats"]["entries_count"],
                projects=data["stats"]["projects"],
                types=data["stats"]["types"],
            )
        )
```

### Validation Result

Résultat de validation d'une archive.

```python
@dataclass
class ValidationResult:
    """Résultat de validation d'archive."""
    valid: bool
    errors: list[str]             # Erreurs bloquantes
    warnings: list[str]           # Avertissements non-bloquants

    def __bool__(self) -> bool:
        return self.valid
```

### Import Plan

Plan d'import avec classification des entrées.

```python
@dataclass
class Conflict:
    """Conflit entre entrée locale et importée."""
    entry_id: str
    local: Entry
    imported: Entry
    fields_changed: list[str]     # ["title", "content", "tags"]

    @property
    def summary(self) -> str:
        """Résumé des différences."""
        return f"{len(self.fields_changed)} champ(s) modifié(s): {', '.join(self.fields_changed)}"

@dataclass
class ImportPlan:
    """Plan d'import avec classification."""
    new_entries: list[Entry]      # Entrées à ajouter
    conflicts: list[Conflict]     # Conflits à résoudre
    identical: list[str]          # IDs identiques (skip)

    @property
    def total(self) -> int:
        return len(self.new_entries) + len(self.conflicts) + len(self.identical)

    @property
    def has_conflicts(self) -> bool:
        return len(self.conflicts) > 0
```

### Import Result

Résultat d'exécution d'import.

```python
@dataclass
class ImportResult:
    """Résultat d'exécution d'import."""
    success: bool
    added: int                    # Entrées ajoutées
    replaced: int                 # Entrées remplacées
    skipped: int                  # Entrées ignorées
    merged: int                   # Entrées fusionnées (nouveaux IDs)
    backup_path: Optional[Path]   # Chemin backup si créé
    errors: list[str]             # Erreurs rencontrées

    @property
    def total_processed(self) -> int:
        return self.added + self.replaced + self.skipped + self.merged
```

---

## Stratégies d'Import

```python
ImportStrategy = Literal["skip", "replace", "merge", "interactive"]
```

| Stratégie | Nouveaux | Conflits | Identiques |
|-----------|----------|----------|------------|
| `skip` | Ajouter | Garder local | Skip |
| `replace` | Ajouter | Écraser local | Skip |
| `merge` | Ajouter | Créer nouvel ID | Skip |
| `interactive` | Ajouter | Demander | Skip |

---

## Format Archive ZIP

### Structure

```
backup.rekall (ZIP)
├── manifest.json           # ~500 bytes
├── entries.json            # Variable (1KB - 10MB+)
└── research/               # Optionnel
    ├── custom-topic.md
    └── another-topic.md
```

### manifest.json

```json
{
  "format_version": "1.0",
  "created_at": "2025-12-07T14:30:00Z",
  "rekall_version": "0.1.0",
  "checksum": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  "stats": {
    "entries_count": 150,
    "projects": ["rekall", "bigmind", "speckit"],
    "types": {
      "bug": 50,
      "pattern": 40,
      "decision": 30,
      "pitfall": 15,
      "config": 10,
      "reference": 5
    }
  }
}
```

### entries.json

```json
[
  {
    "id": "01JARQH8P6MWGR5VKY3XZCBNFT",
    "title": "Fix circular import in React",
    "type": "bug",
    "content": "Solution: Use lazy imports...",
    "project": "bigmind",
    "tags": ["react", "import", "module"],
    "confidence": 4,
    "status": "active",
    "superseded_by": null,
    "created_at": "2025-12-01T10:30:00",
    "updated_at": "2025-12-07T14:00:00"
  }
]
```

---

## Calcul Checksum

Le checksum couvre `entries.json` uniquement (pas le manifest ni research/).

```python
def calculate_checksum(entries_json: bytes) -> str:
    """Calcule SHA256 du contenu entries.json."""
    import hashlib
    hash_obj = hashlib.sha256(entries_json)
    return f"sha256:{hash_obj.hexdigest()}"

def verify_checksum(archive_path: Path) -> bool:
    """Vérifie l'intégrité de l'archive."""
    with zipfile.ZipFile(archive_path, 'r') as zf:
        manifest = json.loads(zf.read("manifest.json"))
        entries_data = zf.read("entries.json")

        expected = manifest["checksum"]
        actual = calculate_checksum(entries_data)

        return expected == actual
```

---

## Détection de Conflits

### Algorithme

```python
def detect_conflict(local: Entry, imported: Entry) -> Optional[Conflict]:
    """Compare deux entrées pour détecter un conflit."""
    if local.id != imported.id:
        return None  # Pas de conflit possible

    # Comparer les champs significatifs
    fields_changed = []

    if local.title != imported.title:
        fields_changed.append("title")
    if local.content != imported.content:
        fields_changed.append("content")
    if local.type != imported.type:
        fields_changed.append("type")
    if local.project != imported.project:
        fields_changed.append("project")
    if set(local.tags) != set(imported.tags):
        fields_changed.append("tags")
    if local.confidence != imported.confidence:
        fields_changed.append("confidence")
    if local.status != imported.status:
        fields_changed.append("status")

    if not fields_changed:
        return None  # Identiques

    return Conflict(
        entry_id=local.id,
        local=local,
        imported=imported,
        fields_changed=fields_changed,
    )
```

### Critères "Identique"

Deux entrées sont identiques si :
- Même `id`
- Même `title`, `content`, `type`, `project`
- Mêmes `tags` (order-independent)
- Même `confidence`, `status`

Note : `created_at`, `updated_at`, `superseded_by` sont ignorés pour la comparaison.

---

## Backup Automatique

### Structure

```
~/.rekall/
├── knowledge.db
├── backups/
│   ├── pre-import-20251207-143000.rekall
│   ├── pre-import-20251208-091500.rekall
│   └── ...
```

### Naming Convention

```
pre-import-YYYYMMDD-HHMMSS.rekall
```

### Création

```python
def create_backup(db_path: Path) -> Path:
    """Crée un backup avant import destructif."""
    backup_dir = db_path.parent / "backups"
    backup_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_path = backup_dir / f"pre-import-{timestamp}.rekall"

    # Exporter toutes les entrées
    db = Database(db_path)
    db.init()
    entries = db.list_all(include_obsolete=True, limit=100000)
    db.close()

    RekallArchive.create(backup_path, entries)
    return backup_path
```

---

## Relations avec Modèles Existants

```
┌─────────────────────────────────────────────────────────────┐
│                      EXISTANT                               │
│  ┌──────────┐    ┌──────────┐    ┌──────────────┐          │
│  │  Entry   │───▶│ Database │───▶│ exporters.py │          │
│  │ models.py│    │  db.py   │    │ (JSON/MD)    │          │
│  └──────────┘    └──────────┘    └──────────────┘          │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                      NOUVEAU                                │
│  ┌──────────────┐    ┌─────────────┐    ┌───────────────┐  │
│  │ RekallArchive│───▶│ ImportPlan  │───▶│ImportExecutor │  │
│  │  archive.py  │    │   sync.py   │    │    sync.py    │  │
│  └──────────────┘    └─────────────┘    └───────────────┘  │
│         │                                       │          │
│         ▼                                       ▼          │
│  ┌──────────────┐                      ┌───────────────┐   │
│  │   Manifest   │                      │ ImportResult  │   │
│  │  archive.py  │                      │    sync.py    │   │
│  └──────────────┘                      └───────────────┘   │
└─────────────────────────────────────────────────────────────┘
```
