# Stratégie : Forcer l'Agent à Bien Utiliser Rekall

**Date** : 2025-12-10
**Statut** : Vision / Pitch

---

## Le Problème Fondamental

### Aujourd'hui : Système Passif

```
┌─────────────────────────────────────────────────────────────┐
│ AGENT                          REKALL                       │
│                                                             │
│ [résout un bug]                                             │
│ [oublie de sauvegarder]  ──X──  (attend passivement)       │
│                                                             │
│ [user demande: "sauvegarde"]                                │
│ [appelle rekall_add]     ────>  (stocke ce qu'on lui donne)│
│ [oublie --context]              (stocke sans contexte)      │
│ [oublie --reason]               (liens sans justification)  │
└─────────────────────────────────────────────────────────────┘
```

**Résultat** : Mémoire incomplète, inutilisable pour désambiguïser.

---

## La Stratégie : 3 Niveaux de "Forçage"

### Niveau 1 : Contraintes Techniques (MCP Schema)

**Principe** : Rendre physiquement impossible de mal faire.

```json
// AVANT : tout optionnel
{
  "required": ["type", "title"]
}

// APRÈS : contexte obligatoire
{
  "required": ["type", "title", "context"],
  "properties": {
    "context": {
      "type": "object",
      "required": ["situation", "solution", "trigger_keywords"],
      "properties": {
        "situation": { "description": "Quel était le problème initial ?" },
        "solution": { "description": "Comment l'as-tu résolu ?" },
        "trigger_keywords": { "description": "Mots-clés pour retrouver" }
      }
    }
  }
}
```

**L'agent NE PEUT PAS appeler `rekall_add` sans fournir le contexte structuré.**

### Niveau 2 : Guidance par le Prompt (MCP Description)

**Principe** : Instruire l'agent sur QUAND et COMMENT utiliser Rekall.

```python
REKALL_SYSTEM_PROMPT = """
## Quand créer une entrée Rekall

AUTOMATIQUEMENT après :
- Résolution d'un bug → type="bug"
- Découverte d'un pattern réutilisable → type="pattern"
- Décision d'architecture → type="decision"
- Piège évité → type="pitfall"

## Comment remplir le contexte

OBLIGATOIRE - Structure :
{
  "situation": "L'utilisateur avait une erreur 504 sur /api/export",
  "solution": "Augmenté proxy_read_timeout de 30s à 120s dans nginx.conf",
  "what_failed": "Augmenter timeout côté client n'a pas marché",
  "trigger_keywords": ["504", "nginx", "timeout", "proxy_read_timeout"]
}

## Exemple complet

Après avoir résolu un bug :
rekall_add(
  type="bug",
  title="Fix 504 Gateway Timeout nginx",
  content="## Problème\\n504 sur endpoint long...\\n## Solution\\n...",
  context={
    "situation": "API timeout sur requêtes > 30s",
    "solution": "nginx proxy_read_timeout 120s",
    "what_failed": "Client-side timeout increase",
    "trigger_keywords": ["504", "nginx", "timeout"]
  }
)
"""
```

### Niveau 3 : Auto-Détection et Rappel (Proactif)

**Principe** : Le système détecte quand l'agent DEVRAIT sauvegarder.

```
┌─────────────────────────────────────────────────────────────┐
│ CONVERSATION                                                │
├─────────────────────────────────────────────────────────────┤
│ User: "J'ai une erreur 504"                                 │
│ Agent: [diagnostique, modifie nginx.conf, teste]            │
│ Agent: "C'est résolu, j'ai augmenté le timeout"            │
│                                                             │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ 🧠 REKALL HOOK DÉTECTE :                                │ │
│ │ • Pattern "résolu/fixed/corrigé" détecté                │ │
│ │ • Fichier modifié: nginx.conf                           │ │
│ │ • Contexte: erreur 504                                  │ │
│ │                                                         │ │
│ │ → Injecter rappel: "N'oublie pas de sauvegarder        │ │
│ │   cette solution dans Rekall avec le contexte complet" │ │
│ └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

---

## Nature Fondamentale des Changements

### Changement 1 : De "Stockage" à "Capture"

| Avant | Après |
|-------|-------|
| L'agent **décide** quoi stocker | Le système **capture** automatiquement |
| Contexte = texte libre optionnel | Contexte = structure obligatoire |
| L'agent écrit le contexte | Le contexte est **extrait** de la conversation |

```python
# AVANT : L'agent écrit manuellement
rekall_add(title="Fix bug", content="...", context="optionnel")

# APRÈS : Le système capture automatiquement
rekall_add(
    title="Fix bug",
    content="...",
    context={
        "conversation_excerpt": auto_captured(),  # 10 derniers messages
        "files_modified": auto_detected(),        # via git diff
        "situation": required_field(),            # agent DOIT remplir
        "solution": required_field(),             # agent DOIT remplir
    }
)
```

### Changement 2 : De "Optionnel" à "Obligatoire"

| Champ | Avant | Après |
|-------|-------|-------|
| `context.situation` | N/A | **REQUIRED** |
| `context.solution` | N/A | **REQUIRED** |
| `context.trigger_keywords` | N/A | **REQUIRED** |
| `link.reason` | Optionnel | **REQUIRED** |

**Conséquence** : L'appel MCP **échoue** si ces champs manquent.

### Changement 3 : De "Passif" à "Proactif"

| Avant | Après |
|-------|-------|
| Rekall attend qu'on l'appelle | Rekall suggère quand sauvegarder |
| Pas de feedback | Rappels contextuels |
| Aucune validation | Validation de la qualité |

---

## Architecture Cible

```
┌─────────────────────────────────────────────────────────────┐
│                    CONVERSATION                             │
│                         │                                   │
│                         ▼                                   │
│              ┌──────────────────────┐                       │
│              │ DÉTECTEUR DE MOMENTS │                       │
│              │ "bug résolu"         │                       │
│              │ "pattern découvert"  │                       │
│              │ "décision prise"     │                       │
│              └──────────┬───────────┘                       │
│                         │                                   │
│                         ▼                                   │
│              ┌──────────────────────┐                       │
│              │ EXTRACTEUR CONTEXTE  │                       │
│              │ • Conversation brute │                       │
│              │ • Fichiers modifiés  │                       │
│              │ • Erreurs rencontrées│                       │
│              └──────────┬───────────┘                       │
│                         │                                   │
│                         ▼                                   │
│              ┌──────────────────────┐                       │
│              │ GÉNÉRATEUR STRUCTURE │◄── LLM extraction     │
│              │ • situation          │                       │
│              │ • solution           │                       │
│              │ • what_failed        │                       │
│              │ • keywords           │                       │
│              └──────────┬───────────┘                       │
│                         │                                   │
│                         ▼                                   │
│              ┌──────────────────────┐                       │
│              │ VALIDATEUR           │                       │
│              │ • Champs requis OK ? │                       │
│              │ • Keywords pertinents?│                       │
│              │ • Liens suggérés ?   │                       │
│              └──────────┬───────────┘                       │
│                         │                                   │
│                         ▼                                   │
│                    ┌─────────┐                              │
│                    │ REKALL  │                              │
│                    │   DB    │                              │
│                    └─────────┘                              │
└─────────────────────────────────────────────────────────────┘
```

---

## Plan d'Implémentation par Priorité

| Phase | Quoi | Impact | Effort |
|-------|------|--------|--------|
| **1** | Schema MCP avec context obligatoire | Force la structure | Faible |
| **2** | Prompt système enrichi | Guide l'agent | Faible |
| **3** | Auto-extraction keywords | Réduit effort agent | Moyen |
| **4** | Hook de rappel | Proactif | Moyen |
| **5** | Consolidation auto | Mémoire sémantique | Élevé |

---

## Pitch One-Liner

> **Rekall** : La mémoire qui ne laisse pas l'IA oublier.

## Pitch Court

> Les agents IA résolvent des problèmes puis les oublient. Rekall capture automatiquement le contexte de chaque solution, structure les connaissances, et force l'agent à documenter ce qu'il apprend. Résultat : une mémoire persistante qui s'améliore à chaque interaction.

## Pitch Complet

> **Le problème** : Les agents IA sont amnésiques. Ils résolvent le même bug 10 fois, oublient les décisions d'architecture, et ne capitalisent jamais sur leurs découvertes.
>
> **La solution** : Rekall transforme chaque session de travail en connaissance durable. Plutôt que d'attendre passivement que l'agent sauvegarde (il oublie), Rekall :
> - **Force** la capture de contexte structuré (schema obligatoire)
> - **Guide** l'agent sur quand et comment sauvegarder (prompts enrichis)
> - **Détecte** les moments où une sauvegarde est pertinente (hooks proactifs)
> - **Consolide** les souvenirs épisodiques en patterns réutilisables (mémoire sémantique)
>
> **Le résultat** : Un agent qui apprend vraiment de ses expériences.

---

*Document créé le 2025-12-10 - Rekall v0.5+*
