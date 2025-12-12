# Implementation Plan: Database Maintenance

**Branch**: `005-db-maintenance` | **Date**: 2025-12-09 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/005-db-maintenance/spec.md`

## Summary

Ajouter des commandes de maintenance de base de données pour Rekall : `rekall info` (affichage infos DB), `rekall backup` (sauvegarde), `rekall restore` (restauration). Intégrer ces fonctionnalités dans le menu TUI "Installation & Maintenance".

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: Typer (CLI), Textual (TUI), Rich (formatage), SQLite3 (stdlib)
**Storage**: SQLite (knowledge.db) avec shutil pour copie fichiers
**Testing**: pytest
**Target Platform**: macOS, Linux (CLI cross-platform)
**Project Type**: Single project (CLI tool avec TUI)
**Performance Goals**: Info < 1s, Backup < 5s pour 100MB, Restore < 10s
**Constraints**: Pas de dépendances externes pour backup (shutil uniquement)
**Scale/Scope**: Bases de données jusqu'à 1GB

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Article | Statut | Notes |
|---------|--------|-------|
| **III. Processus SpecKit** | ✅ | Spec créée via /speckit.specify |
| **VII. ADR** | ⏭️ | Pas de décision architecturale majeure |
| **XV. Test-Before-Next** | ✅ | Tests pytest existants |
| **XVII. DevKMS** | ✅ | Capture automatique si patterns découverts |

**Résultat**: ✅ Tous les gates passent. Pas de violations à justifier.

## Project Structure

### Documentation (this feature)

```text
specs/005-db-maintenance/
├── plan.md              # Ce fichier
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output (simple pour cette feature)
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (CLI contracts)
│   └── cli-commands.md  # Contrats des nouvelles commandes
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
rekall/
├── cli.py          # Nouvelles commandes: info, backup, restore
├── db.py           # Méthodes get_stats(), déjà get_schema_version()
├── tui.py          # Menu "Installation & Maintenance"
├── i18n.py         # Messages pour nouvelles commandes
└── backup.py       # (NOUVEAU) Module backup/restore

tests/
├── test_cli.py     # Tests commandes info/backup/restore
└── test_backup.py  # (NOUVEAU) Tests module backup
```

**Structure Decision**: Extension du projet existant. Un nouveau module `backup.py` pour isoler la logique backup/restore du CLI.

## Complexity Tracking

Pas de violations à justifier - feature simple sans nouvelle architecture.

---

## Phase 0: Research Technique

### Questions Techniques

Pas de NEEDS CLARIFICATION - le contexte technique est connu (projet existant).

### Points Techniques à Valider

| Question | Réponse |
|----------|---------|
| Méthode de backup SQLite | `shutil.copy2()` après flush WAL (`PRAGMA wal_checkpoint(TRUNCATE)`) |
| Validation backup | Ouvrir et vérifier `PRAGMA integrity_check` |
| Format filename | `knowledge_YYYY-MM-DD_HHMMSS.db` |
| Répertoire backups | `~/.rekall/backups/` (créé si absent) |

### Décisions Techniques

1. **Backup = copie fichier** (pas de dump SQL)
   - Rationale: Plus rapide, préserve WAL mode, copie binaire exacte
   - Alternative rejetée: `sqlite3 .dump` - Plus lent, risque de perte données WAL

2. **Validation par integrity_check**
   - Rationale: Détecte corruption avant restore
   - Alternative rejetée: Checksum simple - Ne détecte pas corruption SQLite interne

3. **Module séparé backup.py**
   - Rationale: Isolation, testabilité, réutilisable par TUI et CLI
   - Alternative rejetée: Inline dans cli.py - Trop de responsabilités

---

## Phase 1: Design & Contracts

### Data Model

Pas de nouvelles entités. Utilisation des structures existantes :

- `Database` (db.py) : Ajout méthode `get_stats() -> dict`
- `BackupInfo` (backup.py) : Dataclass pour info backup (path, timestamp, size)

### Contracts CLI

Voir `contracts/cli-commands.md` pour détails.

**Commandes:**
- `rekall info` - Affiche infos DB
- `rekall backup [--output PATH]` - Crée backup
- `rekall restore <FILE>` - Restaure depuis backup

### Quickstart

Voir `quickstart.md` pour guide utilisateur.
