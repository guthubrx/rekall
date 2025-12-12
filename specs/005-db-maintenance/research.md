# Research: Database Maintenance

**Feature**: 005-db-maintenance
**Date**: 2025-12-09

## Contexte Technique

Cette feature étend un projet Python existant (Rekall) avec des fonctionnalités de maintenance de base de données SQLite.

## Décisions Techniques

### 1. Méthode de Backup SQLite

**Décision**: Copie fichier avec `shutil.copy2()` après flush WAL

**Rationale**:
- Plus rapide que `sqlite3 .dump` (copie binaire)
- Préserve le mode WAL et les indexes
- Copie exacte byte-par-byte

**Alternatives considérées**:
- `sqlite3 .dump` → Plus lent, génère SQL texte, risque de perte données WAL non flushées
- `VACUUM INTO` → Nécessite SQLite 3.27+, réorganise la DB (pas une copie exacte)

**Implémentation**:
```python
def create_backup(db_path: Path, output_path: Path) -> Path:
    # Flush WAL to main DB file
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
    conn.close()

    # Copy file with metadata
    shutil.copy2(db_path, output_path)
    return output_path
```

### 2. Validation de Backup

**Décision**: `PRAGMA integrity_check` sur le fichier backup

**Rationale**:
- Détecte corruption SQLite interne
- Standard industry pour validation SQLite
- Rapide pour DBs < 100MB

**Alternatives considérées**:
- Checksum MD5/SHA → Ne détecte pas corruption interne SQLite
- Comparer taille fichier → Insuffisant

**Implémentation**:
```python
def validate_backup(backup_path: Path) -> bool:
    conn = sqlite3.connect(str(backup_path))
    result = conn.execute("PRAGMA integrity_check").fetchone()
    conn.close()
    return result[0] == "ok"
```

### 3. Organisation du Code

**Décision**: Nouveau module `rekall/backup.py`

**Rationale**:
- Séparation des responsabilités (SoC)
- Testabilité isolée
- Réutilisable par CLI et TUI

**Structure**:
```python
# rekall/backup.py
@dataclass
class BackupInfo:
    path: Path
    timestamp: datetime
    size: int

def create_backup(db_path: Path, output: Optional[Path] = None) -> BackupInfo
def restore_backup(backup_path: Path, db_path: Path) -> bool
def validate_backup(backup_path: Path) -> bool
def list_backups(backups_dir: Path) -> list[BackupInfo]
def get_default_backups_dir() -> Path
```

### 4. Format Nom de Fichier Backup

**Décision**: `knowledge_YYYY-MM-DD_HHMMSS.db`

**Rationale**:
- Tri chronologique naturel (ls -la)
- Horodatage précis à la seconde
- Extension `.db` cohérente avec source

**Exemple**: `knowledge_2025-12-09_143022.db`

### 5. Répertoire Backups

**Décision**: `~/.rekall/backups/` (ou XDG si configuré)

**Rationale**:
- Cohérent avec les conventions Rekall existantes
- Séparé de la DB principale
- Facile à retrouver

## Sources Consultées

- SQLite Documentation: [PRAGMA wal_checkpoint](https://sqlite.org/pragma.html#pragma_wal_checkpoint)
- SQLite Documentation: [PRAGMA integrity_check](https://sqlite.org/pragma.html#pragma_integrity_check)
- Python shutil: [shutil.copy2](https://docs.python.org/3/library/shutil.html#shutil.copy2)

## Patterns Existants dans Rekall

Consultés pour cohérence :
- `rekall/archive.py` - Pattern export/import existant
- `rekall/paths.py` - Gestion des chemins XDG
- `rekall/db.py` - Méthode `get_schema_version()` existante
