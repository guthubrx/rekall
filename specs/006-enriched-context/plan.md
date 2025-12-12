# Plan d'Implémentation : Feature 006 - Contexte Enrichi

**Date** : 2025-12-10
**Durée estimée** : 5 phases

---

## Vue d'Ensemble des Phases

```
Phase 1: Schema & Modèle     ████░░░░░░  Foundation
Phase 2: MCP Obligatoire     ████░░░░░░  Force l'agent
Phase 3: Auto-extraction     ██████░░░░  Réduit friction
Phase 4: Recherche Hybride   ████████░░  Exploite le contexte
Phase 5: Consolidation       ██████████  Intelligence
```

---

## Phase 1 : Modèle de Données et Migration

### Objectif
Créer le nouveau modèle `StructuredContext` et migrer la base de données.

### Tâches

#### T001 : Créer le dataclass StructuredContext
**Fichier** : `rekall/models.py`

```python
@dataclass
class StructuredContext:
    """Contexte structuré pour désambiguïsation."""

    situation: str
    solution: str
    trigger_keywords: list[str]
    what_failed: Optional[str] = None
    conversation_excerpt: Optional[str] = None
    files_modified: Optional[list[str]] = None
    error_messages: Optional[list[str]] = None
    created_at: datetime = field(default_factory=datetime.now)
    extraction_method: str = "manual"

    def to_json(self) -> str: ...
    @classmethod
    def from_json(cls, data: str) -> "StructuredContext": ...
    def to_compressed(self) -> bytes: ...
    @classmethod
    def from_compressed(cls, data: bytes) -> "StructuredContext": ...
```

#### T002 : Migration DB v6
**Fichier** : `rekall/db.py`

```sql
-- Migration 6
ALTER TABLE entries ADD COLUMN context_structured TEXT;
-- Garder context_compressed pour rétro-compatibilité
```

#### T003 : Méthodes DB pour contexte structuré
**Fichier** : `rekall/db.py`

- `store_structured_context(entry_id, context: StructuredContext)`
- `get_structured_context(entry_id) -> Optional[StructuredContext]`
- `search_by_keywords(keywords: list[str]) -> list[Entry]`

#### T004 : Tests Phase 1
**Fichier** : `tests/test_db.py`

- Test création/récupération contexte structuré
- Test sérialisation JSON
- Test compression/décompression
- Test migration v6

### Livrables
- [ ] Modèle `StructuredContext` avec validation
- [ ] Migration DB v6
- [ ] Méthodes CRUD pour contexte structuré
- [ ] Tests unitaires

---

## Phase 2 : MCP avec Contexte Obligatoire

### Objectif
Modifier le schema MCP pour rendre le contexte structuré obligatoire.

### Tâches

#### T005 : Modifier schema MCP rekall_add
**Fichier** : `rekall/mcp_server.py`

```python
Tool(
    name="rekall_add",
    description="...",  # Description enrichie avec exemples
    inputSchema={
        "required": ["type", "title", "context"],
        "properties": {
            "context": {
                "type": "object",
                "required": ["situation", "solution", "trigger_keywords"],
                ...
            }
        }
    }
)
```

#### T006 : Handler MCP pour contexte structuré
**Fichier** : `rekall/mcp_server.py`

- Parser le contexte JSON
- Valider les champs requis
- Créer `StructuredContext`
- Stocker via `db.store_structured_context()`

#### T007 : Description MCP enrichie
**Fichier** : `rekall/mcp_server.py`

```python
REKALL_GUIDANCE = """
## Quand créer une entrée Rekall
AUTOMATIQUEMENT après :
- Résolution d'un bug → type="bug"
- Découverte d'un pattern → type="pattern"
...

## Exemple complet
rekall_add(
  type="bug",
  title="Fix 504 timeout nginx",
  context={
    "situation": "API timeout sur requêtes > 30s",
    "solution": "nginx proxy_read_timeout 120s",
    "trigger_keywords": ["504", "nginx", "timeout"]
  }
)
"""
```

#### T008 : CLI add avec --context-json
**Fichier** : `rekall/cli.py`

```python
@app.command()
def add(
    ...
    context_json: Optional[str] = typer.Option(None, "--context-json", "-cj"),
):
    if context_json:
        context = StructuredContext.from_json(context_json)
        db.store_structured_context(entry.id, context)
```

#### T009 : Tests Phase 2
- Test MCP rejette appel sans contexte
- Test MCP accepte contexte valide
- Test CLI --context-json

### Livrables
- [ ] Schema MCP avec contexte obligatoire
- [ ] Handler validant le contexte
- [ ] Description MCP enrichie
- [ ] CLI --context-json
- [ ] Tests

---

## Phase 3 : Auto-extraction et Assistance

### Objectif
Réduire la friction en extrayant automatiquement certaines informations.

### Tâches

#### T010 : Extraction automatique de keywords
**Fichier** : `rekall/context_extractor.py` (nouveau)

```python
def extract_keywords(title: str, content: str) -> list[str]:
    """Extrait les mots-clés significatifs."""
    # Simple: mots > 4 chars, pas stopwords, fréquence > 1
    # Avancé: TF-IDF si numpy disponible
```

#### T011 : Fallback keywords dans MCP
**Fichier** : `rekall/mcp_server.py`

```python
# Si trigger_keywords vide ou absent, extraire automatiquement
if not context.get("trigger_keywords"):
    context["trigger_keywords"] = extract_keywords(title, content)
```

#### T012 : Mode context-interactive CLI
**Fichier** : `rekall/cli.py`

```python
@app.command()
def add(..., context_interactive: bool = typer.Option(False, "--context-interactive")):
    if context_interactive:
        situation = typer.prompt("Situation initiale")
        solution = typer.prompt("Solution apportée")
        keywords = typer.prompt("Mots-clés (virgule)").split(",")
        ...
```

#### T013 : Validation et suggestions
**Fichier** : `rekall/context_extractor.py`

```python
def validate_context(context: StructuredContext) -> list[str]:
    """Retourne liste de warnings/suggestions."""
    warnings = []
    if len(context.situation) < 20:
        warnings.append("Situation trop courte, ajoutez des détails")
    if len(context.trigger_keywords) < 2:
        warnings.append("Ajoutez plus de mots-clés pour faciliter la recherche")
    return warnings
```

#### T014 : Tests Phase 3
- Test extraction keywords
- Test fallback automatique
- Test validation contexte
- Test CLI interactif

### Livrables
- [ ] Module `context_extractor.py`
- [ ] Extraction automatique keywords
- [ ] CLI mode interactif
- [ ] Validation avec suggestions
- [ ] Tests

---

## Phase 4 : Recherche Hybride avec Contexte

### Objectif
Exploiter le contexte structuré pour améliorer la recherche et désambiguïser.

### Tâches

#### T015 : Index BM25 sur keywords
**Fichier** : `rekall/db.py`

```python
def search_by_keywords(self, keywords: list[str], limit: int = 20) -> list[Entry]:
    """Recherche par mots-clés du contexte."""
    # Utiliser FTS5 sur context_structured
```

#### T016 : Re-ranking avec contexte
**Fichier** : `rekall/search.py` (nouveau ou existant)

```python
def search_with_context_rerank(query: str, candidates: list[Entry]) -> list[Entry]:
    """Re-rank les candidats en fonction du match contexte."""
    for entry in candidates:
        ctx = db.get_structured_context(entry.id)
        if ctx:
            # Bonus si query match situation/solution/keywords
            entry.score += calculate_context_match(query, ctx)
    return sorted(candidates, key=lambda e: e.score, reverse=True)
```

#### T017 : Fusion recherche hybride
**Fichier** : `rekall/db.py`

```python
def hybrid_search(self, query: str, limit: int = 10) -> list[SearchResult]:
    """Combine embedding + BM25 + context match."""
    # 1. Recherche embedding (top 30)
    # 2. Recherche BM25 sur keywords (top 30)
    # 3. Reciprocal Rank Fusion
    # 4. Re-rank avec contexte
    # 5. Return top limit
```

#### T018 : Affichage contexte dans résultats
**Fichier** : `rekall/cli.py`, `rekall/tui.py`

- Afficher `situation` dans les résultats de recherche
- Option `--show-context` pour détails complets

#### T019 : Tests Phase 4
- Test recherche par keywords
- Test re-ranking
- Test recherche hybride
- Test affichage contexte

### Livrables
- [ ] Recherche par keywords
- [ ] Re-ranking contextuel
- [ ] Recherche hybride
- [ ] Affichage contexte
- [ ] Tests

---

## Phase 5 : Consolidation Automatique

### Objectif
Transformer automatiquement les entrées épisodiques répétées en patterns sémantiques.

### Tâches

#### T020 : Détection de clusters
**Fichier** : `rekall/consolidation.py` (nouveau)

```python
def detect_clusters(db: Database, threshold: float = 0.85) -> list[Cluster]:
    """Détecte les groupes d'entrées similaires."""
    # Utiliser embeddings existants
    # Clustering par similarité cosine
    # Retourner clusters de >= 3 entrées
```

#### T021 : Génération de pattern
**Fichier** : `rekall/consolidation.py`

```python
def generate_pattern_from_cluster(cluster: Cluster) -> Entry:
    """Génère un pattern sémantique depuis un cluster épisodique."""
    # Extraire les éléments communs
    # Générer titre/contenu généralisé
    # Fusionner les keywords
    # Type = "pattern", memory_type = "semantic"
```

#### T022 : Suggestions de consolidation
**Fichier** : `rekall/consolidation.py`

```python
def suggest_consolidations(db: Database) -> list[Suggestion]:
    """Génère des suggestions de type 'generalize'."""
    clusters = detect_clusters(db)
    suggestions = []
    for cluster in clusters:
        suggestions.append(Suggestion(
            suggestion_type="generalize",
            entry_ids=[e.id for e in cluster.entries],
            score=cluster.similarity,
            reason=f"Ces {len(cluster.entries)} entrées partagent: {cluster.common_keywords}"
        ))
    return suggestions
```

#### T023 : Action de consolidation
**Fichier** : `rekall/db.py`

```python
def consolidate_entries(self, entry_ids: list[str], pattern_title: str) -> Entry:
    """Crée un pattern et lie les entrées sources."""
    # Créer entry pattern
    # Créer liens derived_from vers chaque source
    # Marquer les sources comme consolidées
```

#### T024 : CLI et TUI pour consolidation
**Fichier** : `rekall/cli.py`, `rekall/tui.py`

```bash
rekall consolidate --auto        # Exécute toutes les suggestions
rekall consolidate --review      # Mode interactif
rekall suggest --type generalize # Voir les suggestions
```

#### T025 : Tests Phase 5
- Test détection clusters
- Test génération pattern
- Test suggestions
- Test consolidation

### Livrables
- [ ] Module `consolidation.py`
- [ ] Détection de clusters
- [ ] Génération de patterns
- [ ] Suggestions automatiques
- [ ] CLI/TUI consolidation
- [ ] Tests

---

## Résumé des Phases

| Phase | Tâches | Priorité | Dépendances |
|-------|--------|----------|-------------|
| 1 | T001-T004 | Critique | Aucune |
| 2 | T005-T009 | Critique | Phase 1 |
| 3 | T010-T014 | Haute | Phase 2 |
| 4 | T015-T019 | Haute | Phase 3 |
| 5 | T020-T025 | Moyenne | Phase 4 |

---

## Checklist Globale

- [ ] Phase 1 : Modèle et Migration
- [ ] Phase 2 : MCP Obligatoire
- [ ] Phase 3 : Auto-extraction
- [ ] Phase 4 : Recherche Hybride
- [ ] Phase 5 : Consolidation

---

*Plan créé le 2025-12-10*
