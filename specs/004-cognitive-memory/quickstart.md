# Quickstart : Système de Mémoire Cognitive

**Date** : 2025-12-09
**Feature** : 004-cognitive-memory

---

## Prérequis

- Python 3.9+
- Rekall installé (`pip install -e .`)
- Base Rekall initialisée (`rekall init`)

---

## Nouvelles fonctionnalités

### 1. Liens entre entrées

Créer des connexions pour construire un graphe de connaissances :

```bash
# Créer un lien "related"
rekall link 01HXYZ 01HABC

# Créer un lien avec type spécifique
rekall link 01HXYZ 01HABC --type supersedes

# Voir les entrées liées
rekall related 01HXYZ

# Supprimer un lien
rekall unlink 01HXYZ 01HABC
```

**Types de liens disponibles** :
- `related` - Connexion thématique
- `supersedes` - Remplace une entrée obsolète
- `derived_from` - Généralisé depuis des épisodiques
- `contradicts` - Information conflictuelle

---

### 2. Recherche JSON pour agents AI

Sortie JSON complète pour intégration avec agents AI :

```bash
# Format JSON pour agents
rekall search "auth timeout" --json
```

Retourne :
```json
{
  "query": "auth timeout",
  "results": [{
    "id": "01HXYZ...",
    "type": "bug",
    "title": "Timeout auth API",
    "content": "...",
    "relevance_score": 0.85,
    "links": {...}
  }],
  "total_count": 3
}
```

---

### 4. Types de mémoire

Distinguer les connaissances épisodiques (événements) des sémantiques (concepts) :

```bash
# Créer une entrée épisodique (défaut)
rekall add --type bug "Bug timeout 15/12/2024"

# Créer une entrée sémantique
rekall add --type pattern --memory-type semantic "Pattern retry backoff"

# Filtrer par type de mémoire
rekall search "timeout" --memory-type episodic
rekall list --memory-type semantic
```

---

### 5. Tracking et consolidation

Suivre l'accès aux entrées pour identifier les connaissances fragiles :

```bash
# Voir les entrées non consultées depuis 30 jours
rekall stale

# Voir les entrées non consultées depuis 7 jours
rekall stale --days 7
```

L'indicateur de consolidation (0-100%) apparaît dans `rekall show` :
- 🔴 <30% : Fragile (risque d'oubli)
- 🟡 30-70% : Stable
- 🟢 >70% : Consolidée

---

### 6. Révision espacée

Réviser les connaissances avec un système de répétition espacée :

```bash
# Lancer une session de révision
rekall review

# Limiter à 5 entrées
rekall review --limit 5

# Filtrer par projet
rekall review --project myapp
```

Pendant la révision, noter votre rappel (1-5) :
- 1 = Oublié complètement
- 3 = Rappelé avec effort
- 5 = Rappelé parfaitement

L'intervalle de révision s'ajuste automatiquement.

---

### 7. Généralisation

Créer des patterns sémantiques depuis plusieurs expériences :

```bash
# Généraliser 3 bugs similaires en pattern
rekall generalize 01HXYZ 01HABC 01HDEF

# Prévisualiser sans créer
rekall generalize 01HXYZ 01HABC --dry-run
```

---

## Skill Claude Code

### Installation

```bash
rekall install claude
```

Cela installe le skill dans `~/.claude/skills/rekall.md`.

### Utilisation automatique

Le skill active automatiquement :

1. **Consultation avant action** - Claude cherche dans Rekall avant de fixer un bug
2. **Capture après résolution** - Claude propose de sauvegarder les nouvelles connaissances
3. **Suggestion de liens** - Claude propose de lier les entrées similaires

---

## Migration

Les entrées existantes sont automatiquement migrées au premier lancement :

- `memory_type` = "episodic" (défaut)
- `access_count` = 1
- `last_accessed` = date de création

Aucune action requise.

---

## Exemple de workflow complet

```bash
# 1. Consulter avant de travailler
rekall search "auth timeout"

# 2. Travailler sur le bug...

# 3. Capturer la solution
rekall add --type bug --tags auth,timeout "Bug: timeout auth trop court"

# 4. Lier à des entrées existantes
rekall link 01HNEW 01HOLD --type supersedes

# 5. Plus tard, réviser
rekall stale
rekall review

# 6. Généraliser les patterns récurrents
rekall generalize 01HA 01HB 01HC --title "Pattern timeout handling"
```

---

## Commandes résumées

| Commande | Description |
|----------|-------------|
| `rekall link A B` | Créer un lien entre A et B |
| `rekall unlink A B` | Supprimer le lien |
| `rekall related A` | Voir les entrées liées à A |
| `rekall stale` | Entrées non consultées >30j |
| `rekall review` | Session de révision espacée |
| `rekall generalize A B C` | Créer pattern sémantique |
| `rekall add --memory-type` | Spécifier episodic/semantic |
| `rekall search --memory-type` | Filtrer par type mémoire |
| `rekall search --json` | Sortie JSON pour agents AI |
