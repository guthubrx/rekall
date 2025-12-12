# Quickstart: DevKMS

**Installation et premiers pas en moins de 2 minutes.**

---

## Installation

### Via pip (recommandé)

```bash
pip install devkms
```

### Via uv (plus rapide)

```bash
uv tool install devkms
```

### Via pipx (isolation)

```bash
pipx install devkms
```

### Depuis les sources (développement)

```bash
git clone https://github.com/USER/devkms.git
cd devkms
pip install -e .
```

---

## Vérification

```bash
mem --version
# devkms 0.1.0

mem --help
# Usage: mem [OPTIONS] COMMAND [ARGS]...
#
# DevKMS - Developer Knowledge Management System
# Capturez et retrouvez vos bugs, patterns et décisions.
#
# Commands:
#   add        Ajouter une nouvelle entrée
#   search     Rechercher dans la base
#   show       Afficher une entrée
#   browse     Parcourir les entrées
#   export     Exporter la base
#   install    Installer une intégration IDE
#   deprecate  Marquer une entrée obsolète
#   similar    Recherche sémantique (optionnel)
```

---

## Premiers Pas

### 1. Initialiser (automatique au premier usage)

```bash
mem init
# ✓ Base créée: ~/.devkms/knowledge.db
# ✓ Prêt à utiliser !
```

### 2. Ajouter une première entrée

```bash
# Capture rapide
mem add bug "Fix import circulaire React" -t react,import -p mon-projet

# Avec contenu détaillé (ouvre éditeur)
mem add pattern "API Error Handler"
```

### 3. Rechercher

```bash
# Recherche simple
mem search "import circulaire"

# Filtrer par type
mem search "react" --type bug

# Filtrer par projet
mem search "cache" --project mon-projet
```

### 4. Afficher une entrée

```bash
mem show 01ARZ3NDEKTSV4RRFFQ69G5FAV
```

---

## Intégrations IDE

### Claude Code (recommandé)

```bash
mem install claude-code
# ✓ Skills installés dans ~/.claude-plugins/devkms/
```

### Cursor

```bash
mem install cursor
# ✓ Règles ajoutées à .cursorrules
```

### Autres IDE

```bash
mem install --list
# Disponibles:
#   claude-code    Skills Claude Code
#   cursor         .cursorrules
#   copilot        .github/copilot-instructions.md
#   windsurf       .windsurfrules
#   cline          .clinerules
#   aider          CONVENTIONS.md
#   continue       .continue/rules/
#   zed            .rules
```

---

## Types d'Entrées

| Type | Usage | Exemple |
|------|-------|---------|
| `bug` | Bug résolu | "Fix circular import React" |
| `pattern` | Pattern réutilisable | "API Error Handler" |
| `decision` | Décision technique | "Choix Tailwind vs CSS Modules" |
| `pitfall` | Piège à éviter | "Ne pas utiliser useMemo partout" |
| `config` | Configuration | "Setup ESLint + Prettier" |
| `reference` | Documentation | "React 19 breaking changes" |

---

## Niveaux de Confiance

| Niveau | Signification |
|--------|---------------|
| 0 | Hypothèse non vérifiée |
| 1 | Testé une fois |
| 2 | Fonctionne chez moi (défaut) |
| 3 | Testé plusieurs fois |
| 4 | Source fiable (MDN, docs officielles) |
| 5 | Doc officielle / RFC |

```bash
mem add bug "Fix X" -c 4  # Confiance haute
```

---

## Export

```bash
# Markdown (pour autre agent IA)
mem export --format md > knowledge.md

# JSON (backup/migration)
mem export --format json > backup.json
```

---

## Prochaines Étapes

1. **Ajouter des entrées** au fil de votre travail
2. **Rechercher avant de googler** : `mem search "votre problème"`
3. **Installer l'intégration IDE** pour automatisation

---

## Aide

```bash
mem --help              # Aide générale
mem add --help          # Aide commande add
mem search --help       # Aide commande search
```

**Issues/Feedback** : https://github.com/USER/devkms/issues
