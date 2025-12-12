# Tasks: MCP Tools Expansion

**Input**: Design documents from `/specs/015-mcp-tools-expansion/`
**Prerequisites**: plan.md, spec.md, research.md, contracts/mcp-tools.json

**Tests**: Non demandés explicitement - pas de tâches de tests générées.

**Organisation**: 8 User Stories (4 P1 + 4 P3) - chaque outil MCP est une story indépendante.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Peut s'exécuter en parallèle (fichiers différents, pas de dépendances)
- **[Story]**: User Story correspondante (US1-US8)
- Chemins exacts dans les descriptions

## Path Conventions

- **Fichier principal**: `rekall/mcp_server.py`
- **Tests**: `tests/test_mcp_server.py` (optionnel)

---

## Phase 1: Setup

**Purpose**: Préparation du fichier MCP server pour l'extension

- [x] T001 Vérifier que la branche 015-mcp-tools-expansion est active
- [x] T002 Lire le code existant de `rekall/mcp_server.py` pour comprendre les patterns

---

## Phase 2: Foundational

**Purpose**: Ajouter les 8 Tool definitions dans `list_tools()` et les dispatcher dans `call_tool()`

**⚠️ CRITIQUE**: Cette phase doit être complète avant l'implémentation des handlers

- [x] T003 Ajouter les 4 Tool P1 (unlink, related, similar, sources_suggest) dans `list_tools()` de `rekall/mcp_server.py`
- [x] T004 Ajouter les 4 Tool P3 (info, stale, generalize, sources_verify) dans `list_tools()` de `rekall/mcp_server.py`
- [x] T005 Ajouter les 8 dispatchers dans `call_tool()` de `rekall/mcp_server.py`

**Checkpoint**: ✅ Les 8 outils apparaissent dans `list_tools()`

---

## Phase 3: User Story 1 - rekall_unlink (Priority: P1)

**Goal**: Supprimer un lien existant entre deux entrées

**Independent Test**: `rekall_unlink(source_id, target_id)` supprime le lien et retourne confirmation

### Implementation

- [x] T006 [US1] Implémenter `_handle_unlink(args)` dans `rekall/mcp_server.py`
  - Appeler `db.delete_link(source_id, target_id)`
  - Retourner confirmation ou erreur si lien inexistant

**Checkpoint**: ✅ US1 fonctionnel - `rekall_unlink` supprime les liens

---

## Phase 4: User Story 2 - rekall_related (Priority: P1)

**Goal**: Explorer les entrées reliées à une entrée donnée

**Independent Test**: `rekall_related(entry_id)` retourne les entrées liées avec types de relation

### Implementation

- [x] T007 [US2] Implémenter `_handle_related(args)` dans `rekall/mcp_server.py`
  - Appeler `db.get_related_entries(entry_id, depth)`
  - Formater sortie avec relations entrantes/sortantes
  - Gérer cas sans liens (message explicite)

**Checkpoint**: ✅ US2 fonctionnel - `rekall_related` explore le graphe

---

## Phase 5: User Story 3 - rekall_similar (Priority: P1)

**Goal**: Trouver les entrées sémantiquement similaires

**Independent Test**: `rekall_similar(entry_id)` retourne entrées avec scores de similarité

### Implementation

- [x] T008 [US3] Implémenter `_handle_similar(args)` dans `rekall/mcp_server.py`
  - Vérifier si embeddings activés (`cfg.smart_embeddings_enabled`)
  - Si non: retourner message explicite (pas d'erreur)
  - Si oui: appeler `embeddings.find_similar(entry_id, db, limit)`
  - Formater sortie avec scores

**Checkpoint**: ✅ US3 fonctionnel - `rekall_similar` trouve entrées similaires ou dégrade gracieusement

---

## Phase 6: User Story 4 - rekall_sources_suggest (Priority: P1)

**Goal**: Suggérer des sources web pertinentes pour une entrée

**Independent Test**: `rekall_sources_suggest(entry_id)` retourne sources pertinentes

### Implementation

- [x] T009 [US4] Implémenter `_handle_sources_suggest(args)` dans `rekall/mcp_server.py`
  - Récupérer l'entrée avec `db.get(entry_id)`
  - Extraire tags et keywords de l'entrée
  - Chercher sources par tags/themes avec `db.get_sources_by_tags()` ou `db.get_sources_by_theme()`
  - Limiter et formater les résultats
  - Gérer cas sans sources (message explicite)

**Checkpoint**: ✅ US4 fonctionnel - `rekall_sources_suggest` suggère des sources

---

## Phase 7: User Story 5 - rekall_info (Priority: P3)

**Goal**: Obtenir les statistiques de la base de connaissances

**Independent Test**: `rekall_info()` retourne stats (entrées, types, projets, liens)

### Implementation

- [x] T010 [P] [US5] Implémenter `_handle_info(args)` dans `rekall/mcp_server.py`
  - Compter entrées totales avec `db.list_all()`
  - Agréger par type et projet
  - Ajouter stats sources avec `db.get_source_statistics()`
  - Compter liens totaux
  - Formater sortie lisible

**Checkpoint**: ✅ US5 fonctionnel - `rekall_info` affiche les statistiques

---

## Phase 8: User Story 6 - rekall_stale (Priority: P3)

**Goal**: Trouver les entrées non consultées depuis N jours

**Independent Test**: `rekall_stale(days=90)` retourne entrées obsolètes

### Implementation

- [x] T011 [P] [US6] Implémenter `_handle_stale(args)` dans `rekall/mcp_server.py`
  - Appeler `db.get_stale_entries(days, limit)`
  - Formater sortie avec date dernier accès
  - Gérer cas sans entrées obsolètes (message explicite)

**Checkpoint**: ✅ US6 fonctionnel - `rekall_stale` identifie les entrées obsolètes

---

## Phase 9: User Story 7 - rekall_generalize (Priority: P3)

**Goal**: Créer une entrée générique à partir de plusieurs entrées

**Independent Test**: `rekall_generalize([A,B,C])` crée pattern avec liens derived_from

### Implementation

- [x] T012 [P] [US7] Implémenter `_handle_generalize(args)` dans `rekall/mcp_server.py`
  - Valider minimum 2 entry_ids
  - Récupérer les entrées sources
  - Générer titre si non fourni (combiner titres sources)
  - Créer nouvelle entrée type "pattern"
  - Créer liens "derived_from" vers chaque source
  - Retourner ID nouvelle entrée et résumé

**Checkpoint**: ✅ US7 fonctionnel - `rekall_generalize` crée des patterns

---

## Phase 10: User Story 8 - rekall_sources_verify (Priority: P3)

**Goal**: Vérifier l'accessibilité des URLs sources (link rot)

**Independent Test**: `rekall_sources_verify(limit=10)` retourne statuts URLs

### Implementation

- [x] T013 [P] [US8] Implémenter `_handle_sources_verify(args)` dans `rekall/mcp_server.py`
  - Récupérer sources à vérifier avec `db.get_sources_to_verify(limit)`
  - Appeler `link_rot.verify_sources()` ou vérification inline
  - Formater sortie avec statuts (accessible/broken/timeout)
  - Mettre à jour statuts dans DB

**Checkpoint**: ✅ US8 fonctionnel - `rekall_sources_verify` détecte le link rot

---

## Phase 11: Polish & Validation

**Purpose**: Validation finale et documentation

- [x] T014 Vérifier que les 8 outils apparaissent dans `list_tools()`
- [x] T015 Tester manuellement chaque outil avec des données de test (494 tests passent)
- [x] T016 [P] Mettre à jour REKALL_HELP dans `rekall/mcp_server.py` avec les nouveaux outils

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: Aucune dépendance
- **Phase 2 (Foundational)**: Dépend de Phase 1 - BLOQUE toutes les User Stories
- **Phases 3-10 (User Stories)**: Dépendent de Phase 2
  - Peuvent s'exécuter en parallèle (fichiers différents = même fichier mais fonctions différentes)
- **Phase 11 (Polish)**: Dépend de toutes les User Stories

### User Story Dependencies

Toutes les User Stories sont **indépendantes** :

| Story | Outil | Dépendances |
|-------|-------|-------------|
| US1 | rekall_unlink | Aucune |
| US2 | rekall_related | Aucune |
| US3 | rekall_similar | Aucune (dégrade si pas d'embeddings) |
| US4 | rekall_sources_suggest | Aucune (Feature 013 assumée fonctionnelle) |
| US5 | rekall_info | Aucune |
| US6 | rekall_stale | Aucune |
| US7 | rekall_generalize | Aucune |
| US8 | rekall_sources_verify | Aucune |

### Parallel Opportunities

Toutes les tâches T006-T013 peuvent s'exécuter en parallèle car elles modifient des fonctions différentes dans le même fichier.

```bash
# Lancer tous les handlers P1 en parallèle :
Task: "Implémenter _handle_unlink dans rekall/mcp_server.py"
Task: "Implémenter _handle_related dans rekall/mcp_server.py"
Task: "Implémenter _handle_similar dans rekall/mcp_server.py"
Task: "Implémenter _handle_sources_suggest dans rekall/mcp_server.py"

# Lancer tous les handlers P3 en parallèle :
Task: "Implémenter _handle_info dans rekall/mcp_server.py"
Task: "Implémenter _handle_stale dans rekall/mcp_server.py"
Task: "Implémenter _handle_generalize dans rekall/mcp_server.py"
Task: "Implémenter _handle_sources_verify dans rekall/mcp_server.py"
```

---

## Implementation Strategy

### MVP First (P1 Only)

1. Compléter Phase 1-2 (Setup + Foundational)
2. Compléter US1-US4 (outils P1)
3. **STOP et VALIDER**: Tester les 4 outils P1
4. Déployer/démontrer si satisfaisant

### Full Feature

1. Compléter MVP (P1)
2. Ajouter US5-US8 (outils P3)
3. Compléter Phase 11 (Polish)
4. Valider les 8 outils

---

## Notes

- Toutes les fonctions sous-jacentes existent déjà dans `db.py`, `embeddings.py`, `link_rot.py`
- Le travail = wrappers MCP uniquement
- Suivre le pattern des handlers existants (`_handle_search`, `_handle_show`, etc.)
- Chaque handler doit gérer les cas d'erreur avec messages explicites
- Commit après chaque User Story complétée
