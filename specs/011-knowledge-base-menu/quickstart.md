# Quickstart: Base de Connaissances Menu

**Feature**: 011-knowledge-base-menu
**Temps estimé**: 15-30 minutes

## Prérequis

- Python 3.10+
- Rekall installé (`pip install -e .`)
- Base de données initialisée

## Étapes d'implémentation

### 1. Modifier le menu (`rekall/tui.py`)

Localiser `get_menu_items()` (~ligne 5794) et réorganiser :

```python
def get_menu_items():
    return [
        # Section 1: Général (sans browse)
        ("__section__", "GÉNÉRAL", ""),
        ("language", t("menu.language"), t("menu.language.desc")),
        ("config", t("menu.config"), t("menu.config.desc")),
        ("__spacer__", "", ""),

        # Section 2: Base de connaissances (NOUVELLE)
        ("__section__", t("menu.knowledge_base"), ""),
        ("browse", t("menu.browse"), t("menu.browse.desc")),
        ("search", t("menu.search"), t("menu.search.desc")),
        ("sources", t("menu.sources"), t("menu.sources.desc")),
        ("__spacer__", "", ""),

        # Section 3: Données
        ("__section__", "DONNÉES", ""),
        ("export", t("menu.export"), t("menu.export.desc")),
        ("__spacer__", "", ""),

        # Quitter
        ("quit", t("menu.quit"), t("menu.quit.desc")),
    ]
```

### 2. Ajouter l'action search (`rekall/tui.py`)

Localiser le dictionnaire `actions` (~ligne 5834) et ajouter :

```python
actions = {
    ...
    "search": self.action_search,
    ...
}
```

### 3. Ajouter les traductions (`rekall/i18n.py`)

```python
"menu.knowledge_base": "BASE DE CONNAISSANCES",
"menu.search": "Rechercher",
"menu.search.desc": "Rechercher dans les entrées",
```

## Vérification

### Test rapide

```bash
# Lint
ruff check rekall/tui.py rekall/i18n.py

# Import
python -c "from rekall.tui import get_menu_items; print(get_menu_items())"

# TUI
rekall tui
```

### Checklist visuelle

- [ ] Section "BASE DE CONNAISSANCES" visible
- [ ] Contient : Parcourir, Rechercher, Sources
- [ ] Section "RECHERCHE" supprimée
- [ ] Section "SOURCES" supprimée
- [ ] "Parcourir" retiré de "GÉNÉRAL"
- [ ] Toutes les actions fonctionnent

## Rollback

Si problème, restaurer `tui.py` depuis git :

```bash
git checkout -- rekall/tui.py rekall/i18n.py
```
