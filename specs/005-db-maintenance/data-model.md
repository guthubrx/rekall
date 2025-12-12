# Data Model: Database Maintenance

**Feature**: 005-db-maintenance
**Date**: 2025-12-09

## Entités

### BackupInfo (nouvelle)

Information sur un fichier de backup.

```
BackupInfo
├── path: Path           # Chemin complet vers le fichier backup
├── timestamp: datetime  # Date/heure de création du backup
├── size: int            # Taille en bytes
└── db_name: str         # Nom de la DB source (knowledge.db)
```

**Validation**:
- `path` doit exister et être un fichier `.db`
- `size` > 0
- `timestamp` extrait du nom de fichier ou mtime

### DatabaseStats (nouvelle)

Statistiques de la base de données pour `rekall info`.

```
DatabaseStats
├── path: Path           # Chemin vers knowledge.db
├── schema_version: int  # Version du schéma (PRAGMA user_version)
├── is_current: bool     # True si version = CURRENT_SCHEMA_VERSION
├── total_entries: int   # Nombre total d'entrées
├── active_entries: int  # Entrées avec status='active'
├── obsolete_entries: int # Entrées avec status='obsolete'
├── links_count: int     # Nombre de liens
├── file_size: int       # Taille fichier en bytes
└── file_size_human: str # Taille formatée (ex: "256 KB")
```

## Relations

```
┌─────────────┐
│  Database   │
│ (existant)  │
└──────┬──────┘
       │ get_stats()
       ▼
┌─────────────────┐
│ DatabaseStats   │
└─────────────────┘

┌─────────────┐     create_backup()     ┌────────────┐
│  Database   │ ─────────────────────►  │ BackupInfo │
│   (source)  │                         └────────────┘
└─────────────┘                                │
       ▲                                       │
       │              restore_backup()         │
       └───────────────────────────────────────┘
```

## Stockage

**Backups**: `~/.rekall/backups/knowledge_YYYY-MM-DD_HHMMSS.db`

Le répertoire est créé automatiquement si absent.

## Intégration avec Modèles Existants

Aucune modification des modèles existants (`Entry`, `Link`, etc.).

Les nouvelles structures sont des dataclasses légères pour transport de données.
