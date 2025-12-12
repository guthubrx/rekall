# Feature Specification: Base de Connaissances Menu

**Feature Branch**: `011-knowledge-base-menu`
**Created**: 2025-12-11
**Status**: Draft
**Input**: Créer une section "Base de connaissances" dans le menu TUI regroupant Parcourir, Rechercher et Sources documentaires

## Contexte

Actuellement, le menu principal de la TUI est structuré ainsi :
- **GÉNÉRAL** : Langue, Configuration, Parcourir
- **RECHERCHE** : Fichiers research
- **SOURCES** : Sources documentaires
- **DONNÉES** : Export/Import

Cette organisation disperse les fonctionnalités liées à la gestion des connaissances (entrées, recherche, sources). L'utilisateur doit naviguer dans plusieurs sections pour accéder à des fonctionnalités conceptuellement liées.

## Objectif

Créer une section unifiée **"BASE DE CONNAISSANCES"** qui regroupe :
1. Parcourir les entrées (browse)
2. Rechercher dans les entrées (search - nouvelle action)
3. Sources documentaires (sources)

Cela améliore la cohérence conceptuelle et réduit la navigation.

---

## User Scenarios & Testing

### User Story 1 - Navigation unifiée vers les connaissances (Priority: P1)

En tant qu'utilisateur de Rekall, je veux accéder à toutes les fonctionnalités de gestion des connaissances depuis une seule section du menu, afin de naviguer plus intuitivement.

**Why this priority**: C'est l'objectif principal de la feature - regrouper les entrées existantes.

**Independent Test**: Lancer `rekall tui`, vérifier que la section "BASE DE CONNAISSANCES" existe avec les 3 sous-entrées.

**Acceptance Scenarios**:

1. **Given** le menu principal affiché, **When** je regarde les sections, **Then** je vois une section "BASE DE CONNAISSANCES"
2. **Given** la section "BASE DE CONNAISSANCES", **When** je la consulte, **Then** je vois "Parcourir", "Rechercher", "Sources"
3. **Given** je sélectionne "Parcourir", **When** l'action s'exécute, **Then** l'écran de navigation des entrées s'affiche
4. **Given** je sélectionne "Sources", **When** l'action s'exécute, **Then** le dashboard Sources s'affiche

---

### User Story 2 - Recherche intégrée (Priority: P2)

En tant qu'utilisateur, je veux pouvoir lancer une recherche directement depuis le menu "Base de connaissances", sans passer par Browse puis Search.

**Why this priority**: Améliore l'accès à une fonctionnalité fréquemment utilisée.

**Independent Test**: Sélectionner "Rechercher" depuis le menu, entrer un terme, voir les résultats.

**Acceptance Scenarios**:

1. **Given** la section "BASE DE CONNAISSANCES", **When** je sélectionne "Rechercher", **Then** une invite de recherche s'affiche
2. **Given** l'invite de recherche, **When** j'entre un terme et valide, **Then** les résultats correspondants s'affichent

---

### Edge Cases

- Menu vide si base de données non initialisée → Afficher message d'avertissement
- Aucun résultat de recherche → Afficher "Aucun résultat trouvé"

---

## Requirements

### Functional Requirements

- **FR-001**: Le menu principal DOIT contenir une section "BASE DE CONNAISSANCES"
- **FR-002**: La section DOIT regrouper les actions : Parcourir, Rechercher, Sources
- **FR-003**: L'action "Parcourir" DOIT afficher l'écran de navigation des entrées (existant)
- **FR-004**: L'action "Rechercher" DOIT afficher une invite de saisie puis les résultats
- **FR-005**: L'action "Sources" DOIT afficher le dashboard Sources (existant)
- **FR-006**: Les sections "RECHERCHE" et "SOURCES" actuelles DOIVENT être supprimées du menu
- **FR-007**: La section "GÉNÉRAL" DOIT conserver uniquement Langue et Configuration

### Structure du menu résultant

```
┌─────────────────────────────────────────────┐
│ GÉNÉRAL                                     │
│   🌐 Langue                                 │
│   ⚙  Configuration & Maintenance           │
│                                             │
│ BASE DE CONNAISSANCES                       │
│   📚 Parcourir les entrées                  │
│   🔍 Rechercher                             │
│   📖 Sources documentaires                  │
│                                             │
│ DONNÉES                                     │
│   📤 Export / Import                        │
│                                             │
│ ❌ Quitter                                  │
└─────────────────────────────────────────────┘
```

---

## Success Criteria

### Measurable Outcomes

- **SC-001**: L'utilisateur accède aux entrées, recherche et sources en maximum 2 clics depuis le menu principal
- **SC-002**: Le menu principal contient 4 sections au lieu de 5 (réduction de la complexité)
- **SC-003**: 100% des fonctionnalités existantes restent accessibles après réorganisation

---

## Assumptions

- La fonction `action_search()` dans `tui.py` existe déjà (prompt + résultats)
- Les traductions `menu.browse`, `menu.sources` existent déjà
- Nouvelle traduction à ajouter : `menu.knowledge_base` pour le titre de section

---

## Out of Scope

- Modification du contenu des écrans Browse ou Sources
- Ajout de nouvelles fonctionnalités de recherche
- Modification de l'ordre des résultats de recherche
