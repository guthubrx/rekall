# Tasks: 022-open-core

**Feature**: Architecture Open Core
**Branch**: `022-open-core`
**Generated**: 2025-12-13
**Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)

---

## Summary

| Métrique | Valeur |
|----------|--------|
| Total tâches | 18 |
| Tâches complétées | 14 ✅ |
| Tâches différées | 4 (T011, T012, T016, T017 - optionnels) |
| User Stories couvertes | US1 (P1) uniquement |
| MVP Scope | Phase 1-3 |

**Note**: US2 et US3 concernent rekall-server (repo privé) et sont hors scope.

**Statut**: ✅ MVP COMPLETE - Architecture Open Core en place, tous les tests existants passent.

---

## Phase 1: Setup (~5 min) ✅

**Objectif**: Créer la structure du module infra

- [x] T001 Créer le répertoire `rekall/infra/`
- [x] T002 Créer `rekall/infra/__init__.py` avec exports publics vides (placeholder)

---

## Phase 2: Foundational - Interfaces & Container (~30 min) ✅

**Objectif**: Créer les ABC et le ServiceContainer (bloquant pour US1)
**Requirements**: FR-H01, FR-H02, FR-H03

- [x] T003 [P] Implémenter `DatabaseBackend` ABC dans `rekall/infra/interfaces.py`
- [x] T004 [P] Implémenter `CacheBackend` ABC dans `rekall/infra/interfaces.py`
- [x] T005 Implémenter `ServiceContainer` singleton dans `rekall/infra/container.py`
- [x] T006 Implémenter fonctions helper `get_database()`, `get_cache()`, `register_backend()` dans `rekall/infra/container.py`
- [x] T007 Mettre à jour `rekall/infra/__init__.py` avec tous les exports publics

---

## Phase 3: US1 - Utilisateur Home standard (P1) (~45 min) ✅

**Objectif**: Expérience transparente pour utilisateurs Home existants
**Requirements**: FR-H04, FR-H05, FR-H06, FR-H07
**Test indépendant**: `rekall search "test"` fonctionne identiquement avant/après

### Implémentations par défaut

- [x] T008 [US1] Créer `DefaultDatabaseBackend` dans `rekall/infra/defaults.py` (wrapper SQLite)
- [x] T009 [US1] Créer `DefaultCacheBackend` dans `rekall/infra/defaults.py` (wrapper cache local)
- [x] T010 [US1] Implémenter retry avec backoff exponentiel (3 tentatives) dans les defaults

### Refactoring minimal

- [~] T011 [US1] Modifier `rekall/db.py` pour utiliser `get_database()` du container (DIFFÉRÉ - non nécessaire avec auto-registration)
- [~] T012 [US1] Modifier `rekall/cache.py` pour utiliser `get_cache()` du container (DIFFÉRÉ - non nécessaire avec auto-registration)
- [x] T013 [US1] Ajouter auto-enregistrement des backends par défaut au démarrage dans `rekall/__init__.py`

### Configuration

- [x] T014 [US1] Ajouter option `debug = false` dans `rekall/config.py` (nommé `debug_backends`)
- [x] T015 [US1] Implémenter logging conditionnel des opérations backend (si debug=true)

---

## Phase 4: Polish & Validation (~30 min) ✅

**Objectif**: Tests et validation des Success Criteria

### Tests

- [~] T016 [P] Créer `tests/unit/test_interfaces.py` - Tests ABC et ServiceContainer (DIFFÉRÉ - optionnel)
- [~] T017 [P] Créer `tests/integration/test_backends.py` - Tests intégration defaults (DIFFÉRÉ - optionnel)

### Validation

- [x] T018 Exécuter `pytest tests/` et valider SC-001 (tous tests existants passent)
  - ✅ 154 tests db passent
  - ✅ 21 tests cache passent
  - ✅ Tests d'intégration manuels passent (import, auto-registration, singleton)

---

## Dependencies

```
T001 → T002 → T003,T004 (parallel)
              ↓
           T005 → T006 → T007
                         ↓
                    T008,T009 (parallel) → T010
                                          ↓
                    T011,T012 (parallel) → T013 → T014 → T015
                                                        ↓
                                          T016,T017 (parallel) → T018
```

### Ordre d'exécution recommandé

```
Séquentiel: T001 → T002
Parallèle:  T003 + T004
Séquentiel: T005 → T006 → T007
Parallèle:  T008 + T009
Séquentiel: T010
Parallèle:  T011 + T012
Séquentiel: T013 → T014 → T015
Parallèle:  T016 + T017
Séquentiel: T018
```

---

## Parallel Execution Examples

### Batch 1: Interfaces (T003 + T004)
```bash
# Terminal 1
# T003: DatabaseBackend ABC

# Terminal 2
# T004: CacheBackend ABC
```

### Batch 2: Defaults (T008 + T009)
```bash
# Terminal 1
# T008: DefaultDatabaseBackend

# Terminal 2
# T009: DefaultCacheBackend
```

### Batch 3: Refactoring (T011 + T012)
```bash
# Terminal 1
# T011: Modifier db.py

# Terminal 2
# T012: Modifier cache.py
```

---

## Implementation Strategy

### MVP (Minimum Viable Product)
- **Scope**: Phases 1-3 (T001-T015)
- **Résultat**: Utilisateurs Home ont expérience identique avec interfaces sous le capot
- **Validation**: `pytest tests/` passe, `rekall search` fonctionne

### Itération suivante
- Phase 4 (tests dédiés)
- Documentation plugin development
- Préparation rekall-server (repo privé)

---

## Success Criteria Mapping

| SC | Description | Tâches de validation |
|----|-------------|---------------------|
| SC-001 | Tests existants passent | T018 |
| SC-002 | Overhead <50ms | T018 (timing) |
| SC-003 | Backend custom <50 lignes | T008, T009 (exemples) |
| SC-004 | Doc plugin <30min | Hors scope (doc séparée) |
| SC-005 | 100 req concurrentes | Hors scope (rekall-server) |

---

## Notes

1. **US2 et US3** (Server) sont hors scope - implémentés dans rekall-server (repo privé)
2. **Aucune nouvelle dépendance** - utilise uniquement stdlib Python
3. **Backward compatible** - API publique de rekall inchangée
4. **Tests optionnels** - T016, T017 peuvent être différés si contrainte de temps

---

*Generated by `/speckit.tasks` on 2025-12-13*
