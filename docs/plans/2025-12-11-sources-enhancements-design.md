# Design: Sources Enhancements

**Date**: 2025-12-11
**Status**: Validated
**Scope**: 4 features, ~2700 LOC total

## Context

Suite au brainstorming, amélioration des fonctionnalités sources dans la TUI Rekall.

**Priorités utilisateur (ordre décroissant) :**
1. Organisation
2. Découverte
3. Maintenance
4. Intégration

## Features Planifiées

### Feature 012: Sources Organisation

**Scope**: Tags multiples + Filtres multi-critères
**Effort**: ~600 LOC

#### Tags Multiples

- À l'ajout d'une source : champ tags (virgules), auto-complétion
- Édition depuis fiche source : ajouter/retirer tags
- Édition en vrac : sélection multiple → ajouter/retirer tag
- Navigation par tag : liste tags avec compteurs → sources

#### Filtres Multi-critères

Critères combinables :
- Tags (multi-select)
- Score (plage min-max)
- Statut (seed, promoted, active, dormant, inaccessible)
- Rôle (authority, hub, unclassified)
- Fraîcheur (< 7j, < 30j, < 90j, > 90j)
- Texte (recherche domaine + notes)

Fonctionnalités :
- Sauvegarder un filtre comme "Vue"
- Réappliquer une vue sauvegardée
- Tri par colonne dans les résultats

---

### Feature 013: Sources Découverte

**Scope**: Recommandations IA + Recherche web
**Effort**: ~800 LOC

#### Recommandations IA

- Suggestions à la création d'entrée (sources existantes pertinentes)
- Recommandations globales (analyse 10 dernières entrées)
- Enrichissement automatique (tags suggérés pour sources sans tags)
- Fallback sans IA : suggestions basées sur co-citations

#### Recherche Web

- Recherche par thème → 10 résultats
- Import rapide avec tags pré-remplis
- Filtrage par type (docs, tutoriels, blogs, Q&A)
- Pré-classification du rôle
- Détection doublons avant ajout

---

### Feature 014: Sources Maintenance

**Scope**: Audit qualité + Fusion de sources
**Effort**: ~500 LOC

#### Audit Qualité

Catégories :
- Sans tags (0 tags)
- Score faible (< 20)
- Non classifiées (role = unclassified)
- Jamais utilisées (usage = 0, > 30j)
- Doublons potentiels (même domaine)
- Inaccessibles (status = inaccessible)

Fonctionnalités :
- Rapport avec compteurs par catégorie
- Actions rapides (corriger, supprimer, ignorer)
- Score global de santé
- Notification au lancement si audit > 7j

#### Fusion de Sources

- Sélection source A (conserver) + source B (fusionner)
- Prévisualisation : score max, usage somme, tags union
- Réattribution des entrées liées
- Concaténation des notes

---

### Feature 015: Sources Intégration

**Scope**: Voir sources d'une entrée + Graphe de liens
**Effort**: ~800 LOC

#### Voir Sources d'une Entrée

- Section "Sources liées" dans fiche entrée
- Liste compacte avec scores
- Actions : ouvrir fiche, ajouter source, suggérer (IA)
- Badge compteur dans liste Browse

#### Graphe de Liens

**Option A - ASCII (terminal)**
- Graphe simplifié pour explorer les voisins
- Utile pour terminal pur

**Option B - HTML (navigateur)**
- Export HTML avec D3.js/vis.js
- Graphe interactif zoomable
- Filtrable par tag ou autour d'une source

---

## Architecture

### Séparation UI / Logique

Préparer une future interface web (React/TypeScript) :
- Logique métier dans `rekall/` (réutilisable)
- UI TUI dans fonctions `_*` de `tui.py`
- API JSON via CLI existante (`rekall sources ...`)

### Modèle de données

Tables existantes suffisantes :
- `sources` : colonnes déjà en place
- `source_themes` : relation N:N pour tags multiples
- `entry_sources` : lien entrées ↔ sources

Ajouts potentiels :
- Table `saved_filters` pour vues sauvegardées
- Table `audit_results` pour cache audit (optionnel)

---

## Plan d'Implémentation

| Ordre | Feature | Priorité | Phases |
|-------|---------|----------|--------|
| 1 | 012-sources-organisation | P1 | Tags, Filtres |
| 2 | 013-sources-decouverte | P2 | Reco IA, Recherche web |
| 3 | 014-sources-maintenance | P2 | Audit, Fusion |
| 4 | 015-sources-integration | P3 | Voir sources, Graphes |

**MVP** : Feature 012 (Organisation) livre de la valeur immédiate.

---

## Décisions

- **Pas de hiérarchie de tags** : tags flat + multiples suffisent (YAGNI)
- **Graphe HTML** : meilleure UX que ASCII pour graphes complexes
- **Découpage par domaine** : 4 features au lieu de 9 phases atomiques
