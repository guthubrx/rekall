# Feature 006 : Contexte Enrichi pour Mémoire IA

**Version** : 0.1
**Date** : 2025-12-10
**Statut** : Draft

---

## Résumé

Transformer le champ `context` de Rekall d'un simple texte optionnel en un système de capture automatique et structuré qui force l'agent à documenter correctement ses découvertes.

## Motivation

### Problème actuel

1. Le contexte est **optionnel** → oublié 90% du temps
2. Le contexte est **non structuré** → inutilisable pour désambiguïser
3. La capture est **manuelle** → friction élevée
4. Pas de **rappel proactif** → l'agent ne sait pas quand sauvegarder

### Solution proposée

1. **Schema obligatoire** : Contexte structuré requis dans le MCP
2. **Auto-capture** : Extraction automatique de la conversation
3. **Guidance** : Prompts enrichis pour guider l'agent
4. **Proactivité** : Hooks de rappel quand une sauvegarde est pertinente
5. **Consolidation** : Transformation épisodique → sémantique

## User Stories

### US1 : Contexte Structuré Obligatoire

> En tant qu'agent IA, je suis **forcé** de fournir un contexte structuré quand je crée une entrée, pour garantir que les souvenirs sont désambiguïsables.

**Critères d'acceptation** :
- [ ] Le schema MCP `rekall_add` requiert `context` avec sous-champs obligatoires
- [ ] Les sous-champs requis sont : `situation`, `solution`, `trigger_keywords`
- [ ] L'appel échoue si le contexte est incomplet
- [ ] Le CLI `add` accepte `--context-json` pour le contexte structuré

### US2 : Auto-Capture Conversation

> En tant qu'agent IA, je peux fournir `context.conversation_excerpt` qui est automatiquement extrait des derniers échanges, pour réduire ma charge cognitive.

**Critères d'acceptation** :
- [ ] Nouveau champ optionnel `conversation_excerpt` dans le contexte
- [ ] Si fourni par l'agent, stocké tel quel
- [ ] Compression automatique (zlib)
- [ ] Limite de taille configurable

### US3 : Extraction Automatique de Keywords

> En tant qu'agent IA, si je ne fournis pas `trigger_keywords`, le système les extrait automatiquement du titre et contenu.

**Critères d'acceptation** :
- [ ] Extraction automatique si keywords non fournis
- [ ] Algorithme : TF-IDF ou extraction simple (noms, verbes clés)
- [ ] Stockage dans le contexte pour recherche hybride

### US4 : Prompt Système Enrichi

> En tant qu'agent IA, je reçois des instructions claires dans la description MCP sur QUAND et COMMENT utiliser Rekall.

**Critères d'acceptation** :
- [ ] Description MCP enrichie avec exemples
- [ ] Guide sur les moments de sauvegarde (bug résolu, pattern découvert, etc.)
- [ ] Exemple de contexte structuré complet

### US5 : Recherche Hybride avec Contexte

> En tant qu'utilisateur, quand je recherche, le système utilise le contexte pour désambiguïser les résultats similaires.

**Critères d'acceptation** :
- [ ] Recherche BM25 sur `trigger_keywords`
- [ ] Re-ranking basé sur match contexte/query
- [ ] Affichage du contexte pertinent dans les résultats

### US6 : Consolidation Épisodique → Sémantique

> En tant que système, je détecte automatiquement les clusters d'entrées similaires et propose de les consolider en patterns.

**Critères d'acceptation** :
- [ ] Détection de clusters (>= 3 entrées similaires)
- [ ] Génération de suggestion `generalize`
- [ ] Création de pattern avec liens vers les épisodes sources
- [ ] Préservation des contextes originaux

## Modèle de Données

### Nouveau : StructuredContext

```python
@dataclass
class StructuredContext:
    """Contexte structuré pour désambiguïsation."""

    # Obligatoires
    situation: str              # Quel était le problème initial ?
    solution: str               # Comment l'as-tu résolu ?
    trigger_keywords: list[str] # Mots-clés pour retrouver

    # Optionnels
    what_failed: Optional[str] = None        # Ce qui n'a pas marché
    conversation_excerpt: Optional[str] = None  # Extrait conversation
    files_modified: Optional[list[str]] = None  # Fichiers touchés
    error_messages: Optional[list[str]] = None  # Erreurs rencontrées

    # Méta (auto-généré)
    created_at: datetime = field(default_factory=datetime.now)
    extraction_method: str = "manual"  # manual | auto | hybrid
```

### Migration DB

```sql
-- Renommer l'ancien champ
ALTER TABLE entries RENAME COLUMN context_compressed TO context_legacy;

-- Nouveau champ JSON structuré
ALTER TABLE entries ADD COLUMN context_structured TEXT;  -- JSON

-- Index pour recherche keywords
CREATE INDEX idx_context_keywords ON entries(context_structured);
```

## API Changes

### MCP rekall_add (modifié)

```json
{
  "name": "rekall_add",
  "inputSchema": {
    "required": ["type", "title", "context"],
    "properties": {
      "context": {
        "type": "object",
        "required": ["situation", "solution", "trigger_keywords"],
        "properties": {
          "situation": {
            "type": "string",
            "description": "Quel était le problème initial ?"
          },
          "solution": {
            "type": "string",
            "description": "Comment l'as-tu résolu ?"
          },
          "trigger_keywords": {
            "type": "array",
            "items": { "type": "string" },
            "description": "Mots-clés pour retrouver ce souvenir"
          },
          "what_failed": {
            "type": "string",
            "description": "Ce qui a été essayé mais n'a pas marché"
          },
          "conversation_excerpt": {
            "type": "string",
            "description": "Extrait des derniers échanges de conversation"
          }
        }
      }
    }
  }
}
```

### CLI add (modifié)

```bash
# Nouveau flag pour contexte structuré
rekall add bug "Fix 504 timeout" \
  --content "..." \
  --context-json '{"situation": "...", "solution": "...", "trigger_keywords": ["504", "nginx"]}'

# Ou mode interactif
rekall add bug "Fix 504 timeout" --context-interactive
```

## Hors Scope (v1)

- Hook de rappel automatique (Phase 4) - complexité élevée
- Détection de moments de sauvegarde côté conversation
- Intégration IDE pour capture fichiers modifiés
- Multi-modal (screenshots, logs)

## Risques

| Risque | Mitigation |
|--------|------------|
| Friction accrue pour l'agent | Valeurs par défaut intelligentes, extraction auto |
| Contexte trop verbeux | Limite de taille, compression |
| Migration des anciennes entrées | Conserver `context_legacy`, migration optionnelle |
| Performance recherche | Index sur keywords, cache |

## Métriques de Succès

- 90%+ des nouvelles entrées ont un contexte structuré complet
- Temps de recherche désambiguïsée < 500ms
- Taux de rappel amélioré de 30% sur requêtes ambiguës
