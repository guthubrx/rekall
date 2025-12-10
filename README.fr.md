# Rekall

```
        ██████╗ ███████╗██╗  ██╗ █████╗ ██╗     ██╗
        ██╔══██╗██╔════╝██║ ██╔╝██╔══██╗██║     ██║
        ██████╔╝█████╗  █████╔╝ ███████║██║     ██║
        ██╔══██╗██╔══╝  ██╔═██╗ ██╔══██║██║     ██║
        ██║  ██║███████╗██║  ██╗██║  ██║███████╗███████╗
        ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝╚══════╝
```

> *"Get your ass to Mars. Quaid... crush those bugs"*

**Arrêtez de perdre vos connaissances. Commencez à vous en souvenir.**

Rekall est un système de gestion des connaissances pour développeurs avec **mémoire cognitive** et **recherche sémantique**. Il ne se contente pas de stocker vos connaissances — il vous aide à vous en *souvenir* et à les *retrouver* comme le fait votre cerveau.

[![Version](https://img.shields.io/badge/version-0.3.0-blue.svg)](CHANGELOG.md)
[![Python](https://img.shields.io/badge/python-3.9+-green.svg)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-brightgreen.svg)](LICENSE)

**Traductions :** [English](README.md) | [Español](README.es.md) | [Deutsch](README.de.md) | [中文](README.zh-CN.md)

---

## Pourquoi Rekall ?

```
Vous (il y a 3 mois)          Vous (aujourd'hui)
     │                           │
     ▼                           ▼
┌─────────────┐           ┌─────────────┐
│ Fix bug X   │           │ Même bug X  │
│ 2h recherche│           │ repart de   │
│ Trouvé !    │           │ zéro...     │
└─────────────┘           └─────────────┘
     │                           │
     ▼                           ▼
   (perdu)                   (2h encore)
```

**Vous avez déjà résolu ça.** Mais où était cette solution déjà ?

Avec Rekall :

```
┌─────────────────────────────────────────┐
│ $ rekall search "import circulaire"     │
│                                         │
│ [1] bug: Fix: import circulaire models  │
│     Score: ████████░░ 85%               │
│     Situation: Cycle d'import entre     │
│                user.py et profile.py    │
│     Solution: Extraire types partagés   │
│               vers types/common.py      │
└─────────────────────────────────────────┘
```

**Trouvé en 5 secondes. Pas de cloud. Pas d'abonnement.**

---

## Fonctionnalités

| Fonctionnalité | Description |
|----------------|-------------|
| **Recherche sémantique** | Trouver par le sens, pas seulement les mots-clés |
| **Contexte structuré** | Capturer situation, solution et mots-clés |
| **Graphe de connaissances** | Lier les entrées entre elles |
| **Mémoire cognitive** | Distinguer épisodes et patterns |
| **Répétition espacée** | Réviser à intervalles optimaux |
| **Serveur MCP** | Intégration agents IA (Claude, etc.) |
| **100% Local** | Vos données ne quittent jamais votre machine |
| **Interface TUI** | Belle interface terminal avec Textual |

---

## Installation

```bash
# Avec uv (recommandé)
uv tool install git+https://github.com/guthubrx/rekall.git

# Avec pipx
pipx install git+https://github.com/guthubrx/rekall.git

# Vérifier l'installation
rekall version
```

---

## Démarrage rapide

### 1. Capturer une connaissance avec contexte

```bash
# Entrée simple
rekall add bug "Fix: import circulaire dans models" -t python,import

# Avec contexte structuré (recommandé)
rekall add bug "Fix: import circulaire" --context-interactive
# > Situation: Cycle d'import entre user.py et profile.py
# > Solution: Extraire types partagés vers types/common.py
# > Mots-clés: circulaire, import, cycle, refactor
```

### 2. Rechercher sémantiquement

```bash
# Recherche textuelle
rekall search "import circulaire"

# Recherche sémantique (trouve concepts similaires)
rekall search "cycle dépendance module" --semantic

# Par mots-clés
rekall search --keywords "import,cycle"
```

### 3. Explorer dans le TUI

```bash
rekall          # Lancer l'interface interactive
```

```
┌─ Rekall ──────────────────────────────────────────────┐
│  Recherche: import circulaire                         │
├───────────────────────────────────────────────────────┤
│  [1] bug: Fix: import circulaire models    85% █████  │
│      python, import | 2024-12-10                      │
│                                                       │
│  [2] pattern: Injection de dépendances     72% ████   │
│      architecture | 2024-11-15                        │
├───────────────────────────────────────────────────────┤
│  [/] Recherche  [a] Ajouter  [Enter] Voir  [s] Config │
└───────────────────────────────────────────────────────┘
```

---

## Contexte structuré

Chaque entrée peut avoir un contexte riche qui la rend trouvable :

```bash
rekall add bug "Erreur CORS sur Safari" --context-json '{
  "situation": "Safari bloque les requêtes cross-origin malgré les headers CORS",
  "solution": "Ajouter credentials: include et les bons headers Access-Control",
  "trigger_keywords": ["cors", "safari", "cross-origin", "credentials"]
}'
```

Ou en mode interactif :

```bash
rekall add bug "Erreur CORS sur Safari" --context-interactive
```

Cela capture :
- **Situation** : Que se passait-il ? Quels étaient les symptômes ?
- **Solution** : Qu'est-ce qui a corrigé ? Quelle était la cause racine ?
- **Mots-clés** : Mots déclencheurs pour retrouver ça plus tard

---

## Recherche sémantique

Rekall utilise des embeddings locaux pour trouver par le sens :

```bash
# Activer la recherche sémantique
rekall embeddings --status      # Vérifier le statut
rekall embeddings --migrate     # Générer embeddings pour entrées existantes

# Rechercher par le sens
rekall search "timeout authentification" --semantic
```

La recherche combine :
- **Recherche plein texte** (50%) - Correspondance exacte de mots-clés
- **Similarité sémantique** (30%) - Correspondance par le sens
- **Correspondance mots-clés** (20%) - Mots-clés du contexte structuré

---

## Graphe de connaissances

Connectez les entrées liées pour construire un réseau de connaissances :

```
              ┌──────────────────┐
              │  Timeout Auth    │
              │  (Bug #1)        │
              └────────┬─────────┘
                       │ related
          ┌────────────┼────────────┐
          ▼            ▼            ▼
    ┌──────────┐ ┌──────────┐ ┌──────────┐
    │ Timeout  │ │ Timeout  │ │ Timeout  │
    │ DB #2    │ │ API #3   │ │ Cache #4 │
    └────┬─────┘ └────┬─────┘ └──────────┘
         │            │
         └─────┬──────┘
               │ derived_from
               ▼
    ┌────────────────────────────┐
    │   PATTERN: Retry Backoff   │
    │   (Connaissance généralisée)│
    └────────────────────────────┘
```

```bash
rekall link 01HXYZ 01HABC                      # Créer un lien
rekall link 01HXYZ 01HABC --type supersedes    # Avec type de relation
rekall related 01HXYZ                          # Voir les connexions
rekall graph 01HXYZ                            # Visualisation ASCII
```

**Types de liens :** `related`, `supersedes`, `derived_from`, `contradicts`

---

## Mémoire cognitive

Comme votre cerveau, Rekall distingue deux types de mémoire :

### Mémoire épisodique (Ce qui s'est passé)
Événements spécifiques avec contexte complet :
```bash
rekall add bug "Timeout auth sur API prod 15/12" --memory-type episodic
```

### Mémoire sémantique (Ce que vous avez appris)
Patterns abstraits et principes :
```bash
rekall add pattern "Toujours ajouter retry backoff pour APIs externes" --memory-type semantic
```

### Généralisation
Extraire des patterns de plusieurs épisodes :
```bash
rekall generalize 01HA 01HB 01HC --title "Pattern retry pour timeouts"
```

---

## Répétition espacée

Révisez vos connaissances à intervalles optimaux avec l'algorithme SM-2 :

```bash
rekall review              # Démarrer session de révision
rekall review --limit 10   # Réviser 10 entrées
rekall stale               # Trouver connaissances oubliées (30+ jours)
rekall stale --days 7      # Seuil personnalisé
```

Échelle de notation :
- **1** = Complètement oublié
- **3** = Rappelé avec effort
- **5** = Rappel parfait

---

## Serveur MCP (Intégration IA)

Rekall inclut un serveur MCP pour l'intégration avec les assistants IA :

```bash
# Démarrer le serveur MCP
rekall mcp

# Ou configurer dans Claude Desktop / Claude Code
```

**Outils disponibles :**
- `rekall_search` - Rechercher dans la base
- `rekall_add` - Ajouter des entrées
- `rekall_show` - Obtenir détails d'une entrée
- `rekall_link` - Connecter des entrées
- `rekall_suggest` - Obtenir suggestions basées sur embeddings

---

## Intégrations IDE

```bash
rekall install claude     # Claude Code
rekall install cursor     # Cursor AI
rekall install copilot    # GitHub Copilot
rekall install windsurf   # Windsurf
rekall install cline      # Cline
rekall install zed        # Zed
rekall install gemini     # Gemini CLI
rekall install continue   # Continue.dev
```

L'assistant IA va :
1. Chercher dans Rekall avant de résoudre les problèmes
2. Citer vos solutions passées dans ses réponses
3. Suggérer de capturer les nouvelles connaissances après les corrections

---

## Migration & Maintenance

```bash
rekall version             # Afficher version + info schéma
rekall changelog           # Afficher historique des versions
rekall migrate             # Mettre à jour le schéma DB (avec backup)
rekall migrate --dry-run   # Prévisualiser les changements
rekall migrate --enrich-context  # Ajouter contexte structuré aux anciennes entrées
```

---

## Types d'entrées

| Type | Usage | Exemple |
|------|-------|---------|
| `bug` | Bugs corrigés | "Fix: erreur CORS sur Safari" |
| `pattern` | Bonnes pratiques | "Pattern: Repository pattern pour DB" |
| `decision` | Choix d'architecture | "Decision: Utiliser Redis pour sessions" |
| `pitfall` | Erreurs à éviter | "Pitfall: Ne pas utiliser SELECT *" |
| `config` | Astuces de config | "Config: Debug Python dans VS Code" |
| `reference` | Docs externes | "Ref: Documentation React Hooks" |
| `snippet` | Blocs de code | "Snippet: Fonction debounce" |
| `til` | Apprentissages rapides | "TIL: Git rebase -i pour squash" |

---

## Données & Confidentialité

**100% local. Zéro cloud.**

```
Votre machine
     │
     ▼
┌─────────────────────────────────────┐
│  ~/.local/share/rekall/             │
│  ├── rekall.db    (SQLite + FTS5)   │
│  ├── config.toml  (Paramètres)      │
│  └── backups/     (Sauvegardes auto)│
└─────────────────────────────────────┘
     │
     ▼
  Nulle part ailleurs
```

| Plateforme | Emplacement |
|------------|-------------|
| Linux | `~/.local/share/rekall/` |
| macOS | `~/Library/Application Support/rekall/` |
| Windows | `%APPDATA%\rekall\` |

### Partage d'équipe

```bash
rekall init --local   # Crée .rekall/ dans le projet
git add .rekall/      # Commit pour partager avec l'équipe
```

### Export & Sauvegarde

```bash
rekall export backup.rekall.zip                    # Sauvegarde complète
rekall export frontend.zip --project frontend      # Filtré
rekall import backup.rekall.zip --dry-run          # Prévisualiser l'import
```

---

## Référence des commandes

| Commande | Description |
|----------|-------------|
| `rekall` | TUI interactif |
| `rekall add <type> "titre"` | Capturer une connaissance |
| `rekall search "requête"` | Rechercher des entrées |
| `rekall search --semantic` | Recherche sémantique |
| `rekall search --keywords` | Recherche par mots-clés |
| `rekall search --json` | Sortie JSON pour IA |
| `rekall show <id>` | Détails entrée + score |
| `rekall browse` | Parcourir toutes les entrées |
| `rekall link <a> <b>` | Connecter des entrées |
| `rekall unlink <a> <b>` | Supprimer connexion |
| `rekall related <id>` | Afficher entrées liées |
| `rekall graph <id>` | Visualisation graphe ASCII |
| `rekall stale` | Entrées oubliées |
| `rekall review` | Session de répétition espacée |
| `rekall generalize <ids>` | Épisodes vers Pattern |
| `rekall deprecate <id>` | Marquer obsolète |
| `rekall export <fichier>` | Exporter la base |
| `rekall import <fichier>` | Importer archive |
| `rekall install <ide>` | Intégration IDE |
| `rekall embeddings` | Gérer embeddings sémantiques |
| `rekall mcp` | Démarrer serveur MCP |
| `rekall version` | Version et info schéma |
| `rekall changelog` | Historique des versions |
| `rekall migrate` | Mettre à jour la base |

---

## Prérequis

- Python 3.9+
- Aucun service externe
- Aucun internet requis (sauf téléchargement optionnel du modèle d'embedding)
- Aucun compte nécessaire

---

## Licence

MIT

---

**Arrêtez de perdre vos connaissances. Commencez à vous en souvenir.**

```bash
uv tool install git+https://github.com/guthubrx/rekall.git
rekall
```
