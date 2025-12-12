# Plan d'Implémentation : Suppression d'Entrée depuis Browse

**Branche**: `008-browse-delete-entry` | **Date**: 2025-12-10 | **Spec**: [spec.md](./spec.md)
**Input**: Spécification fonctionnelle validée

## Résumé

Remplacer le système actuel de confirmation de suppression (qui quitte l'écran Browse vers `SimpleMenuApp`) par un overlay intégré centré avec fond transparent. L'overlay affichera le nombre de liens impactés et supportera les raccourcis clavier (y/n/Escape).

## Contexte Technique

**Langage/Version**: Python 3.9+
**Dépendances Principales**: Textual >=0.89.0, typer, rich
**Stockage**: SQLite (rekall.db) - CASCADE constraints en place
**Testing**: pytest avec tests unitaires et intégration TUI
**Plateforme Cible**: CLI cross-platform (macOS, Linux, Windows)
**Type de Projet**: Single project (CLI + TUI)
**Objectifs Performance**: Overlay affiché en <100ms après touche 'd'
**Contraintes**: Pas de background visible (transparent), centrage V+H

## Vérification Constitution

*GATE: Doit passer avant Phase 0. Re-vérifier après Phase 1.*

| Article | Statut | Notes |
|---------|--------|-------|
| I. Langue Française | ✅ | Documentation en français |
| II. Agent Co-Pilote | ✅ | Pas d'idéation non sollicitée |
| III. Processus SpecKit | ✅ | /speckit.specify → /speckit.plan → /speckit.tasks |
| IV. Disjoncteur | N/A | Pas de débogage en cours |
| V. Anti Scope-Creep | ✅ | Feature isolée et bornée |
| VII. ADR | N/A | Pas de décision architecturale majeure |

**Résultat**: ✅ Tous gates passent - pas de violation à justifier.

## Structure Projet

### Documentation (cette feature)

```text
specs/008-browse-delete-entry/
├── spec.md              # Spécification fonctionnelle
├── plan.md              # Ce fichier
├── research.md          # N/A (pas de recherche nécessaire)
├── data-model.md        # N/A (utilise modèles existants)
└── tasks.md             # À générer via /speckit.tasks
```

### Code Source (modifications)

```text
rekall/
├── tui.py               # MODIFIER: BrowseApp + DeleteConfirmOverlay
├── i18n.py              # MODIFIER: Ajouter clés de traduction overlay
└── db.py                # EXISTANT: Méthode delete() déjà en place

tests/
└── test_tui_delete.py   # CRÉER: Tests overlay suppression
```

**Décision Structure**: Modification in-place du fichier `tui.py` existant. Pas de nouveau module nécessaire - l'overlay sera une classe interne à `BrowseApp`.

## Architecture Technique

### Composants Modifiés

```
┌─────────────────────────────────────────────────────────────┐
│                      BrowseApp                              │
│  ┌─────────────────┐  ┌───────────────────────────────────┐ │
│  │   DataTable     │  │      DeleteConfirmOverlay         │ │
│  │   (entries)     │  │  ┌─────────────────────────────┐  │ │
│  │                 │  │  │ "Supprimer [titre] ?"       │  │ │
│  │  [entry 1]      │  │  │ "5 liens seront supprimés"  │  │ │
│  │  [entry 2] ←────┼──┼──│ [Oui]  [Non]               │  │ │
│  │  [entry 3]      │  │  └─────────────────────────────┘  │ │
│  └─────────────────┘  │  layer: modal, align: center      │ │
│                       └───────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### Flux d'Exécution

```
1. User presse 'd' sur entrée sélectionnée
   │
   ▼
2. action_delete_entry() appelée
   │ - Vérifie self.selected_entry != None
   │ - Compte les liens (db.get_links)
   │
   ▼
3. Affiche DeleteConfirmOverlay
   │ - Titre: "Supprimer '{titre}' ?"
   │ - Warning: "N liens seront supprimés" (si N > 0)
   │ - Boutons: Oui / Non
   │
   ▼
4. User confirme (y / Enter sur Oui) ou annule (n / Escape / Enter sur Non)
   │
   ├─► Annulation: overlay.remove(), retour au browse
   │
   └─► Confirmation:
       │ - db.delete(entry_id)
       │ - show_toast("✓ Supprimé")
       │ - Refresh DataTable
       │ - Déplacer curseur vers entrée suivante
```

### CSS Overlay

```css
#delete-confirm-overlay {
    layer: modal;
    align: center middle;      /* Centré V+H */
    width: auto;
    max-width: 60;
    height: auto;
    padding: 1 2;
    background: transparent;   /* Fond transparent - REQUIS */
}

#delete-confirm-box {
    background: $surface;      /* Seul le contenu a un fond */
    border: thick $error;      /* Bordure rouge pour danger */
    padding: 1 2;
}
```

### Bindings Clavier

| Touche | Action | Scope |
|--------|--------|-------|
| `d` | Ouvre overlay | BrowseApp (existant) |
| `y` | Confirme suppression | DeleteConfirmOverlay |
| `n` | Annule | DeleteConfirmOverlay |
| `Escape` | Annule | DeleteConfirmOverlay |
| `Enter` | Action bouton sélectionné | DeleteConfirmOverlay |

## Traductions i18n

Nouvelles clés à ajouter dans `rekall/i18n.py`:

```python
# Section delete overlay
"delete.confirm_title": {
    "en": "Delete '{title}'?",
    "fr": "Supprimer '{title}' ?",
},
"delete.links_warning": {
    "en": "{count} link(s) will be removed",
    "fr": "{count} lien(s) seront supprimés",
},
"delete.confirm_yes": {
    "en": "Yes, delete",
    "fr": "Oui, supprimer",
},
"delete.confirm_no": {
    "en": "No, cancel",
    "fr": "Non, annuler",
},
"delete.success": {
    "en": "Entry deleted",
    "fr": "Entrée supprimée",
},
"delete.error": {
    "en": "Deletion failed",
    "fr": "Échec de la suppression",
},
```

## Méthode DB Existante

La méthode `db.delete()` est déjà implémentée (`db.py:589-597`):

```python
def delete(self, entry_id: str) -> None:
    """Delete an entry. Tags deleted by CASCADE, FTS by trigger."""
    self.conn.execute("DELETE FROM entries WHERE id = ?", (entry_id,))
    self.conn.commit()
```

Les contraintes CASCADE suppriment automatiquement:
- `tags` (entry_id FK)
- `links` (source_id et target_id FK)
- `embeddings` (entry_id FK)
- `context_keywords` (entry_id FK)

Le trigger `TRIGGER_DELETE` nettoie l'index FTS.

## Méthode pour Compter les Liens

Nouvelle méthode à ajouter dans `db.py`:

```python
def count_links(self, entry_id: str) -> int:
    """Count total links for an entry (incoming + outgoing)."""
    cursor = self.conn.execute(
        "SELECT COUNT(*) FROM links WHERE source_id = ? OR target_id = ?",
        (entry_id, entry_id),
    )
    return cursor.fetchone()[0]
```

## Tests

### Tests Unitaires

```python
# tests/test_tui_delete.py

def test_delete_overlay_appears_on_d_key():
    """Pressing 'd' shows confirmation overlay."""

def test_delete_overlay_shows_link_count():
    """Overlay displays correct link count for linked entries."""

def test_delete_confirms_with_y_key():
    """Pressing 'y' deletes entry and closes overlay."""

def test_delete_cancels_with_n_key():
    """Pressing 'n' closes overlay without deletion."""

def test_delete_cancels_with_escape():
    """Pressing 'Escape' closes overlay without deletion."""

def test_delete_refreshes_list():
    """After deletion, entry list is refreshed."""

def test_delete_moves_cursor_to_next():
    """After deletion, cursor moves to next entry."""

def test_delete_last_entry_shows_empty_message():
    """Deleting last entry shows 'no entries' message."""
```

### Tests Intégration DB

```python
def test_delete_cascades_links():
    """Deleting entry removes all associated links."""

def test_delete_cascades_embeddings():
    """Deleting entry removes all associated embeddings."""

def test_delete_updates_fts():
    """Deleting entry removes FTS index entry."""
```

## Estimation

| Tâche | Complexité | LOC estimées |
|-------|------------|--------------|
| DeleteConfirmOverlay widget | Moyenne | ~80 |
| Modification action_delete_entry | Faible | ~20 |
| CSS overlay | Faible | ~15 |
| Traductions i18n | Faible | ~20 |
| count_links() dans db.py | Faible | ~8 |
| Tests unitaires | Moyenne | ~100 |
| **Total** | | **~243 LOC** |

## Risques et Mitigations

| Risque | Impact | Mitigation |
|--------|--------|------------|
| Overlay pas vraiment centré | UX | Tester avec différentes tailles terminal |
| Fond pas transparent | UX | CSS layer modal + background: transparent |
| Race condition refresh | Data | Refresh après commit confirmé |

## Prochaine Étape

Exécuter `/speckit.tasks` pour générer les tâches détaillées d'implémentation.
