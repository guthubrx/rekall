# Implementation Plan - 023 TUI Enriched Entries Tab

**Date**: 2025-12-13
**Branche**: 023-tui-validated-entries
**Status**: Ready for Implementation

## Technical Context

| Element | Value |
|---------|-------|
| **Framework TUI** | Textual (Python) |
| **Fichier principal** | `rekall/tui_main.py` (~387KB) |
| **Classe cible** | `UnifiedSourcesApp` (ligne 8555) |
| **Base de donnees** | SQLite (`rekall/db.py`) |
| **Modele** | `Source` existant avec colonnes ai_* |

## Constitution Check

| Article | Status | Notes |
|---------|--------|-------|
| I. Langue Francaise | ✅ | Documentation en francais |
| III. Process SpecKit | ✅ | spec → plan → tasks → implement |
| VII. ADR | N/A | Pas de decision architecturale majeure |
| XV. Test-Before-Next | ✅ | Tests definis dans contracts |
| XVI. Worktree | ✅ | Worktree cree `.worktrees/023-tui-validated-entries/` |
| XVII. DevKMS | ✅ | Patterns documentes si necessaire |

## Architecture Decision

**Decision**: Etendre `UnifiedSourcesApp` existante avec un 4eme onglet

**Rationale**:
- Coherence avec l'architecture 3-onglets existante
- Reutilisation du panneau de detail partage
- Reutilisation du systeme de tri (SortableTableMixin)
- Pas de nouvelle classe necessaire

**Alternative rejetee**: Creer une nouvelle App separee
- Rejet: Duplication de code, UX fragmentee

## Implementation Phases

### Phase 1: Database Layer (db.py)

**Objectif**: Ajouter les methodes d'acces aux sources enrichies

**Fichier**: `rekall/db.py`

**Methodes a ajouter**:

```python
def get_enriched_sources(
    self,
    status: str | None = None,
    limit: int = 500
) -> list[Source]:
    """
    Recupere les sources avec enrichissement IA.

    Args:
        status: Filtrer par 'proposed' ou 'validated' (None = tous)
        limit: Nombre max de resultats

    Returns:
        Liste de Source triees par statut puis confidence
    """
    pass

def validate_enrichment(self, source_id: str) -> bool:
    """
    Valide une source proposed -> validated.
    Met a jour enrichment_validated_at.
    """
    pass

def reject_enrichment(self, source_id: str) -> bool:
    """
    Rejette une source proposed -> none.
    Garde les metadonnees IA pour re-enrichissement futur.
    """
    pass

def count_enriched_sources(self) -> dict:
    """
    Retourne le compte des sources enrichies.
    Returns: {'total': N, 'proposed': N, 'validated': N}
    """
    pass
```

**LOC estimees**: ~80 lignes

---

### Phase 2: TUI Data & State (tui_main.py)

**Objectif**: Ajouter les structures de donnees pour l'onglet

**Modifications dans `UnifiedSourcesApp.__init__`**:

```python
# Ajouter apres staging_entries
self.enriched_entries: list[Source] = []
self.selected_enriched: Source | None = None
```

**Modifications dans `_load_all_data`**:

```python
# Ajouter apres staging
self.enriched_entries = list(self.db.get_enriched_sources(limit=500))
```

**LOC estimees**: ~15 lignes

---

### Phase 3: TUI Tab & Table (tui_main.py)

**Objectif**: Ajouter l'onglet et la table dans l'interface

**Modifications dans `compose()`** (apres tab-sources, avant tab-inbox):

```python
with TabPane("Enrichies (0)", id="tab-enriched"):
    yield DataTable(id="enriched-table", classes="sources-table")
```

**Nouvelles methodes**:

```python
def _setup_enriched_table(self) -> None:
    """Configure les colonnes de la table Enrichies."""
    # Domain, Type, Confidence, Status, Tags, Validated

def _populate_enriched_table(self) -> None:
    """Remplit la table avec enriched_entries."""
    # Format rows avec indicateurs visuels
```

**Modifications dans `on_mount`**:

```python
self._setup_enriched_table()
```

**LOC estimees**: ~60 lignes

---

### Phase 4: TUI Navigation (tui_main.py)

**Objectif**: Ajouter la navigation clavier et le switch d'onglet

**Modifications dans `BINDINGS`**:

```python
Binding("n", "tab_enriched", "Enrichies", show=True),
```

**Nouvelles methodes**:

```python
def action_tab_enriched(self) -> None:
    """Switch vers l'onglet Enrichies."""
    self._switch_to_tab("enriched")
```

**Modifications dans `_switch_to_tab`**:

```python
elif tab == "enriched":
    self.entries = self.enriched_entries
    self.query_one("#tabs", TabbedContent).active = "tab-enriched"
    if self.enriched_entries:
        self.selected_enriched = self.enriched_entries[0]
```

**LOC estimees**: ~25 lignes

---

### Phase 5: TUI Detail Panel (tui_main.py)

**Objectif**: Afficher les details d'enrichissement

**Modifications dans `_update_detail_panel`**:

```python
elif self.current_tab == "enriched" and self.selected_enriched:
    source = self.selected_enriched
    title_widget.update(f"[bold]{source.domain}[/bold]")

    lines = [
        f"[cyan]Type:[/cyan] {source.ai_type}",
        f"[cyan]Confidence:[/cyan] {int(source.ai_confidence * 100)}%",
        f"[cyan]Status:[/cyan] {source.enrichment_status}",
        "",
        f"[cyan]Tags:[/cyan] {', '.join(source.ai_tags or [])}",
        "",
        f"[cyan]Summary:[/cyan]",
        source.ai_summary or "(none)",
    ]
    meta_widget.update("\n".join(lines))
```

**LOC estimees**: ~30 lignes

---

### Phase 6: TUI Actions (tui_main.py)

**Objectif**: Implémenter les actions validate/reject

**Modifications dans `action_show_actions`**:

```python
elif self.current_tab == "enriched" and self.selected_enriched:
    actions = self._get_enriched_actions()
```

**Nouvelles methodes**:

```python
def _get_enriched_actions(self) -> list:
    """Retourne les actions pour l'onglet Enrichies."""
    source = self.selected_enriched
    actions = [("view", "📋 View details")]

    if source.enrichment_status == "proposed":
        actions.extend([
            ("validate", "✓ Validate"),
            ("reject", "✗ Reject"),
        ])

    return actions

def _action_validate_enrichment(self) -> None:
    """Valide l'enrichissement selectionne."""
    if self.db.validate_enrichment(self.selected_enriched.id):
        self.show_left_notify("✓ Enrichment validated")
        self._refresh_enriched()

def _action_reject_enrichment(self) -> None:
    """Rejette l'enrichissement selectionne."""
    if self.db.reject_enrichment(self.selected_enriched.id):
        self.show_left_notify("✗ Enrichment rejected")
        self._refresh_enriched()

def _refresh_enriched(self) -> None:
    """Rafraichit les donnees et la table enriched."""
    self.enriched_entries = list(self.db.get_enriched_sources(limit=500))
    self._populate_enriched_table()
    self._update_stats()
```

**LOC estimees**: ~50 lignes

---

### Phase 7: TUI Stats & Filter (tui_main.py)

**Objectif**: Mettre a jour les compteurs et le filtrage

**Modifications dans `_update_stats`**:

```python
# Ajouter le compteur Enrichies
enriched_count = len(self.enriched_entries)
# Mettre a jour le label du tab
```

**Modifications dans `_apply_filter`**:

```python
elif self.current_tab == "enriched":
    self.enriched_entries = [
        s for s in self.db.get_enriched_sources(limit=500)
        if query in s.domain.lower() or
           query in (s.ai_type or "").lower() or
           any(query in tag.lower() for tag in (s.ai_tags or []))
    ]
    self._populate_enriched_table()
```

**LOC estimees**: ~25 lignes

---

### Phase 8: Tests

**Objectif**: Tests unitaires et d'integration

**Fichier**: `tests/test_tui_enriched.py`

```python
def test_enriched_tab_exists():
    """L'onglet Enrichies existe dans la TUI."""

def test_enriched_keyboard_binding():
    """Le raccourci 'n' active l'onglet."""

def test_enriched_shows_proposed_first():
    """Les entrees proposed sont avant validated."""

def test_validate_action():
    """L'action validate change proposed -> validated."""

def test_reject_action():
    """L'action reject change proposed -> none."""

def test_enriched_detail_panel():
    """Le panneau affiche ai_summary et ai_tags."""

def test_enriched_empty_state():
    """Message affiche si aucune source enrichie."""
```

**LOC estimees**: ~100 lignes

---

## Summary

| Phase | Description | LOC | Fichier |
|-------|-------------|-----|---------|
| 1 | Database Layer | ~80 | db.py |
| 2 | TUI Data & State | ~15 | tui_main.py |
| 3 | TUI Tab & Table | ~60 | tui_main.py |
| 4 | TUI Navigation | ~25 | tui_main.py |
| 5 | TUI Detail Panel | ~30 | tui_main.py |
| 6 | TUI Actions | ~50 | tui_main.py |
| 7 | TUI Stats & Filter | ~25 | tui_main.py |
| 8 | Tests | ~100 | test_tui_enriched.py |
| **Total** | | **~385** | |

## Dependencies

```
Phase 1 (DB) ─┬─► Phase 2 (State) ─► Phase 3 (Tab)
              │
              └─► Phase 4 (Nav) ─► Phase 5 (Detail) ─► Phase 6 (Actions)
                                                      │
                                                      └─► Phase 7 (Stats)
                                                          │
                                                          └─► Phase 8 (Tests)
```

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Conflit raccourci `n` | Low | Low | Verifie: `n` est disponible |
| Performance 500+ entrees | Low | Low | Limite existante respectee |
| Regression autres onglets | Medium | Medium | Tests existants + nouveaux |

## Artifacts Generated

- [x] `research.md` - Decisions techniques
- [x] `data-model.md` - Schema et requetes
- [x] `contracts/tui-enriched-tab.md` - Interface contrat
- [x] `quickstart.md` - Guide demarrage rapide
- [x] `plan.md` - Ce document

## Next Step

```
/speckit.tasks
```

Pour generer les taches detaillees basees sur ce plan.
