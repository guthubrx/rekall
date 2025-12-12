# Tâches d'Implémentation : Suppression d'Entrée depuis Browse

**Branche**: `008-browse-delete-entry`
**Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)
**Généré**: 2025-12-10

---

## Phase 1 : Setup

- [x] T001 Ajouter la méthode `count_links()` dans `rekall/db.py`
- [x] T002 [P] Ajouter les traductions delete overlay dans `rekall/i18n.py`

---

## Phase 2 : Fondation (Bloquant)

- [x] T003 Créer le widget `DeleteConfirmOverlay` dans `rekall/tui.py`
- [x] T004 Ajouter le CSS pour l'overlay de suppression dans `rekall/tui.py` (intégré dans widget DEFAULT_CSS)

---

## Phase 3 : User Story 1 - Suppression Basique (P1)

**Objectif**: Permettre la suppression d'une entrée via overlay centré
**Test indépendant**: Sélectionner une entrée sans liens, presser 'd', confirmer, vérifier suppression

- [x] T005 [US1] Modifier `action_delete_entry()` pour afficher l'overlay au lieu de quitter dans `rekall/tui.py`
- [x] T006 [US1] Implémenter la logique de confirmation (bouton Oui) avec suppression dans `rekall/tui.py`
- [x] T007 [US1] Implémenter la logique d'annulation (bouton Non) dans `rekall/tui.py`
- [x] T008 [US1] Implémenter le refresh de la DataTable après suppression dans `rekall/tui.py`
- [x] T009 [US1] Implémenter le déplacement du curseur vers l'entrée suivante dans `rekall/tui.py`
- [x] T010 [US1] Afficher toast de succès après suppression dans `rekall/tui.py`
- [x] T011 [US1] Gérer le cas de suppression de la dernière entrée (message "pas d'entrées") dans `rekall/tui.py`

---

## Phase 4 : User Story 2 - Avertissement Liens (P2)

**Objectif**: Afficher le nombre de liens impactés avant confirmation
**Test indépendant**: Créer une entrée avec 2+ liens, presser 'd', vérifier affichage du compteur

- [x] T012 [US2] Appeler `count_links()` dans `action_delete_entry()` avant affichage overlay dans `rekall/tui.py`
- [x] T013 [US2] Passer le nombre de liens au widget `DeleteConfirmOverlay` dans `rekall/tui.py`
- [x] T014 [US2] Afficher conditionnellement le message "N lien(s) seront supprimés" dans `rekall/tui.py`

---

## Phase 5 : User Story 3 - Raccourcis Clavier (P3)

**Objectif**: Permettre confirmation rapide via y/n/Escape
**Test indépendant**: Presser 'd' puis 'y' pour confirmer, ou 'd' puis 'n' pour annuler

- [x] T015 [US3] Ajouter binding 'y' pour confirmation dans `DeleteConfirmOverlay` dans `rekall/tui.py`
- [x] T016 [US3] Ajouter binding 'n' pour annulation dans `DeleteConfirmOverlay` dans `rekall/tui.py`
- [x] T017 [US3] Ajouter binding 'Escape' pour annulation dans `DeleteConfirmOverlay` dans `rekall/tui.py`

---

## Phase 6 : Polish & Edge Cases

- [x] T018 Gérer le cas où aucune entrée n'est sélectionnée (ne rien faire) dans `rekall/tui.py`
- [x] T019 Afficher toast d'erreur si la suppression échoue dans `rekall/tui.py`
- [x] T020 Retirer branche "delete" de action_browse() (suppression in-app via overlay) dans `rekall/tui.py`
- [x] T021 Vérifier que le binding 'd' existant fonctionne toujours dans `rekall/tui.py`

---

## Dépendances

```text
T001, T002 (parallèle) → T003 → T004 → T005-T011 (US1) → T012-T014 (US2) → T015-T017 (US3) → T018-T021 (Polish)
```

**Graphe de dépendances par User Story**:

```
Phase 1 (Setup) ✅
  ├── T001 count_links()
  └── T002 [P] traductions i18n
        │
        ▼
Phase 2 (Fondation) ✅
  └── T003 DeleteConfirmOverlay widget
        │
        └── T004 CSS overlay
              │
              ▼
Phase 3 (US1 - Suppression Basique) ✅
  └── T005-T011 (7 tâches)
        │
        ▼
Phase 4 (US2 - Avertissement Liens) ✅
  └── T012-T014 (3 tâches)
        │
        ▼
Phase 5 (US3 - Raccourcis Clavier) ✅
  └── T015-T017 (3 tâches)
        │
        ▼
Phase 6 (Polish) ✅
  └── T018-T021 (4 tâches)
```

## Résumé

| Métrique | Valeur |
|----------|--------|
| Total tâches | 21 |
| Tâches complétées | 21 |
| Setup | 2/2 ✅ |
| Fondation | 2/2 ✅ |
| US1 (P1) | 7/7 ✅ |
| US2 (P2) | 3/3 ✅ |
| US3 (P3) | 3/3 ✅ |
| Polish | 4/4 ✅ |

## Statut

**✅ IMPLÉMENTATION TERMINÉE**
