# Research : MCP Tools Expansion

**Date** : 2025-12-12 | **Feature** : 015-mcp-tools-expansion

## Analyse des Fonctions Existantes

### Fonctions DB Disponibles

| Fonction | Fichier | Ligne | Status |
|----------|---------|-------|--------|
| `delete_link(source_id, target_id)` | db.py | 1064 | ✅ Prêt |
| `get_related_entries(entry_id, depth)` | db.py | 1108 | ✅ Prêt |
| `get_stale_entries(days, limit)` | db.py | 1357 | ✅ Prêt |
| `find_similar(entry_id, db, limit)` | embeddings.py | 256 | ✅ Prêt |
| `verify_sources(urls, limit)` | link_rot.py | 130 | ✅ Prêt |
| `get_source_statistics()` | db.py | 3247 | ✅ Prêt |
| `get_sources_by_theme(theme)` | db.py | 3720 | ✅ Pour sources_suggest |

### Fonctions à Implémenter

| Outil MCP | Logique Requise | Complexité |
|-----------|-----------------|------------|
| `rekall_sources_suggest` | Match tags/keywords entrée → sources | Moyenne |
| `rekall_generalize` | Wrapper CLI generalize existant | Faible |
| `rekall_info` | Agrégation stats existantes | Faible |

## Décisions Techniques

### 1. Pattern des Handlers MCP

**Décision** : Utiliser le même pattern async que les handlers existants
**Rationale** : Cohérence avec `_handle_search`, `_handle_show`, etc.
**Alternatives rejetées** : Sync handlers (incompatible MCP SDK)

### 2. Gestion Embeddings Absents

**Décision** : Retourner message explicite, pas d'erreur
**Rationale** : Meilleure UX pour agents, pas de crash
**Format** : `"Embeddings not enabled. Enable with: rekall config set smart_embeddings.enabled true"`

### 3. Timeout Link Rot

**Décision** : 10s par URL, via httpx async
**Rationale** : Éviter blocage sur URLs lentes, httpx déjà utilisé
**Alternatives rejetées** : requests (sync, bloquant)

### 4. Profondeur Graphe

**Décision** : depth max = 3 pour `rekall_related`
**Rationale** : Éviter explosion combinatoire, performance
**Calcul** : Depth 3 = ~27 entrées max (3^3)

## Sources Consultées

- Code existant `rekall/mcp_server.py` (patterns handlers)
- Code existant `rekall/db.py` (fonctions sous-jacentes)
- MCP SDK documentation (inputSchema format)
