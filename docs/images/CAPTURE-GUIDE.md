# Guide de Capture - GIF et Screenshots

## Prérequis

### Outil recommandé (macOS)
- **Kap** : https://getkap.co/ (gratuit, open-source)
  - Export GIF optimisé
  - Contrôle FPS et qualité
  - Trim facile

### Alternatives
- **ScreenToGif** (Windows) : https://www.screentogif.com/
- **Peek** (Linux) : https://github.com/phw/peek
- **asciinema** (cross-platform, terminal only) : https://asciinema.org/

---

## 1. GIF de Démonstration (`demo.gif`)

### Dimensions et Format
- **Taille** : 800x500px (ou 1000x600 pour haute résolution)
- **FPS** : 15-20 (bon compromis qualité/taille)
- **Durée** : 30-45 secondes max
- **Taille fichier** : < 5MB (GitHub limite)
- **Format** : GIF optimisé

### Préparation Terminal
```bash
# Agrandir la police du terminal (Cmd + pour zoom)
# Utiliser un thème sombre propre (One Dark, Dracula, etc.)
# Fenêtre : environ 100 colonnes x 30 lignes
```

### Script du GIF (à suivre dans l'ordre)

**Scène 1 - Capture (10s)**
```bash
# Terminal vide, tape lentement pour que ce soit lisible
rekall add bug "CORS fails on Safari" --context-interactive
```

Répondre aux prompts :
```
> Situation: Safari blocks requests even with CORS headers set
> Solution: Add credentials: 'include' and explicit Allow-Origin
> Keywords: cors, safari, cross-origin, fetch, credentials
```

**Scène 2 - Recherche (8s)**
```bash
# Pause 1 seconde, puis :
rekall search "browser blocking API calls"
```

Montrer les résultats avec scores de matching.

**Scène 3 - TUI (12s)**
```bash
# Lancer l'interface
rekall
```

Actions dans la TUI :
1. Taper `/` pour recherche
2. Chercher "cors"
3. Naviguer avec flèches (montrer sélection)
4. Appuyer Enter pour voir détails
5. Appuyer `q` pour quitter

**Scène 4 - Fin (5s)**
```bash
# Montrer le message de sortie ou prompt vide
# Laisser 2 secondes avant de couper
```

### Post-production
1. **Trim** : Couper les temps morts
2. **Speed up** : Accélérer les parties lentes (max 1.5x)
3. **Optimiser** : Réduire couleurs si > 5MB
4. **Boucle** : Configurer en boucle infinie

### Placement dans README
Le GIF est déjà référencé à la ligne ~90 :
```markdown
<p align="center">
  <img src="docs/screenshots/demo.gif" alt="Rekall in action" width="700">
</p>
```

Sauvegarder le fichier dans : `docs/screenshots/demo.gif`

---

## 2. Screenshot TUI (`tui.png`)

### Dimensions
- **Taille** : 1200x800px environ
- **Format** : PNG (qualité max)

### Préparation
```bash
# Créer des données de démo d'abord
rekall add bug "CORS fails on Safari" -t cors,safari,fetch
rekall add bug "PostgreSQL connection timeout" -t postgres,timeout,db
rekall add pattern "Retry with exponential backoff" -t retry,resilience
rekall add decision "JWT over sessions for microservices" -t auth,jwt
rekall add config "VS Code Python debug settings" -t vscode,debug,python
```

### Capture
1. Lancer `rekall`
2. Faire une recherche (ex: `/` puis "timeout")
3. Avoir 3-4 résultats visibles avec scores
4. Screenshot avec **Cmd+Shift+4** (sélection) ou Kap

### Post-production (optionnel)
Avec Figma, Preview, ou outil image :
- Ajouter ombre portée légère (10px blur, 15% opacity)
- Arrondir coins (8-12px radius)
- Ajouter bordure subtile (#333, 1px)
- Padding extérieur (20px)

### Placement
Remplacer le screenshot ASCII dans la section "### Terminal UI" par :
```markdown
<p align="center">
  <img src="docs/screenshots/tui.png" alt="Rekall Terminal UI" width="700">
</p>
```

Sauvegarder dans : `docs/screenshots/tui.png`

---

## 3. Screenshot Recherche (`search.png`)

### Contenu
Montrer une recherche avec résultats hybrides :
```bash
rekall search "browser API problem"
```

### Ce qu'on veut voir
- La requête en haut
- 3-4 résultats avec scores (85%, 72%, etc.)
- Les tags/keywords visibles
- Les dates relatives ("3 months ago")

Sauvegarder dans : `docs/screenshots/search.png`

---

## 4. Screenshot MCP Integration (`mcp.png`)

### Contenu
Si possible, montrer Claude Code ou Cursor utilisant Rekall :
- L'assistant qui affiche "Searching your knowledge..."
- Les résultats trouvés dans la conversation

Sauvegarder dans : `docs/screenshots/mcp.png`

---

## Checklist Finale

```
docs/screenshots/
├── demo.gif       # [ ] GIF workflow complet (< 5MB)
├── tui.png        # [ ] Screenshot interface TUI
├── search.png     # [ ] Screenshot résultats recherche (optionnel)
└── mcp.png        # [ ] Screenshot intégration MCP (optionnel)
```

## Conseils

1. **Police lisible** : Utiliser une taille de police assez grande
2. **Contraste** : Thème sombre avec texte clair
3. **Pas de données sensibles** : Utiliser des exemples génériques
4. **Anglais** : Garder le terminal en anglais pour le README principal
5. **Propre** : Pas de notifications, barre de menu cachée si possible
