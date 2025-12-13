# Research Technique - 023 TUI Enriched Entries Tab

**Date**: 2025-12-13
**Branche**: 023-tui-validated-entries

## Decisions Techniques

### 1. Raccourci Clavier pour l'Onglet Enrichies

**Decision**: Utiliser `n` au lieu de `e` pour l'onglet "Enrichies"

**Rationale**:
- Le raccourci `e` est deja utilise pour "Quick edit" dans UnifiedSourcesApp (ligne 8785)
- `n` est disponible et peut etre memorise comme "eNrichies" ou "Nouveau contenu"
- Alternative envisagee: `x` mais moins intuitif

**Alternatives considerees**:
- `e` - Deja pris par Quick edit
- `v` - Pourrait confliter avec "view" dans certains contextes
- `x` - Non intuitif
- `n` - Choisi car disponible et memorisable

### 2. Architecture d'Integration

**Decision**: Modifier `UnifiedSourcesApp` existante plutot que creer une nouvelle App

**Rationale**:
- Coherence avec l'architecture existante (3 onglets dans UnifiedSourcesApp)
- Reutilisation du panneau de detail partage
- Partage du systeme de filtrage et tri (SortableTableMixin)
- Pattern etabli : ajouter TabPane + DataTable + methods

**Fichiers a modifier**:
1. `rekall/tui_main.py` - UnifiedSourcesApp (ligne 8555+)
2. `rekall/db.py` - Methode pour recuperer sources enrichies
3. Aucun nouveau modele necessaire (utilise `Source` existant avec colonnes ai_*)

### 3. Source de Donnees

**Decision**: Filtrer la table `sources` existante sur `enrichment_status != 'none'`

**Rationale**:
- Le modele Source contient deja les colonnes d'enrichissement :
  - `enrichment_status` (none/proposed/validated)
  - `ai_type`, `ai_tags`, `ai_summary`, `ai_confidence`
- Pas besoin de nouvelle table
- Coherent avec la spec : "Le modele de donnees existant reste inchange"

**Requete SQL**:
```sql
SELECT * FROM sources
WHERE enrichment_status IN ('validated', 'proposed')
ORDER BY
  CASE enrichment_status
    WHEN 'proposed' THEN 0
    WHEN 'validated' THEN 1
  END,
  ai_confidence DESC
```

### 4. Actions dans l'Onglet Enrichies

**Decision**: Implementer 3 actions principales

| Action | Raccourci | Description |
|--------|-----------|-------------|
| Valider | `v` | Passe proposed → validated |
| Rejeter | `r` | Passe → none (disparait de l'onglet) |
| Voir details | `enter` | Affiche menu actions complet |

**Rationale**:
- Aligne sur FR-005 et FR-009 de la spec
- Workflow simple : voir → decider → agir

### 5. Colonnes de la Table Enrichies

**Decision**: 6 colonnes adaptees aux metadonnees IA

| Colonne | Width | Key | Source |
|---------|-------|-----|--------|
| domain | 22 | domain | source.domain |
| ai_type | 12 | ai_type | source.ai_type |
| confidence | 8 | confidence | source.ai_confidence (%) |
| status | 10 | status | enrichment_status (icone) |
| ai_tags | 25 | tags | source.ai_tags (tronques) |
| validated_at | 12 | date | source.enrichment_validated_at |

**Indicateurs visuels**:
- proposed: ⏳ (orange)
- validated: ✓ (vert)

## Sources Techniques

- [Textual TabbedContent](https://textual.textualize.io/widgets/tabbed_content/) - Documentation officielle
- Code existant `UnifiedSourcesApp` (tui_main.py:8555) - Pattern de reference
- [Textual DataTable](https://textual.textualize.io/widgets/data_table/) - Guide colonnes

## Risques Identifies

| Risque | Probabilite | Impact | Mitigation |
|--------|-------------|--------|------------|
| Conflit raccourci | Faible | Moyen | Utiliser `n` au lieu de `e` |
| Performance si beaucoup d'entrees | Faible | Faible | Limite 500 comme autres onglets |
| Confusion UX Sources/Enrichies | Moyen | Moyen | Labels clairs + indicateurs visuels |
