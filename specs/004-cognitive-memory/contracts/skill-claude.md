# Skill Claude Code Contract : Rekall Cognitive

**Date** : 2025-12-09
**Feature** : 004-cognitive-memory
**User Stories** : US2 (consultation), US3 (capture), US7 (généralisation)

---

## Fichier skill

**Emplacement** : `~/.claude/skills/rekall.md`

---

## Structure du skill

```markdown
---
name: rekall
description: Consultation automatique Rekall avant tâches dev, capture après résolution
---

## Déclencheurs de consultation (US2)

### Quand consulter automatiquement

L'agent DOIT exécuter `rekall search` AVANT de commencer :

| Contexte détecté | Requête Rekall |
|------------------|----------------|
| Bug fix demandé | `rekall search "bug {keywords}" --limit 5` |
| Feature/refactor | `rekall search "pattern {keywords}" --limit 5` |
| Choix technique | `rekall search "decision {keywords}" --limit 5` |
| Configuration | `rekall search "config {keywords}" --limit 5` |

### Extraction des keywords

Extraire de la demande utilisateur :
- Technologies mentionnées (React, Python, SQLite...)
- Noms de fichiers/modules
- Descriptions d'erreur
- Concepts techniques

### Architecture deux audiences

L'agent reçoit des données JSON complètes pour raisonner, puis présente un résumé lisible à l'humain.

```
Rekall CLI (--json) → Skill Claude (logique) → Humain (lecture)
```

### Format JSON pour l'agent (FR-008a)

```bash
rekall search "auth timeout" --json
```

```json
{
  "query": "auth timeout",
  "results": [{
    "id": "01HXYZ...",
    "type": "bug",
    "title": "Timeout auth API",
    "content": "## Problème\nTimeout 5s insuffisant...",
    "tags": ["auth", "api", "timeout"],
    "project": "backend-api",
    "confidence": 4,
    "consolidation_score": 0.89,
    "access_count": 12,
    "last_accessed": "2025-12-07",
    "relevance_score": 0.85,
    "links": {
      "outgoing": [{"target_id": "01HABC", "type": "related"}],
      "incoming": []
    }
  }],
  "total_count": 3,
  "context_matches": {"project": true, "tags": ["auth"]}
}
```

### Format humain (FR-008b)

L'agent présente à l'humain avec citations inline :

```
🧠 Rekall: 3 connaissances pertinentes

D'après « Timeout auth API » [1], le timeout par défaut de 5s est
insuffisant en production. La solution recommandée selon
« Pattern retry backoff » [2] est d'implémenter un retry exponentiel.

---
Références:
[1] 01HXYZ - bug - Timeout auth API
[2] 01HABC - pattern - Pattern retry backoff
[3] 01HDEF - config - Config timeout services
```

### Score de pertinence

Formule combinée :
```
relevance = (FTS × 0.4) + (context_match × 0.35) + (meta_quality × 0.25)
```

Seuils d'affichage :
- `> 0.7` : Détail complet
- `0.4 - 0.7` : Résumé
- `< 0.4` : Non affiché

### Aucun résultat (FR-009)

```
🧠 Rekall: Aucune connaissance trouvée pour "nouveau-sujet"

Je procède sans contexte historique.
💡 Si cette tâche produit des connaissances utiles, je proposerai
   de les capturer à la fin.
```

---

## Déclencheurs de capture (US3)

### Quand proposer la capture

L'agent DOIT proposer de capturer après :

| Événement | Type suggéré |
|-----------|--------------|
| Bug résolu | `bug` |
| Décision technique prise | `decision` |
| Pattern découvert/utilisé | `pattern` |
| Piège évité | `pitfall` |
| Config trouvée | `config` |
| Référence web utile | `reference` |

### Format de proposition (FR-010, FR-011, FR-012)

```
💾 Connaissance acquise détectée

Je propose de sauvegarder dans Rekall :

**Titre**: Timeout auth API - augmenter à 30s
**Type**: bug
**Tags**: auth, api, timeout, python
**Memory**: episodic

Contenu suggéré:
---
## Problème
Timeout de 5s insuffisant pour l'auth API en production.

## Solution
Augmenter le timeout à 30s dans la config.

## Contexte
Fichier: `src/auth/client.py`
Commit: abc1234
---

Voulez-vous :
1. ✅ Sauvegarder tel quel
2. ✏️ Modifier avant sauvegarde
3. ❌ Ne pas sauvegarder
```

### Exécution de la capture (FR-014)

Si accepté :
```bash
rekall add \
  --type bug \
  --tags auth,api,timeout,python \
  --memory-type episodic \
  --confidence 4 \
  "Timeout auth API - augmenter à 30s"
```

Puis ouvrir l'éditeur pour le contenu, ou utiliser stdin.

---

## Propositions de liens (US7)

### Détection de similarité

Après création d'une entrée, si des entrées similaires existent :

```
🔗 Entrées potentiellement liées détectées

L'entrée que vous venez de créer pourrait être liée à :

1. [bug] "Timeout auth API v1" (01HDEF)
   → Similarité: 85% (même contexte auth/timeout)

2. [pattern] "Pattern retry backoff" (01HGHI)
   → Similarité: 60% (pattern applicable)

Voulez-vous créer des liens ?
- [1] Lier à #1 comme "related"
- [2] Lier à #2 comme "derived_from"
- [3] Lier aux deux
- [4] Ignorer
```

### Suggestion de généralisation

Si 3+ entrées épisodiques similaires :

```
💡 Opportunité de généralisation

Vous avez 3 entrées épisodiques similaires sur "timeout auth":
- 01HXYZ "Timeout auth v1"
- 01HABC "Timeout auth staging"
- 01HDEF "Timeout auth prod"

Voulez-vous généraliser en pattern sémantique ?
→ `rekall generalize 01HXYZ 01HABC 01HDEF`
```

---

## Règles de comportement

### Priorités

1. **Consultation AVANT action** - Toujours chercher dans Rekall avant de proposer une solution
2. **Citation des sources** - Toujours mentionner les IDs Rekall utilisés
3. **Capture NON intrusive** - Proposer, ne jamais forcer la capture
4. **Liens suggérés** - Proposer des liens, ne jamais les créer automatiquement

### Limitations

- Ne PAS capturer les conversations triviales
- Ne PAS consulter pour les questions non-techniques
- Ne PAS créer de liens sans confirmation utilisateur
- Respecter les refus de capture (ne pas re-proposer la même session)

---

## Exemples d'interactions

### Exemple 1: Bug fix avec consultation

```
User: J'ai un bug de timeout sur l'auth