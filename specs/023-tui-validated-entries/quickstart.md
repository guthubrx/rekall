# Quickstart - 023 TUI Enriched Entries Tab

**Date**: 2025-12-13
**Branche**: 023-tui-validated-entries
**Worktree**: `.worktrees/023-tui-validated-entries/`

## Contexte Rapide

Cette feature ajoute un 4eme onglet "Enrichies" dans la TUI Rekall (UnifiedSourcesApp) pour afficher les sources ayant des metadonnees d'enrichissement IA (validated + proposed).

## Fichiers a Modifier

| Fichier | Modifications |
|---------|---------------|
| `rekall/tui_main.py` | UnifiedSourcesApp: ajouter onglet, table, actions |
| `rekall/db.py` | Nouvelles methodes: get_enriched_sources, validate/reject |

## Demarrage Rapide

```bash
# 1. Aller dans le worktree
cd .worktrees/023-tui-validated-entries

# 2. Installer dependances (si necessaire)
uv sync

# 3. Lancer la TUI pour voir l'etat actuel
uv run rekall

# 4. Verifier les sources enrichies existantes
uv run python -c "
from rekall.db import get_db
db = get_db()
sources = db.conn.execute('''
    SELECT domain, enrichment_status, ai_type
    FROM sources
    WHERE enrichment_status != 'none'
    LIMIT 10
''').fetchall()
for s in sources:
    print(s)
"
```

## Points d'Entree Code

### UnifiedSourcesApp (tui_main.py:8555)

```python
class UnifiedSourcesApp(SortableTableMixin, App):
    # Ligne ~8796: BINDINGS - ajouter Binding("n", "tab_enriched", ...)
    # Ligne ~8829: compose() - ajouter TabPane pour enriched
    # Ligne ~8919: _load_all_data() - charger enriched_entries
    # Ligne ~9102: _switch_to_tab() - gerer "enriched"
    # Ligne ~9155: _update_detail_panel() - afficher details enriched
```

### Pattern a Suivre

Copier le pattern de l'onglet Staging :
1. `_setup_staging_table()` → `_setup_enriched_table()`
2. `_populate_staging_table()` → `_populate_enriched_table()`
3. Actions staging → Actions enriched (validate/reject)

## Tests Manuels

```bash
# 1. Lancer la TUI
uv run rekall

# 2. Verifier que l'onglet "Enrichies" apparait
# 3. Appuyer sur 'n' pour naviguer vers l'onglet
# 4. Verifier que les sources enrichies s'affichent
# 5. Selectionner une entree 'proposed'
# 6. Valider avec 'v' ou via le menu actions
```

## Donnees de Test

Si aucune source enrichie n'existe, en creer via MCP :

```python
# Via Claude Code
rekall_enrich_source(
    source_id="...",
    ai_type="documentation",
    ai_tags=["test", "example"],
    ai_summary="Test enrichment summary",
    ai_confidence=0.85,
    auto_validate=False  # Pour avoir du 'proposed'
)
```

## Checklist Implementation

- [ ] Ajouter `enriched_entries: list` dans `__init__`
- [ ] Ajouter `selected_enriched` dans `__init__`
- [ ] Ajouter `Binding("n", "tab_enriched", ...)` dans BINDINGS
- [ ] Ajouter TabPane "Enrichies" dans `compose()`
- [ ] Implementer `_setup_enriched_table()`
- [ ] Implementer `_populate_enriched_table()`
- [ ] Ajouter `action_tab_enriched()`
- [ ] Modifier `_switch_to_tab()` pour "enriched"
- [ ] Modifier `_load_all_data()` pour charger enriched
- [ ] Modifier `_update_detail_panel()` pour enriched
- [ ] Modifier `_update_stats()` pour compter enriched
- [ ] Ajouter `db.get_enriched_sources()` dans db.py
- [ ] Ajouter `db.validate_enrichment()` dans db.py
- [ ] Ajouter `db.reject_enrichment()` dans db.py
- [ ] Ajouter actions validate/reject dans menu
- [ ] Tests unitaires
- [ ] Test manuel complet
