# Tasks: Database Maintenance

**Input**: Design documents from `/specs/005-db-maintenance/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Non demandés explicitement - tests optionnels non inclus.

**Organization**: Tasks groupées par User Story pour implémentation et test indépendants.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Peut être exécuté en parallèle (fichiers différents, pas de dépendances)
- **[Story]**: User Story concernée (US1, US2, etc.)
- Chemins exacts inclus dans les descriptions

---

## Phase 1: Setup (Infrastructure)

**Purpose**: Créer le module backup.py et structures de données

- [ ] T001 Créer le fichier rekall/backup.py avec imports de base (Path, datetime, shutil, sqlite3)
- [ ] T002 [P] Créer la dataclass BackupInfo dans rekall/backup.py (path, timestamp, size, db_name)
- [ ] T003 [P] Créer la dataclass DatabaseStats dans rekall/backup.py (path, schema_version, is_current, entries, links, size)
- [ ] T004 [P] Ajouter constante CURRENT_SCHEMA_VERSION dans rekall/backup.py (import depuis db.py)

**Checkpoint**: Module backup.py créé avec dataclasses - prêt pour les fonctions

---

## Phase 2: Foundational (Fonctions Core)

**Purpose**: Implémenter les fonctions de backup/restore utilisées par CLI et TUI

- [ ] T005 Implémenter get_default_backups_dir() dans rekall/backup.py (utilise paths.py)
- [ ] T006 [P] Implémenter validate_backup(backup_path) dans rekall/backup.py (PRAGMA integrity_check)
- [ ] T007 Implémenter create_backup(db_path, output) dans rekall/backup.py (WAL flush + shutil.copy2)
- [ ] T008 Implémenter restore_backup(backup_path, db_path) dans rekall/backup.py (safety backup + replace)
- [ ] T009 [P] Implémenter list_backups(backups_dir) dans rekall/backup.py (tri par date)
- [ ] T010 Implémenter get_database_stats(db_path) dans rekall/backup.py (query stats)

**Checkpoint**: Fonctions core prêtes - CLI et TUI peuvent les utiliser

---

## Phase 3: User Story 1 - Voir les informations (Priority: P1)

**Goal**: Afficher les statistiques de la base de données

**Independent Test**: Exécuter `rekall info`, vérifier affichage path, schema, entries, links, size

### Implementation US1

- [ ] T011 [US1] Ajouter messages i18n pour info.* dans rekall/i18n.py
- [ ] T012 [US1] Ajouter commande `rekall info` dans rekall/cli.py
- [ ] T013 [US1] Implémenter l'affichage formaté avec Rich (table/panel) dans rekall/cli.py
- [ ] T014 [P] [US1] Gérer le cas "no database found" dans rekall/cli.py

**Checkpoint**: US1 complète - `rekall info` affiche les statistiques

---

## Phase 4: User Story 2 - Créer un backup (Priority: P1)

**Goal**: Sauvegarder la base de données en un clic

**Independent Test**: Exécuter `rekall backup`, vérifier fichier créé dans ~/.rekall/backups/

### Implementation US2

- [ ] T015 [US2] Ajouter messages i18n pour backup.* dans rekall/i18n.py
- [ ] T016 [US2] Ajouter commande `rekall backup` dans rekall/cli.py
- [ ] T017 [US2] Ajouter option `--output PATH` à `rekall backup` dans rekall/cli.py
- [ ] T018 [P] [US2] Implémenter l'affichage confirmation avec taille dans rekall/cli.py

**Checkpoint**: US2 complète - `rekall backup` crée un backup validé

---

## Phase 5: User Story 3 - Restaurer depuis backup (Priority: P1)

**Goal**: Restaurer la base de données depuis une sauvegarde avec safety net

**Independent Test**: Exécuter `rekall restore <file>`, vérifier DB restaurée + safety backup créé

### Implementation US3

- [ ] T019 [US3] Ajouter messages i18n pour restore.* dans rekall/i18n.py
- [ ] T020 [US3] Ajouter commande `rekall restore <FILE>` dans rekall/cli.py
- [ ] T021 [US3] Implémenter la création automatique du safety backup dans rekall/cli.py
- [ ] T022 [P] [US3] Implémenter l'affichage des statistiques post-restore dans rekall/cli.py
- [ ] T023 [US3] Gérer les erreurs (fichier inexistant, backup invalide) dans rekall/cli.py

**Checkpoint**: US3 complète - `rekall restore` restaure avec safety backup automatique

---

## Phase 6: User Story 4 - Menu TUI Maintenance (Priority: P2)

**Goal**: Intégrer backup/restore dans l'interface TUI

**Independent Test**: Ouvrir TUI, naviguer vers Installation & Maintenance, créer backup via interface

### Implementation US4

- [ ] T024 [US4] Renommer entrée menu "Installation" → "Installation & Maintenance" dans rekall/tui.py
- [ ] T025 [US4] Ajouter bouton "Database Info" dans le menu maintenance TUI
- [ ] T026 [US4] Ajouter modal/écran d'affichage des stats DB dans rekall/tui.py
- [ ] T027 [P] [US4] Ajouter bouton "Create Backup" dans le menu maintenance TUI
- [ ] T028 [P] [US4] Ajouter confirmation après backup réussi dans rekall/tui.py
- [ ] T029 [US4] Ajouter bouton "Restore from Backup" dans le menu maintenance TUI
- [ ] T030 [US4] Implémenter le sélecteur de fichier backup (liste des backups) dans rekall/tui.py
- [ ] T031 [US4] Ajouter dialogue de confirmation avant restore dans rekall/tui.py
- [ ] T032 [P] [US4] Ajouter messages i18n pour TUI maintenance dans rekall/i18n.py

**Checkpoint**: US4 complète - TUI permet info/backup/restore via interface graphique

---

## Phase 7: Polish & Validation

**Purpose**: Nettoyage et validation finale

- [ ] T033 [P] Valider le quickstart.md avec une démo complète
- [ ] T034 [P] Mettre à jour README.md avec les nouvelles commandes
- [ ] T035 Exécuter `ruff check` et corriger les erreurs lint
- [ ] T036 [P] Vérifier les edge cases (DB vide, backup corrompu, permissions)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: Pas de dépendances - peut démarrer immédiatement
- **Foundational (Phase 2)**: Dépend de Setup - BLOQUE les User Stories
- **US1-US3 (Phases 3-5)**: Dépendent de Foundational - peuvent être parallélisées
- **US4 (Phase 6)**: Dépend de US1-US3 (réutilise les fonctions)
- **Polish (Phase 7)**: Dépend de toutes les US

### User Story Dependencies

```
Setup → Foundational → ┬─ US1 (Info) ────────┐
                       ├─ US2 (Backup) ──────┼→ US4 (TUI) → Polish
                       └─ US3 (Restore) ─────┘
```

### Parallel Opportunities

**Setup (Phase 1)**:
```bash
# Parallèle: T002, T003, T004 (dataclasses indépendantes)
```

**Foundational (Phase 2)**:
```bash
# Parallèle: T006, T009 (validate et list)
```

**US4 (Phase 6)**:
```bash
# Parallèle: T027, T028, T032 (boutons et i18n)
```

---

## Implementation Strategy

### MVP First (CLI Only)

1. Compléter Phase 1: Setup (T001-T004)
2. Compléter Phase 2: Foundational (T005-T010)
3. Compléter Phases 3-5: US1, US2, US3 (T011-T023)
4. **STOP et VALIDER**: Tester CLI indépendamment
5. Déployer si prêt - MVP avec backup/restore CLI fonctionnel

### Full Delivery

1. MVP CLI
2. Ajouter US4 (TUI) → Test → Interface graphique complète
3. Polish → Documentation et validation

---

## Summary

| Métrique | Valeur |
|----------|--------|
| **Total tâches** | 36 |
| **Phase 1 (Setup)** | 4 |
| **Phase 2 (Foundational)** | 6 |
| **US1 (Info) P1** | 4 |
| **US2 (Backup) P1** | 4 |
| **US3 (Restore) P1** | 5 |
| **US4 (TUI) P2** | 9 |
| **Polish** | 4 |
| **Tâches parallélisables [P]** | 14 |

### MVP Scope

**CLI seul** (19 tâches: Setup + Foundational + US1-US3):
- `rekall info` - voir stats DB
- `rekall backup` - créer backup
- `rekall restore` - restaurer avec safety net

### Independent Test Criteria

| US | Test indépendant |
|----|------------------|
| US1 | `rekall info` affiche path, schema, entries, links, size |
| US2 | `rekall backup` crée fichier validé dans ~/.rekall/backups/ |
| US3 | `rekall restore <file>` restaure + safety backup créé |
| US4 | TUI permet info/backup/restore via interface graphique |
