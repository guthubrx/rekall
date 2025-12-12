# Tasks : Feature 006 - Contexte Enrichi

**Date** : 2025-12-10
**Statut** : Terminé

---

## Tableau de Suivi

| ID | Tâche | Phase | Statut | Fichiers |
|----|-------|-------|--------|----------|
| T001 | Créer dataclass StructuredContext | 1 | ✅ done | models.py |
| T002 | Migration DB v6 | 1 | ✅ done | db.py |
| T003 | Méthodes DB contexte structuré | 1 | ✅ done | db.py |
| T004 | Tests Phase 1 | 1 | ✅ done | test_db.py, test_models.py |
| T005 | Modifier schema MCP rekall_add | 2 | ✅ done | mcp_server.py |
| T006 | Handler MCP contexte structuré | 2 | ✅ done | mcp_server.py |
| T007 | Description MCP enrichie | 2 | ✅ done | mcp_server.py |
| T008 | CLI add --context-json | 2 | ✅ done | cli.py |
| T009 | Tests Phase 2 | 2 | ✅ done | test_cli.py |
| T010 | Extraction automatique keywords | 3 | ✅ done | context_extractor.py |
| T011 | Fallback keywords MCP | 3 | ✅ done | mcp_server.py |
| T012 | CLI mode context-interactive | 3 | ✅ done | cli.py |
| T013 | Validation et suggestions | 3 | ✅ done | context_extractor.py |
| T014 | Tests Phase 3 | 3 | ✅ done | test_context_extractor.py |
| T015 | Scoring keywords contexte | 4 | ✅ done | context_extractor.py |
| T016 | Re-ranking avec contexte | 4 | ✅ done | embeddings.py |
| T017 | Fusion recherche hybride | 4 | ✅ done | embeddings.py |
| T018 | Affichage contexte résultats | 4 | ✅ done | mcp_server.py |
| T019 | Tests Phase 4 | 4 | ✅ done | test_context_extractor.py |
| T020 | Détection de clusters | 5 | ✅ done | consolidation.py |
| T021 | Génération de pattern | 5 | ✅ done | consolidation.py |
| T022 | Suggestions consolidation | 5 | ✅ done | consolidation.py |
| T023 | MCP suggest amélioré | 5 | ✅ done | mcp_server.py |
| T024 | CLI suggest (existant) | 5 | ✅ done | cli.py |
| T025 | Tests Phase 5 | 5 | ✅ done | test_consolidation.py |

---

## Phase 1 : Modèle de Données et Migration

### T001 : Créer dataclass StructuredContext
**Statut** : pending
**Fichier** : `rekall/models.py`

**Description** :
Créer le nouveau dataclass pour le contexte structuré avec validation.

**Code** :
```python
@dataclass
class StructuredContext:
    """Contexte structuré pour désambiguïsation des entrées."""

    # Champs obligatoires
    situation: str              # Quel était le problème initial ?
    solution: str               # Comment l'as-tu résolu ?
    trigger_keywords: list[str] # Mots-clés pour retrouver

    # Champs optionnels
    what_failed: Optional[str] = None
    conversation_excerpt: Optional[str] = None
    files_modified: Optional[list[str]] = None
    error_messages: Optional[list[str]] = None

    # Méta
    created_at: datetime = field(default_factory=datetime.now)
    extraction_method: str = "manual"  # manual | auto | hybrid

    def __post_init__(self):
        """Valider les champs obligatoires."""
        if not self.situation or len(self.situation) < 5:
            raise ValueError("situation must be at least 5 characters")
        if not self.solution or len(self.solution) < 5:
            raise ValueError("solution must be at least 5 characters")
        if not self.trigger_keywords or len(self.trigger_keywords) < 1:
            raise ValueError("at least 1 trigger keyword required")

    def to_json(self) -> str:
        """Sérialiser en JSON."""
        import json
        return json.dumps({
            "situation": self.situation,
            "solution": self.solution,
            "trigger_keywords": self.trigger_keywords,
            "what_failed": self.what_failed,
            "conversation_excerpt": self.conversation_excerpt,
            "files_modified": self.files_modified,
            "error_messages": self.error_messages,
            "created_at": self.created_at.isoformat(),
            "extraction_method": self.extraction_method,
        })

    @classmethod
    def from_json(cls, data: str | dict) -> "StructuredContext":
        """Désérialiser depuis JSON."""
        import json
        if isinstance(data, str):
            data = json.loads(data)
        return cls(
            situation=data["situation"],
            solution=data["solution"],
            trigger_keywords=data["trigger_keywords"],
            what_failed=data.get("what_failed"),
            conversation_excerpt=data.get("conversation_excerpt"),
            files_modified=data.get("files_modified"),
            error_messages=data.get("error_messages"),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else datetime.now(),
            extraction_method=data.get("extraction_method", "manual"),
        )
```

**Tests** :
- Création avec champs valides
- Validation rejette champs vides
- Sérialisation/désérialisation JSON

---

### T002 : Migration DB v6
**Statut** : pending
**Fichier** : `rekall/db.py`

**Description** :
Ajouter la colonne `context_structured` pour stocker le JSON du contexte.

**Code** :
```python
CURRENT_SCHEMA_VERSION = 6

MIGRATIONS = {
    ...
    6: [
        "ALTER TABLE entries ADD COLUMN context_structured TEXT",
    ],
}
```

**Tests** :
- Migration s'exécute sans erreur
- Nouvelle colonne existe
- Anciennes entrées ont context_structured = NULL

---

### T003 : Méthodes DB contexte structuré
**Statut** : pending
**Fichier** : `rekall/db.py`

**Description** :
Ajouter les méthodes CRUD pour le contexte structuré.

**Code** :
```python
def store_structured_context(self, entry_id: str, context: StructuredContext) -> None:
    """Stocker le contexte structuré pour une entrée."""
    self.conn.execute(
        "UPDATE entries SET context_structured = ? WHERE id = ?",
        (context.to_json(), entry_id)
    )
    self.conn.commit()

def get_structured_context(self, entry_id: str) -> Optional[StructuredContext]:
    """Récupérer le contexte structuré d'une entrée."""
    cursor = self.conn.execute(
        "SELECT context_structured FROM entries WHERE id = ?",
        (entry_id,)
    )
    row = cursor.fetchone()
    if row and row["context_structured"]:
        return StructuredContext.from_json(row["context_structured"])
    return None

def search_by_keywords(self, keywords: list[str], limit: int = 20) -> list[Entry]:
    """Rechercher par mots-clés du contexte."""
    # Recherche JSON dans context_structured
    conditions = []
    params = []
    for kw in keywords:
        conditions.append("context_structured LIKE ?")
        params.append(f"%{kw}%")

    sql = f"""
        SELECT * FROM entries
        WHERE {" OR ".join(conditions)}
        ORDER BY updated_at DESC
        LIMIT ?
    """
    params.append(limit)
    # ...
```

**Tests** :
- Store et retrieve context
- Search par keywords trouve les entrées
- Entrée sans context retourne None

---

### T004 : Tests Phase 1
**Statut** : pending
**Fichier** : `tests/test_db.py`

**Description** :
Tests unitaires pour Phase 1.

**Code** :
```python
class TestStructuredContext:
    def test_create_valid_context(self):
        ctx = StructuredContext(
            situation="API returning 504 errors",
            solution="Increased nginx timeout to 120s",
            trigger_keywords=["504", "nginx", "timeout"]
        )
        assert ctx.situation == "API returning 504 errors"

    def test_reject_empty_situation(self):
        with pytest.raises(ValueError):
            StructuredContext(situation="", solution="fix", trigger_keywords=["k"])

    def test_json_roundtrip(self):
        ctx = StructuredContext(...)
        json_str = ctx.to_json()
        ctx2 = StructuredContext.from_json(json_str)
        assert ctx.situation == ctx2.situation

class TestStructuredContextDB:
    def test_store_and_retrieve(self, temp_db_path):
        # ...

    def test_search_by_keywords(self, temp_db_path):
        # ...
```

---

## Phase 2 : MCP avec Contexte Obligatoire

### T005 : Modifier schema MCP rekall_add
**Statut** : pending
**Fichier** : `rekall/mcp_server.py`

**Description** :
Rendre le contexte obligatoire dans le schema MCP.

**Code** :
```python
Tool(
    name="rekall_add",
    description=REKALL_ADD_GUIDANCE,  # Description enrichie
    inputSchema={
        "type": "object",
        "required": ["type", "title", "context"],
        "properties": {
            "type": {...},
            "title": {...},
            "content": {...},
            "context": {
                "type": "object",
                "description": "Contexte structuré OBLIGATOIRE",
                "required": ["situation", "solution", "trigger_keywords"],
                "properties": {
                    "situation": {
                        "type": "string",
                        "description": "Quel était le problème initial ? (min 10 chars)"
                    },
                    "solution": {
                        "type": "string",
                        "description": "Comment l'as-tu résolu ? (min 10 chars)"
                    },
                    "trigger_keywords": {
                        "type": "array",
                        "items": {"type": "string"},
                        "minItems": 1,
                        "description": "Mots-clés pour retrouver ce souvenir"
                    },
                    "what_failed": {
                        "type": "string",
                        "description": "Ce qui a été essayé mais n'a pas marché"
                    },
                    "conversation_excerpt": {
                        "type": "string",
                        "description": "Extrait des échanges pertinents"
                    }
                }
            },
            ...
        }
    }
)
```

---

### T006 : Handler MCP contexte structuré
**Statut** : pending
**Fichier** : `rekall/mcp_server.py`

**Description** :
Modifier `_handle_add` pour traiter le contexte structuré.

**Code** :
```python
async def _handle_add(args: dict) -> list:
    # ... création entry ...

    # Traiter contexte structuré
    context_data = args.get("context")
    if context_data:
        try:
            structured_ctx = StructuredContext.from_json(context_data)
            db.store_structured_context(entry.id, structured_ctx)
        except ValueError as e:
            return [TextContent(type="text", text=f"Context validation error: {e}")]

    # ... reste du code ...
```

---

### T007 : Description MCP enrichie
**Statut** : pending
**Fichier** : `rekall/mcp_server.py`

**Description** :
Ajouter une description détaillée guidant l'agent.

**Code** :
```python
REKALL_ADD_GUIDANCE = """
Add a knowledge entry to Rekall memory. CONTEXT IS REQUIRED.

## When to Use
AUTOMATICALLY call rekall_add after:
- Resolving a bug → type="bug"
- Discovering a reusable pattern → type="pattern"
- Making an architecture decision → type="decision"
- Avoiding a pitfall → type="pitfall"

## Context Structure (REQUIRED)
{
  "situation": "What was the initial problem? Be specific.",
  "solution": "How did you solve it? Include key details.",
  "trigger_keywords": ["word1", "word2", "word3"],
  "what_failed": "What was tried but didn't work? (optional)",
  "conversation_excerpt": "Relevant conversation excerpt (optional)"
}

## Example
rekall_add(
  type="bug",
  title="Fix 504 Gateway Timeout on nginx",
  content="## Problem\\nAPI timeout on requests > 30s...\\n## Solution\\n...",
  context={
    "situation": "Production API returning 504 errors on export endpoint",
    "solution": "Increased proxy_read_timeout from 30s to 120s in nginx.conf",
    "trigger_keywords": ["504", "nginx", "timeout", "proxy_read_timeout", "gateway"],
    "what_failed": "Increasing client-side timeout did not help"
  }
)
"""
```

---

### T008 : CLI add --context-json
**Statut** : pending
**Fichier** : `rekall/cli.py`

**Description** :
Ajouter l'option `--context-json` au CLI.

**Code** :
```python
@app.command()
def add(
    entry_type: str = typer.Argument(...),
    title: str = typer.Argument(...),
    content: Optional[str] = typer.Option(None, "--content", "-c"),
    context_json: Optional[str] = typer.Option(
        None,
        "--context-json",
        "-cj",
        help="Contexte structuré en JSON"
    ),
    ...
):
    # ... création entry ...

    if context_json:
        try:
            ctx = StructuredContext.from_json(context_json)
            db.store_structured_context(entry.id, ctx)
            console.print(f"[green]✓[/green] Contexte structuré enregistré")
        except (json.JSONDecodeError, ValueError) as e:
            console.print(f"[yellow]⚠[/yellow] Contexte invalide: {e}")
```

---

### T009 : Tests Phase 2
**Statut** : pending
**Fichiers** : `tests/test_cli.py`, `tests/test_mcp.py`

---

## Phase 3 : Auto-extraction et Assistance

### T010 : Extraction automatique keywords
**Statut** : pending
**Fichier** : `rekall/context_extractor.py` (nouveau)

**Code** :
```python
"""Extracteur de contexte automatique."""

import re
from collections import Counter

STOPWORDS = {"the", "a", "an", "is", "are", "was", "were", "be", "been", ...}

def extract_keywords(title: str, content: str, max_keywords: int = 10) -> list[str]:
    """Extrait les mots-clés significatifs du titre et contenu."""
    text = f"{title} {content}".lower()

    # Extraire les mots
    words = re.findall(r'\b[a-z]{4,}\b', text)

    # Filtrer stopwords
    words = [w for w in words if w not in STOPWORDS]

    # Compter fréquences
    freq = Counter(words)

    # Top N
    return [word for word, _ in freq.most_common(max_keywords)]


def extract_error_patterns(text: str) -> list[str]:
    """Extrait les patterns d'erreur courants."""
    patterns = [
        r'error[:\s]+([^\n]+)',
        r'exception[:\s]+([^\n]+)',
        r'\b(\d{3})\s+(error|timeout|not found)',
        r'failed[:\s]+([^\n]+)',
    ]
    errors = []
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        errors.extend(matches)
    return errors[:5]
```

---

### T011 : Fallback keywords MCP
**Statut** : pending
**Fichier** : `rekall/mcp_server.py`

**Code** :
```python
from rekall.context_extractor import extract_keywords

async def _handle_add(args: dict) -> list:
    context_data = args.get("context", {})

    # Fallback: extraire keywords si non fournis
    if not context_data.get("trigger_keywords"):
        title = args.get("title", "")
        content = args.get("content", "")
        context_data["trigger_keywords"] = extract_keywords(title, content)
        context_data["extraction_method"] = "auto"
```

---

### T012 : CLI mode context-interactive
**Statut** : pending
**Fichier** : `rekall/cli.py`

**Code** :
```python
@app.command()
def add(
    ...
    context_interactive: bool = typer.Option(
        False, "--context-interactive", "-ci",
        help="Mode interactif pour le contexte"
    ),
):
    if context_interactive:
        console.print("[cyan]Contexte structuré (OBLIGATOIRE)[/cyan]")
        situation = typer.prompt("Situation initiale")
        solution = typer.prompt("Solution apportée")
        keywords_str = typer.prompt("Mots-clés (séparés par virgule)")
        keywords = [k.strip() for k in keywords_str.split(",")]
        what_failed = typer.prompt("Ce qui n'a pas marché (optionnel)", default="")

        ctx = StructuredContext(
            situation=situation,
            solution=solution,
            trigger_keywords=keywords,
            what_failed=what_failed or None,
        )
        db.store_structured_context(entry.id, ctx)
```

---

### T013 : Validation et suggestions
**Statut** : pending
**Fichier** : `rekall/context_extractor.py`

**Code** :
```python
def validate_context(context: StructuredContext) -> list[str]:
    """Retourne liste de warnings/suggestions."""
    warnings = []

    if len(context.situation) < 20:
        warnings.append("⚠ Situation trop courte - ajoutez des détails pour faciliter la recherche")

    if len(context.solution) < 20:
        warnings.append("⚠ Solution trop courte - décrivez les étapes clés")

    if len(context.trigger_keywords) < 3:
        warnings.append("⚠ Peu de mots-clés - ajoutez-en pour améliorer la recherche")

    if not context.what_failed:
        warnings.append("💡 Conseil: documentez ce qui n'a pas marché pour éviter de refaire les mêmes erreurs")

    return warnings
```

---

### T014 : Tests Phase 3
**Statut** : pending
**Fichier** : `tests/test_context_extractor.py`

---

## Phase 4 : Recherche Hybride avec Contexte

### T015-T019 : Voir plan.md pour détails

---

## Phase 5 : Consolidation Automatique

### T020-T025 : Voir plan.md pour détails

---

## Progression

```
Phase 1: ██████████ 4/4 (100%)
Phase 2: ██████████ 5/5 (100%)
Phase 3: ██████████ 5/5 (100%)
Phase 4: ██████████ 5/5 (100%)
Phase 5: ██████████ 6/6 (100%)
─────────────────────────────
Total:   ██████████ 25/25 (100%)
```

---

## Résumé d'implémentation

### Fichiers créés
- `rekall/context_extractor.py` - Extraction automatique de keywords
- `rekall/consolidation.py` - Détection de patterns et consolidation
- `tests/test_context_extractor.py` - 29 tests
- `tests/test_consolidation.py` - 11 tests

### Fichiers modifiés
- `rekall/models.py` - StructuredContext dataclass
- `rekall/db.py` - Migration v6, méthodes contexte structuré
- `rekall/embeddings.py` - hybrid_search avec scoring keywords
- `rekall/mcp_server.py` - Handlers enrichis
- `rekall/cli.py` - Mode --context-interactive

### Tests
- **267 tests passent** (ajout de 40 nouveaux tests)

---

*Dernière mise à jour : 2025-12-10*
