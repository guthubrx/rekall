# Contrats MCP Tools: Smart Embeddings System

**Feature**: 005-smart-embeddings
**Protocole**: MCP (Model Context Protocol) v1.0
**Créé**: 2025-12-09
**Mise à jour**: 2025-12-09 - Progressive Disclosure Pattern

---

## Vue d'Ensemble

Le serveur MCP Rekall expose des tools permettant aux agents AI (Claude, OpenAI, Gemini, Copilot...) d'interagir avec la base de connaissances.

**Architecture SOTA** : Pas de skills/rules files par agent. Les instructions comportementales sont intégrées via `rekall_help()`.

### Démarrage du Serveur

```bash
rekall mcp-server
# ou
rekall mcp-server --port 8765
```

### Configuration MCP Client

```json
{
  "mcpServers": {
    "rekall": {
      "command": "rekall",
      "args": ["mcp-server"]
    }
  }
}
```

### Constitution Minimale (Optionnel)

Si le projet utilise une constitution/rules file :

```markdown
## Rekall Knowledge Base
Tu as accès au serveur MCP Rekall. Appelle `rekall_help()` au premier usage.
```

**3 lignes suffisent.** Tout le reste est dans le MCP.

---

## Progressive Disclosure Pattern

Pour optimiser l'utilisation du contexte (-80% tokens), ce serveur implémente le pattern Progressive Disclosure :

```
Layer 1: Discovery (toujours léger)
├── rekall_help()      → Guide complet (~400 tokens, 1x/session)
└── rekall_search()    → Résultats compacts (id, title, score, snippet)

Layer 2: Details (à la demande)
└── rekall_show(id)    → Contenu complet d'une entrée

Layer 3: Actions
├── rekall_add()       → Créer entrée
├── rekall_link()      → Créer lien
└── rekall_suggest_*() → Gérer suggestions
```

---

## Tools Disponibles

### 1. rekall_help ⭐ (Appeler en premier)

**Guide d'utilisation Rekall.** Retourne les workflows, déclencheurs proactifs, et format de citations. **Appeler une fois en début de session.**

#### Input Schema

```json
{
  "type": "object",
  "properties": {
    "topic": {
      "type": "string",
      "enum": ["search", "capture", "links", "citations", "all"],
      "default": "all",
      "description": "Section spécifique (optionnel, 'all' par défaut)"
    }
  }
}
```

#### Output Schema

```json
{
  "type": "object",
  "properties": {
    "guide": { "type": "string" },
    "topics_available": { "type": "array", "items": { "type": "string" } }
  }
}
```

#### Exemple de Réponse (topic="all")

```markdown
# Rekall - Guide Agent

## Workflow Recherche
1. `rekall_search(query)` → résultats compacts
2. Si pertinent: `rekall_show(id)` → détails complets
3. Citer dans ta réponse: "[01HX] Titre..."

## Workflow Capture
Après résolution d'un bug/problème:
- `rekall_add(type, title, content, context=conversation)`

## Déclencheurs Proactifs
- Bug fix → chercher solutions passées
- Feature → chercher patterns existants
- Erreur mentionnée → chercher si déjà résolu

## Format Citations
Inline: "Selon [01HX123] Fix CORS Safari, le problème..."
```

---

### 2. rekall_search

Recherche dans la base de connaissances. **Retourne des résultats compacts** (Progressive Disclosure). Utiliser `rekall_show(id)` pour les détails.

#### Input Schema

```json
{
  "type": "object",
  "properties": {
    "query": {
      "type": "string",
      "description": "Termes de recherche (mots-clés ou question naturelle)"
    },
    "context": {
      "type": "string",
      "description": "Contexte de la conversation pour enrichir la recherche sémantique"
    },
    "limit": {
      "type": "integer",
      "default": 5,
      "minimum": 1,
      "maximum": 20,
      "description": "Nombre maximum de résultats"
    },
    "type": {
      "type": "string",
      "enum": ["bug", "pattern", "decision", "pitfall", "config", "reference"],
      "description": "Filtrer par type"
    },
    "project": {
      "type": "string",
      "description": "Filtrer par projet"
    }
  },
  "required": ["query"]
}
```

#### Output Schema (Compact - Progressive Disclosure)

```json
{
  "type": "object",
  "properties": {
    "query": { "type": "string" },
    "total": { "type": "integer" },
    "results": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "id": { "type": "string" },
          "type": { "type": "string" },
          "title": { "type": "string" },
          "score": { "type": "number", "description": "Relevance 0-1" },
          "snippet": { "type": "string", "description": "Extrait ~100 chars" },
          "tags": { "type": "array", "items": { "type": "string" } }
        }
      }
    },
    "hint": { "type": "string", "description": "Suggestion pour plus de détails" }
  }
}
```

#### Exemple

```json
// Input
{
  "query": "erreur navigateur Apple",
  "context": "Bug CORS sur Safari iOS",
  "limit": 3
}

// Output (COMPACT - ~150 tokens au lieu de ~500)
{
  "query": "erreur navigateur Apple",
  "total": 2,
  "results": [
    {
      "id": "01HX123",
      "type": "bug",
      "title": "Fix CORS Safari header",
      "score": 0.92,
      "snippet": "Safari ne supporte pas certains headers CORS...",
      "tags": ["cors", "safari", "ios"]
    },
    {
      "id": "01HX456",
      "type": "pattern",
      "title": "Cross-origin requests best practices",
      "score": 0.78,
      "snippet": "Pour les requêtes cross-origin, toujours...",
      "tags": ["cors", "api"]
    }
  ],
  "hint": "Use rekall_show(id) for full content and links"
}
```

---

### 3. rekall_add

Ajoute une nouvelle entrée avec calcul automatique des embeddings.

#### Input Schema

```json
{
  "type": "object",
  "properties": {
    "type": {
      "type": "string",
      "enum": ["bug", "pattern", "decision", "pitfall", "config", "reference"],
      "description": "Type d'entrée"
    },
    "title": {
      "type": "string",
      "description": "Titre de l'entrée (max 100 caractères)",
      "maxLength": 100
    },
    "content": {
      "type": "string",
      "description": "Contenu détaillé de l'entrée"
    },
    "tags": {
      "type": "array",
      "items": { "type": "string" },
      "description": "Tags kebab-case (2-5 recommandés)"
    },
    "context": {
      "type": "string",
      "description": "Contexte complet de la conversation (pour embedding contextuel)"
    },
    "project": {
      "type": "string",
      "description": "Nom du projet associé (optionnel)"
    },
    "confidence": {
      "type": "integer",
      "minimum": 0,
      "maximum": 5,
      "default": 3,
      "description": "Niveau de confiance (0-5)"
    },
    "memory_type": {
      "type": "string",
      "enum": ["episodic", "semantic"],
      "default": "episodic",
      "description": "Type de mémoire"
    }
  },
  "required": ["type", "title"]
}
```

#### Output Schema

```json
{
  "type": "object",
  "properties": {
    "id": { "type": "string" },
    "title": { "type": "string" },
    "type": { "type": "string" },
    "created": { "type": "boolean" },
    "embeddings_calculated": { "type": "boolean" },
    "similar_entries": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "id": { "type": "string" },
          "title": { "type": "string" },
          "score": { "type": "number" }
        }
      }
    },
    "suggestions_created": { "type": "integer" }
  }
}
```

#### Exemple

```json
// Input
{
  "type": "bug",
  "title": "Fix timeout authentication API",
  "content": "Le timeout par défaut de 30s est insuffisant pour l'API d'auth...",
  "tags": ["timeout", "auth", "api"],
  "context": "L'utilisateur signale des erreurs de connexion intermittentes...",
  "project": "myapp",
  "confidence": 4
}

// Output
{
  "id": "01HX789DEF...",
  "title": "Fix timeout authentication API",
  "type": "bug",
  "created": true,
  "embeddings_calculated": true,
  "similar_entries": [
    {
      "id": "01HX123ABC...",
      "title": "Fix CORS Safari header",
      "score": 0.78
    }
  ],
  "suggestions_created": 1
}
```

---

### 4. rekall_show

Affiche les détails complets d'une entrée. **Utiliser après rekall_search pour creuser un résultat.**

#### Input Schema

```json
{
  "type": "object",
  "properties": {
    "id": {
      "type": "string",
      "description": "ID de l'entrée (ULID complet ou préfixe de 5+ caractères)"
    }
  },
  "required": ["id"]
}
```

#### Output Schema

```json
{
  "type": "object",
  "properties": {
    "id": { "type": "string" },
    "type": { "type": "string" },
    "title": { "type": "string" },
    "content": { "type": "string" },
    "tags": { "type": "array", "items": { "type": "string" } },
    "project": { "type": "string", "nullable": true },
    "confidence": { "type": "integer" },
    "status": { "type": "string" },
    "memory_type": { "type": "string" },
    "created_at": { "type": "string", "format": "date-time" },
    "updated_at": { "type": "string", "format": "date-time" },
    "last_accessed": { "type": "string", "format": "date-time", "nullable": true },
    "access_count": { "type": "integer" },
    "consolidation_score": { "type": "number" },
    "embeddings": {
      "type": "object",
      "properties": {
        "summary": { "type": "boolean" },
        "context": { "type": "boolean" }
      }
    },
    "links": {
      "type": "object",
      "properties": {
        "outgoing": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "target_id": { "type": "string" },
              "target_title": { "type": "string" },
              "relation_type": { "type": "string" }
            }
          }
        },
        "incoming": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "source_id": { "type": "string" },
              "source_title": { "type": "string" },
              "relation_type": { "type": "string" }
            }
          }
        }
      }
    }
  }
}
```

---

### 5. rekall_suggest_links

Retourne les suggestions de liens pendantes.

#### Input Schema

```json
{
  "type": "object",
  "properties": {
    "limit": {
      "type": "integer",
      "default": 10,
      "minimum": 1,
      "maximum": 50
    }
  }
}
```

#### Output Schema

```json
{
  "type": "object",
  "properties": {
    "suggestions": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "id": { "type": "string" },
          "entry_a": {
            "type": "object",
            "properties": {
              "id": { "type": "string" },
              "title": { "type": "string" }
            }
          },
          "entry_b": {
            "type": "object",
            "properties": {
              "id": { "type": "string" },
              "title": { "type": "string" }
            }
          },
          "score": { "type": "number" },
          "reason": { "type": "string" },
          "created_at": { "type": "string", "format": "date-time" }
        }
      }
    },
    "total_pending": { "type": "integer" }
  }
}
```

---

### 6. rekall_suggest_generalize

Retourne les suggestions de généralisation pendantes.

#### Input Schema

```json
{
  "type": "object",
  "properties": {
    "limit": {
      "type": "integer",
      "default": 10,
      "minimum": 1,
      "maximum": 50
    }
  }
}
```

#### Output Schema

```json
{
  "type": "object",
  "properties": {
    "suggestions": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "id": { "type": "string" },
          "entries": {
            "type": "array",
            "items": {
              "type": "object",
              "properties": {
                "id": { "type": "string" },
                "title": { "type": "string" }
              }
            }
          },
          "score": { "type": "number" },
          "reason": { "type": "string" },
          "created_at": { "type": "string", "format": "date-time" }
        }
      }
    },
    "total_pending": { "type": "integer" }
  }
}
```

---

### 7. rekall_link

Crée un lien entre deux entrées.

#### Input Schema

```json
{
  "type": "object",
  "properties": {
    "source_id": {
      "type": "string",
      "description": "ID de l'entrée source"
    },
    "target_id": {
      "type": "string",
      "description": "ID de l'entrée cible"
    },
    "relation_type": {
      "type": "string",
      "enum": ["related", "supersedes", "derived_from", "contradicts"],
      "default": "related",
      "description": "Type de relation"
    }
  },
  "required": ["source_id", "target_id"]
}
```

#### Output Schema

```json
{
  "type": "object",
  "properties": {
    "created": { "type": "boolean" },
    "link_id": { "type": "string" },
    "source": {
      "type": "object",
      "properties": {
        "id": { "type": "string" },
        "title": { "type": "string" }
      }
    },
    "target": {
      "type": "object",
      "properties": {
        "id": { "type": "string" },
        "title": { "type": "string" }
      }
    },
    "relation_type": { "type": "string" }
  }
}
```

---

### 8. rekall_accept_suggestion

Accepte une suggestion (crée le lien ou prépare la généralisation).

#### Input Schema

```json
{
  "type": "object",
  "properties": {
    "suggestion_id": {
      "type": "string",
      "description": "ID de la suggestion à accepter"
    }
  },
  "required": ["suggestion_id"]
}
```

#### Output Schema

```json
{
  "type": "object",
  "properties": {
    "accepted": { "type": "boolean" },
    "suggestion_type": { "type": "string" },
    "action_taken": { "type": "string" },
    "link_created": {
      "type": "object",
      "nullable": true,
      "properties": {
        "source_id": { "type": "string" },
        "target_id": { "type": "string" }
      }
    },
    "generalize_command": {
      "type": "string",
      "nullable": true,
      "description": "Commande rekall generalize à exécuter"
    }
  }
}
```

---

### 9. rekall_reject_suggestion

Rejette une suggestion (ne réapparaîtra plus).

#### Input Schema

```json
{
  "type": "object",
  "properties": {
    "suggestion_id": {
      "type": "string",
      "description": "ID de la suggestion à rejeter"
    }
  },
  "required": ["suggestion_id"]
}
```

#### Output Schema

```json
{
  "type": "object",
  "properties": {
    "rejected": { "type": "boolean" },
    "suggestion_id": { "type": "string" }
  }
}
```

---

## Gestion des Erreurs

### Format d'Erreur

```json
{
  "error": {
    "code": "ENTRY_NOT_FOUND",
    "message": "Entry with ID '01HX123...' not found",
    "details": {}
  }
}
```

### Codes d'Erreur

| Code | HTTP | Description |
|------|------|-------------|
| `ENTRY_NOT_FOUND` | 404 | Entrée non trouvée |
| `SUGGESTION_NOT_FOUND` | 404 | Suggestion non trouvée |
| `INVALID_ENTRY_TYPE` | 400 | Type d'entrée invalide |
| `INVALID_RELATION_TYPE` | 400 | Type de relation invalide |
| `EMBEDDINGS_DISABLED` | 503 | Embeddings non configurés |
| `MODEL_NOT_AVAILABLE` | 503 | Modèle d'embedding non installé |
| `LINK_ALREADY_EXISTS` | 409 | Lien déjà existant |
| `SELF_LINK_ERROR` | 400 | Tentative de lier une entrée à elle-même |
| `INTERNAL_ERROR` | 500 | Erreur interne |

---

## Notes d'Implémentation

### Limite de Contexte

- Maximum: 10,000 caractères pour le paramètre `context`
- Au-delà: Troncature automatique aux 8,000 premiers caractères
- Recommandé: Inclure les 3-5 derniers échanges pertinents

### Bonnes Pratiques

**Toutes les instructions comportementales sont dans `rekall_help()`.**

Les agents doivent appeler `rekall_help()` une fois en début de session pour recevoir :
- Workflows (recherche, capture)
- Déclencheurs proactifs (quand chercher/capturer)
- Format de citations

**Pas besoin de skills/rules files par agent.** Le serveur MCP est auto-documenté.
