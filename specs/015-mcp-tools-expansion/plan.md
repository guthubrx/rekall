# Plan d'Implémentation : MCP Tools Expansion

**Branche** : `015-mcp-tools-expansion` | **Date** : 2025-12-12 | **Spec** : [spec.md](./spec.md)

## Résumé

Ajout de 8 nouveaux outils MCP pour compléter la couverture fonctionnelle de rekall :
- **P1** : `rekall_unlink`, `rekall_related`, `rekall_similar`, `rekall_sources_suggest`
- **P3** : `rekall_info`, `rekall_stale`, `rekall_generalize`, `rekall_sources_verify`

Toutes les fonctions sous-jacentes existent déjà dans `db.py`, `embeddings.py` et `link_rot.py`. Le travail consiste à créer les wrappers MCP dans `mcp_server.py`.

## Contexte Technique

**Langage/Version** : Python 3.11+
**Dépendances Principales** : mcp (SDK), sqlite3, httpx (link rot)
**Stockage** : SQLite (rekall.db)
**Tests** : pytest
**Plateforme Cible** : CLI cross-platform (macOS, Linux)
**Type de Projet** : Single (CLI package)
**Performance** : < 2s par outil (sauf sources_verify < 30s pour 10 URLs)
**Contraintes** : Dégradation gracieuse si embeddings non activés

## Constitution Check

✅ **Article III** : Feature suit le cycle SpecKit (specify → plan → tasks → implement)
✅ **Article VII** : Pas de décision architecturale majeure (extension du serveur MCP existant)
✅ **Article XV** : Tests obligatoires avant commit
✅ **Article XVI** : Travail dans branche dédiée

## Structure Projet

### Documentation (cette feature)

```text
specs/015-mcp-tools-expansion/
├── spec.md              # Spécification (créé)
├── plan.md              # Ce fichier
├── research.md          # Analyse des fonctions existantes
├── data-model.md        # N/A (pas de nouveau modèle)
├── contracts/           # Schémas MCP tools
│   └── mcp-tools.json   # InputSchema pour les 8 outils
└── tasks.md             # Tâches d'implémentation
```

### Code Source (à modifier)

```text
rekall/
├── mcp_server.py        # Fichier principal à étendre (+8 outils)
├── db.py                # Fonctions existantes (lecture seule)
├── embeddings.py        # find_similar() existant
└── link_rot.py          # verify_sources() existant

tests/
└── test_mcp_server.py   # Tests unitaires MCP (à créer/étendre)
```

**Décision Structure** : Extension in-place du fichier `mcp_server.py` existant. Pas de refactoring nécessaire.

## Complexité Tracking

Aucune violation de constitution détectée. Implémentation simple (wrappers vers fonctions existantes).

---

## Phase 0 : Research Technique

### Fonctions Existantes Identifiées

| Outil MCP | Fonction DB/Module | Signature |
|-----------|-------------------|-----------|
| `rekall_unlink` | `db.delete_link(source_id, target_id)` | Retourne bool |
| `rekall_related` | `db.get_related_entries(entry_id, depth)` | Retourne list[Entry] |
| `rekall_similar` | `embeddings.find_similar(entry_id, db, limit)` | Retourne list[(Entry, score)] |
| `rekall_sources_suggest` | `db.get_sources_by_theme()` + matching | À implémenter |
| `rekall_info` | `db.get_source_statistics()` + counts | Agrégation |
| `rekall_stale` | `db.get_stale_entries(days, limit)` | Retourne list[Entry] |
| `rekall_generalize` | CLI `generalize` logic | À wrapper |
| `rekall_sources_verify` | `link_rot.verify_sources(urls, limit)` | Retourne dict statuts |

### Décisions Techniques

| Décision | Choix | Rationale |
|----------|-------|-----------|
| Pattern MCP | Async handlers comme existants | Cohérence avec code actuel |
| Gestion erreurs | TextContent avec message explicite | Standard MCP SDK |
| Embeddings absents | Message gracieux (pas d'erreur) | UX agent |
| Timeout verify | 10s par URL via httpx | Éviter blocage |

---

## Phase 1 : Contracts MCP

### Schémas InputSchema

Voir `contracts/mcp-tools.json` pour les schémas JSON complets.

#### rekall_unlink

```json
{
  "type": "object",
  "properties": {
    "source_id": {"type": "string", "description": "ID de l'entrée source du lien"},
    "target_id": {"type": "string", "description": "ID de l'entrée cible du lien"}
  },
  "required": ["source_id", "target_id"]
}
```

#### rekall_related

```json
{
  "type": "object",
  "properties": {
    "entry_id": {"type": "string", "description": "ID de l'entrée à explorer"},
    "depth": {"type": "integer", "description": "Profondeur de traversée (défaut: 1)", "default": 1}
  },
  "required": ["entry_id"]
}
```

#### rekall_similar

```json
{
  "type": "object",
  "properties": {
    "entry_id": {"type": "string", "description": "ID de l'entrée de référence"},
    "limit": {"type": "integer", "description": "Nombre max de résultats (défaut: 5)", "default": 5}
  },
  "required": ["entry_id"]
}
```

#### rekall_sources_suggest

```json
{
  "type": "object",
  "properties": {
    "entry_id": {"type": "string", "description": "ID de l'entrée pour laquelle suggérer des sources"},
    "limit": {"type": "integer", "description": "Nombre max de suggestions (défaut: 5)", "default": 5}
  },
  "required": ["entry_id"]
}
```

#### rekall_info

```json
{
  "type": "object",
  "properties": {}
}
```

#### rekall_stale

```json
{
  "type": "object",
  "properties": {
    "days": {"type": "integer", "description": "Seuil en jours (défaut: 90)", "default": 90},
    "limit": {"type": "integer", "description": "Nombre max de résultats (défaut: 20)", "default": 20}
  }
}
```

#### rekall_generalize

```json
{
  "type": "object",
  "properties": {
    "entry_ids": {
      "type": "array",
      "items": {"type": "string"},
      "description": "IDs des entrées à généraliser (minimum 2)"
    },
    "title": {"type": "string", "description": "Titre de l'entrée généralisée (optionnel)"}
  },
  "required": ["entry_ids"]
}
```

#### rekall_sources_verify

```json
{
  "type": "object",
  "properties": {
    "limit": {"type": "integer", "description": "Nombre max d'URLs à vérifier (défaut: 10)", "default": 10}
  }
}
```

---

## Prochaine Étape

Exécuter `/speckit.tasks` pour générer les tâches d'implémentation détaillées.
