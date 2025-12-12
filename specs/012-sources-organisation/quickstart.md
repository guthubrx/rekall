# Quickstart: Sources Organisation

**Feature**: 012-sources-organisation
**Temps estimé**: 2-3 heures

## Prérequis

- Python 3.10+
- Rekall installé (`pip install -e .`)
- Base de données initialisée avec sources

## Test de Validation Rapide

### 1. Tags Multiples

```bash
# Lancer TUI
rekall tui

# Navigation
BASE DE CONNAISSANCES → Sources documentaires → Ajouter une source

# Test : Créer source avec tags multiples
URL: example.com
Tags: test, python, demo

# Vérifier
Sources documentaires → Parcourir par tag
# Doit afficher : test (1), python (1), demo (1)
```

### 2. Édition Tags

```bash
# Dans TUI
Sources documentaires → [sélectionner une source] → Modifier les tags

# Ajouter un tag
# Retirer un tag
# Vérifier les changements
```

### 3. Filtres Multi-critères

```bash
# Dans TUI
Sources documentaires → Recherche avancée

# Configurer filtres :
- Tags : python, go (sélection multiple)
- Score : 30-100
- Statut : active, seed

# Appliquer → Voir résultats filtrés
```

### 4. Vues Sauvegardées

```bash
# Après avoir configuré un filtre
→ Sauvegarder cette vue
Nom : "Sources Python actives"

# Vérifier
Sources documentaires → Mes vues
→ Sélectionner "Sources Python actives"
→ Filtre appliqué automatiquement
```

## Checklist Visuelle

### Tags
- [ ] Saisie tags séparés par virgule à la création
- [ ] Auto-complétion des tags existants
- [ ] Affichage tags dans fiche source
- [ ] Modification tags depuis fiche
- [ ] Liste tags avec compteurs
- [ ] Navigation : tag → sources

### Filtres
- [ ] Sélection multiple tags (OU)
- [ ] Plage score (min-max)
- [ ] Sélection statuts multiples
- [ ] Sélection rôles multiples
- [ ] Filtre fraîcheur (jours)
- [ ] Recherche texte
- [ ] Combinaison critères (ET)

### Vues
- [ ] Sauvegarde filtre actif
- [ ] Liste des vues
- [ ] Application d'une vue
- [ ] Suppression d'une vue

## Rollback

Si problème, restaurer depuis git :

```bash
git checkout -- rekall/db.py rekall/tui.py rekall/i18n.py rekall/models.py
```

## Commandes de Test

```bash
# Lint
ruff check rekall/

# Tests
python -m pytest tests/ -v

# Import
python -c "from rekall.db import get_all_tags_with_counts"
```
