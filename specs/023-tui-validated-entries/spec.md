# Feature Specification: TUI Enriched Entries Tab

**Feature Branch**: `023-tui-validated-entries`
**Created**: 2025-12-13
**Status**: Draft
**Input**: User description: "Ajouter un onglet Validees dans la TUI pour separer les Sources (sites web/domaines) des Entrees enrichies (articles valides). Actuellement la TUI confond les deux concepts dans le meme onglet Sources."

## Clarifications

### Session 2025-12-13

- Q: Nom de l'onglet - "Validees" vs autre nom refletant validated + proposed ? → A: **Enrichies** (reflète mieux le contenu: toutes les entrées avec métadonnées IA)
- Q: Tri par defaut des entrees dans l'onglet Enrichies ? → A: **Par statut** (proposed en premier, puis validated) - met en avant les actions requises
- Q: Comportement apres rejet d'une entree "proposed" ? → A: **Revenir a "none"** - disparait de l'onglet, peut etre re-enrichie plus tard
- Q: Raccourci clavier pour l'onglet Enrichies ? → A: **`n`** (car `e` est deja pris par Quick Edit)

## Contexte du Probleme

Actuellement, la TUI Rekall presente une confusion conceptuelle dans l'onglet "Sources" :

| Concept actuel | Ce que c'est vraiment | Exemple |
|----------------|----------------------|---------|
| **Source** (affiche) | Site web / Domaine | edpb.europa.eu |
| **Entree enrichie** (manquant) | Article/page specifique avec metadonnees IA | edpb.europa.eu/guidelines/2024/... |

L'enrichissement via `rekall_enrich_source` ajoute des metadonnees (`ai_type`, `ai_tags`, `ai_summary`) mais ces donnees enrichies ne sont pas visibles distinctement dans la TUI.

## User Scenarios & Testing

### User Story 1 - Consulter les entrees enrichies (Priority: P1)

En tant qu'utilisateur de Rekall, je veux voir un onglet "Enrichies" distinct qui affiche les entrees enrichies par l'IA (validated et proposed), afin de distinguer clairement les domaines (Sources) des contenus enrichis.

**Why this priority**: C'est la demande principale - rendre visible la separation conceptuelle entre sites et contenus enrichis.

**Independent Test**: L'utilisateur peut ouvrir la TUI, naviguer vers l'onglet "Enrichies" et voir la liste des entrees avec leurs metadonnees IA (type, tags, summary).

**Acceptance Scenarios**:

1. **Given** la TUI est ouverte, **When** l'utilisateur appuie sur `n` ou clique sur l'onglet "Enrichies", **Then** il voit une liste des entrees avec `enrichment_status IN ('validated', 'proposed')`
2. **Given** l'onglet "Enrichies" est actif, **When** l'utilisateur selectionne une entree, **Then** le panneau de detail affiche : ai_type, ai_tags, ai_summary, confidence score, enrichment_status

---

### User Story 2 - Voir les entrees en attente de validation (Priority: P2)

En tant qu'utilisateur, je veux distinguer les entrees "proposed" (en attente de validation humaine) des entrees "validated" (auto-validees), afin de savoir ce qui necessite mon attention.

**Why this priority**: Complete P1 en gerant le workflow de validation humaine.

**Independent Test**: L'utilisateur voit un indicateur visuel clair distinguant les entrees validees des entrees en attente.

**Acceptance Scenarios**:

1. **Given** l'onglet "Enrichies" affiche des entrees, **When** une entree a `enrichment_status = 'proposed'`, **Then** elle est affichee avec un indicateur distinct (ex: icone horloge ou couleur differente)
2. **Given** une entree est en statut "proposed", **When** l'utilisateur la selectionne et appuie sur une touche d'action, **Then** il peut valider, modifier ou rejeter l'enrichissement

---

### User Story 3 - Navigation fluide entre onglets (Priority: P3)

En tant qu'utilisateur, je veux naviguer rapidement entre Sources, Enrichies, Inbox et Staging avec des raccourcis clavier coherents.

**Why this priority**: Ameliore l'ergonomie generale de la TUI.

**Independent Test**: L'utilisateur peut naviguer entre tous les onglets avec des raccourcis clavier sans utiliser la souris.

**Acceptance Scenarios**:

1. **Given** la TUI est ouverte sur n'importe quel onglet, **When** l'utilisateur appuie sur `n`, **Then** l'onglet "Enrichies" devient actif
2. **Given** le nouvel onglet est ajoute, **When** l'utilisateur consulte l'aide (`?`), **Then** le raccourci `n` pour "Enrichies" est documente

---

### Edge Cases

- Que se passe-t-il si aucune entree n'est enrichie ? Afficher un message "Aucune entree enrichie. Utilisez rekall_enrich_source pour commencer."
- Que se passe-t-il si toutes les entrees sont "proposed" sans aucune "validated" ? Afficher les deux types avec distinction visuelle claire
- Comment gerer la pagination si des centaines d'entrees sont enrichies ? Utiliser le meme systeme de pagination que l'onglet Sources existant

## Requirements

### Functional Requirements

- **FR-001**: Le systeme DOIT afficher un nouvel onglet "Enrichies" dans la TUI, positionne entre "Sources" et "Inbox"
- **FR-002**: L'onglet "Enrichies" DOIT lister les entrees ayant des metadonnees d'enrichissement (`enrichment_status IN ('validated', 'proposed')`)
- **FR-003**: Chaque entree dans l'onglet DOIT afficher : domaine, ai_type, ai_confidence, enrichment_status, ai_tags (tronques)
- **FR-004**: Le panneau de detail DOIT afficher le ai_summary complet quand une entree est selectionnee
- **FR-005**: Le systeme DOIT permettre la validation/rejet des entrees "proposed" via raccourci clavier
- **FR-006**: Le systeme DOIT mettre a jour le compteur de l'onglet "Enrichies (N)" en temps reel
- **FR-007**: Le raccourci clavier `n` DOIT activer l'onglet "Enrichies"
- **FR-008**: Les entrees DOIVENT etre triees par statut par defaut (proposed en premier, puis validated)
- **FR-009**: Le rejet d'une entree "proposed" DOIT remettre son enrichment_status a "none" (disparait de l'onglet Enrichies)

### Key Entities

- **Source (existant)**: Represente un domaine/site web (ex: edpb.europa.eu) - reste dans l'onglet "Sources"
- **Enriched Entry (nouveau concept visible)**: Represente une source avec metadonnees IA (ai_type, ai_tags, ai_summary, ai_confidence, enrichment_status) - visible dans l'onglet "Enrichies"

## Success Criteria

### Measurable Outcomes

- **SC-001**: L'utilisateur peut distinguer visuellement les sources (domaines) des entrees enrichies en moins de 5 secondes
- **SC-002**: 100% des entrees avec `enrichment_status != 'none'` apparaissent dans l'onglet "Enrichies"
- **SC-003**: L'utilisateur peut valider une entree "proposed" en 3 clics/touches maximum
- **SC-004**: La navigation entre les 4 onglets (Sources, Enrichies, Inbox, Staging) prend moins de 1 seconde

## Assumptions

- Le modele de donnees existant (`sources` table avec colonnes ai_*) reste inchange
- Le framework Textual utilise par la TUI supporte l'ajout dynamique d'onglets (TabbedContent)
- Les raccourcis clavier existants (s, i, g) restent inchanges, seul `n` est ajoute pour "Enrichies"

## Research Findings

Sources consultees :
- [Textual TabbedContent Widget](https://www.blog.pythonlibrary.org/2023/04/25/textual-101-using-the-tabbedcontent-widget/) - Pattern d'implementation des onglets
- [8 TUI Patterns](https://medium.com/@Nexumo_/8-tui-patterns-to-turn-python-scripts-into-apps-ce6f964d3b6f) - Best practices pour TUI modernes
- [Textual Anatomy](https://textual.textualize.io/blog/2024/09/15/anatomy-of-a-textual-user-interface/) - Architecture recommandee

Aucun red flag identifie - l'ajout d'un onglet est une operation standard dans Textual.
