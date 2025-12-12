# CLI Commands Contract : Système de Mémoire Cognitive

**Date** : 2025-12-09
**Feature** : 004-cognitive-memory

---

## Commandes existantes (modifiées)

### `rekall add`

**Modification** : Ajout option `--memory-type`

```bash
rekall add [OPTIONS]

Options (nouvelles):
  --memory-type, -m  [episodic|semantic]  Type de mémoire [default: episodic]
```

**Exemples** :
```bash
rekall add --type bug --memory-type episodic "Bug auth timeout"
rekall add --type pattern --memory-type semantic "Pattern retry avec backoff"
```

---

### `rekall show <id>`

**Modification** : Affiche section "Related" et indicateurs cognitifs

**Output enrichi** :
```
┌─────────────────────────────────────────────────────────────┐
│ 01HXYZ... │ Bug auth timeout                    │ bug      │
├─────────────────────────────────────────────────────────────┤
│ Memory: episodic │ Consolidation: ████░░░░░░ 42%            │
│ Accès: 7 fois    │ Dernier: il y a 3 jours                  │
├─────────────────────────────────────────────────────────────┤
│ Content...                                                   │
├─────────────────────────────────────────────────────────────┤
│ Related:                                                     │
│   → [related] 01HABC... "Config timeout serveur"            │
│   ← [derived_from] 01HDEF... "Pattern timeout handling"     │
└─────────────────────────────────────────────────────────────┘
```

---

### `rekall search <query>`

**Modification** : Filtre `--memory-type`, suggestions "Voir aussi"

```bash
rekall search [OPTIONS] <QUERY>

Options (nouvelles):
  --memory-type, -m  [episodic|semantic]  Filtrer par type de mémoire
```

**Output enrichi** (si entrées liées) :
```
Results for "timeout":
  1. [bug] 01HXYZ... "Bug auth timeout"
  2. [pattern] 01HABC... "Pattern retry"

Voir aussi (entrées liées):
  → 01HDEF... "Config timeout" (lié à #1)
```

---

### `rekall delete <id>`

**Modification** : Blocage si liens existent

```bash
rekall delete <ID>

# Si liens existent:
Error: Entry 01HXYZ has 3 links:
  → [related] 01HABC... "Config timeout"
  → [related] 01HDEF... "Pattern retry"
  ← [derived_from] 01HGHI... "Semantic timeout"

Use --force to delete entry and all its links.
```

```bash
rekall delete --force <ID>
# Output: Deleted entry 01HXYZ and 3 links.
```

---

## Nouvelles commandes

### `rekall link <source_id> <target_id>`

**Description** : Créer un lien entre deux entrées (FR-001, FR-002)

```bash
rekall link [OPTIONS] <SOURCE_ID> <TARGET_ID>

Arguments:
  SOURCE_ID  ID de l'entrée source
  TARGET_ID  ID de l'entrée cible

Options:
  --type, -t  [related|supersedes|derived_from|contradicts]  [default: related]
```

**Exemples** :
```bash
rekall link 01HXYZ 01HABC                    # related par défaut
rekall link 01HXYZ 01HABC --type supersedes  # A remplace B
rekall link 01HXYZ 01HABC --type contradicts # Conflit
```

**Output** :
```
Created link: 01HXYZ → [related] → 01HABC
```

**Erreurs** :
```
Error: Entry 01HXYZ not found.
Error: Link already exists: 01HXYZ → [related] → 01HABC
Error: Cannot link entry to itself.
```

---

### `rekall unlink <source_id> <target_id>`

**Description** : Supprimer un lien (FR-005)

```bash
rekall unlink [OPTIONS] <SOURCE_ID> <TARGET_ID>

Options:
  --type, -t  [related|supersedes|derived_from|contradicts]  Type spécifique
              Si non spécifié, supprime tous les liens entre les deux entrées
```

**Exemples** :
```bash
rekall unlink 01HXYZ 01HABC                    # Tous les liens
rekall unlink 01HXYZ 01HABC --type related     # Seulement "related"
```

---

### `rekall related <id>`

**Description** : Afficher toutes les entrées liées (FR-003)

```bash
rekall related [OPTIONS] <ID>

Options:
  --type, -t  [related|supersedes|derived_from|contradicts]  Filtrer par type
  --depth, -d  INTEGER  Profondeur de traversée [default: 1]
```

**Output** :
```
Related to "Bug auth timeout" (01HXYZ):

Outgoing (→):
  [related] 01HABC "Config timeout serveur"
  [supersedes] 01HDEF "Ancien bug timeout"

Incoming (←):
  [derived_from] 01HGHI "Pattern timeout handling"

Total: 3 links
```

---

### `rekall stale [--days N]`

**Description** : Lister les entrées non consultées (FR-021)

```bash
rekall stale [OPTIONS]

Options:
  --days, -d  INTEGER  Jours depuis dernier accès [default: 30]
  --limit, -l  INTEGER  Nombre max de résultats [default: 20]
```

**Output** :
```
Stale entries (not accessed in 30+ days):

  01HXYZ "Bug auth timeout"           │ 45 days │ 🔴 fragile
  01HABC "Config old server"          │ 32 days │ 🟡 fading
  01HDEF "Decision deprecated API"    │ 31 days │ 🟡 fading

3 entries need attention. Consider:
  - rekall review     # Start spaced repetition
  - rekall deprecate  # Mark obsolete if outdated
```

---

### `rekall review`

**Description** : Session de révision espacée (FR-023, FR-024, FR-025)

```bash
rekall review [OPTIONS]

Options:
  --limit, -l  INTEGER  Nombre d'entrées à réviser [default: 10]
  --project, -p  TEXT  Filtrer par projet
```

**Mode interactif** :
```
Review session: 5 entries due

[1/5] Bug auth timeout (01HXYZ)
      Type: bug │ Memory: episodic │ Last reviewed: 7 days ago

      Content preview...

      Rate your recall:
      [1] Forgot  [2] Hard  [3] Good  [4] Easy  [5] Perfect

> 3

Next review: in 14 days
─────────────────────────────────

[2/5] Pattern retry backoff (01HABC)
...
```

**Output final** :
```
Review complete!
  Reviewed: 5 entries
  Average recall: 3.2/5
  Next session: 3 entries due tomorrow
```

---

### `rekall generalize <id> [<id2> ...]`

**Description** : Créer une entrée sémantique depuis épisodiques (FR-017, FR-018)

```bash
rekall generalize [OPTIONS] <IDS>...

Arguments:
  IDS  IDs des entrées épisodiques à généraliser (2 minimum)

Options:
  --title, -t  TEXT  Titre de l'entrée sémantique
  --dry-run         Afficher le draft sans créer
```

**Output** :
```
Analyzing 3 episodic entries...

Common patterns found:
  - All involve timeout errors
  - All resolved by increasing timeout
  - All in authentication context

Draft semantic entry:
─────────────────────────────────
Title: Pattern - Auth timeout handling
Type: pattern
Memory: semantic
Content:
  ## Pattern
  Les timeouts d'authentification sont souvent causés par...

  ## Resolution
  Augmenter le timeout à 30s minimum...

  ## Sources (episodic)
  - 01HXYZ "Bug auth timeout v1"
  - 01HABC "Bug auth timeout v2"
  - 01HDEF "Bug auth timeout staging"
─────────────────────────────────

Create this entry? [y/N]
```

---

## Résumé des commandes

| Commande | User Story | Functional Req |
|----------|------------|----------------|
| `rekall add --memory-type` | US4 | FR-015 |
| `rekall show` (enrichi) | US1, US5 | FR-003, FR-022 |
| `rekall search --memory-type` | US4 | FR-016 |
| `rekall delete --force` | - | Clarif #3 |
| `rekall link` | US1 | FR-001, FR-002 |
| `rekall unlink` | US1 | FR-005 |
| `rekall related` | US1 | FR-003 |
| `rekall stale` | US5 | FR-021 |
| `rekall review` | US6 | FR-023, FR-024, FR-025 |
| `rekall generalize` | US4, US7 | FR-017, FR-018 |
