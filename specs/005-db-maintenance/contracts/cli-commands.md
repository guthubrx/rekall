# CLI Commands Contract: Database Maintenance

**Feature**: 005-db-maintenance
**Date**: 2025-12-09

## Nouvelles Commandes

### `rekall info`

Affiche les informations de la base de données.

**Signature**:
```
rekall info
```

**Options**: Aucune

**Output (succès)**:
```
Rekall v0.1.0
─────────────────────────
Database:  ~/.local/share/rekall/knowledge.db
Schema:    v2 (current)
Entries:   42 (38 active, 4 obsolete)
Links:     15
Size:      256 KB
```

**Output (pas de DB)**:
```
No database found.
Run 'rekall init' to create one.
```

**Exit codes**:
- `0`: Succès
- `1`: Erreur (DB corrompue, etc.)

---

### `rekall backup`

Crée une sauvegarde de la base de données.

**Signature**:
```
rekall backup [--output PATH]
```

**Options**:
| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--output`, `-o` | Path | Auto-generated | Chemin de sortie personnalisé |

**Output (succès)**:
```
✓ Backup created: ~/.rekall/backups/knowledge_2025-12-09_143022.db
  Size: 256 KB
```

**Output (custom path)**:
```
✓ Backup created: /path/to/my-backup.db
  Size: 256 KB
```

**Output (erreur)**:
```
Error: No database to backup.
Error: Cannot write to /path/to/output.db
```

**Exit codes**:
- `0`: Succès
- `1`: Erreur

**Comportement**:
1. Vérifie que la DB existe
2. Flush WAL avec `PRAGMA wal_checkpoint(TRUNCATE)`
3. Copie le fichier avec `shutil.copy2()`
4. Vérifie intégrité du backup avec `PRAGMA integrity_check`
5. Affiche confirmation

---

### `rekall restore`

Restaure la base de données depuis une sauvegarde.

**Signature**:
```
rekall restore <FILE>
```

**Arguments**:
| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `FILE` | Path | Oui | Chemin vers le fichier backup |

**Output (succès)**:
```
⚠ Creating safety backup before restore...
  Saved: ~/.rekall/backups/knowledge_2025-12-09_143025_pre-restore.db

✓ Database restored from: /path/to/backup.db
  Entries: 42 | Links: 15
```

**Output (erreur validation)**:
```
Error: Invalid backup file (integrity check failed).
Current database unchanged.
```

**Output (fichier inexistant)**:
```
Error: Backup file not found: /path/to/backup.db
```

**Exit codes**:
- `0`: Succès
- `1`: Erreur

**Comportement**:
1. Vérifie que le fichier backup existe
2. Valide intégrité avec `PRAGMA integrity_check`
3. **Crée backup automatique** de la DB actuelle (safety net)
4. Remplace la DB actuelle par le backup
5. Affiche statistiques du restore

---

## Intégration i18n

Nouveaux messages à ajouter dans `rekall/i18n.py`:

```python
"info.title": "Database Information"
"info.no_db": "No database found."
"info.schema": "Schema"
"info.schema_current": "(current)"
"info.schema_outdated": "(outdated - run init)"
"info.entries": "Entries"
"info.links": "Links"
"info.size": "Size"

"backup.created": "Backup created"
"backup.size": "Size"
"backup.no_db": "No database to backup"
"backup.error": "Backup failed"

"restore.safety_backup": "Creating safety backup before restore..."
"restore.saved": "Saved"
"restore.success": "Database restored from"
"restore.invalid": "Invalid backup file (integrity check failed)"
"restore.not_found": "Backup file not found"
"restore.unchanged": "Current database unchanged"
```
