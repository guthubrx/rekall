# Patterns CSS Textual - Guide de Reference

Ce document capture les solutions aux problemes CSS Textual rencontres lors du developpement de rekall TUI.

## Centrage d'Overlays SANS Fond Gris

### Le Probleme

Centrer un overlay (popup/modal) horizontalement ET verticalement dans Textual, SANS que le reste de l'ecran soit couvert par un fond gris semi-transparent.

**Ce qu'on voulait:**
- Popup centree H et V
- Reste de l'ecran visible (pas de fond gris)
- Contenu scrollable si depasse

### Approches qui NE FONCTIONNENT PAS

#### 1. `align: center middle` (ECHEC)

```css
#my-overlay {
    layer: modal;
    align: center middle;  /* NE CENTRE PAS l'overlay lui-meme */
    width: 50;
    height: auto;
}
```

**Pourquoi ca echoue:** `align` centre le CONTENU de l'overlay, pas l'overlay lui-meme dans son parent.

#### 2. `offset-x/offset-y` avec pourcentages (ECHEC)

```css
#my-overlay {
    layer: modal;
    offset-x: 50%;
    offset-y: 50%;
    width: 50;
}
```

**Pourquoi ca echoue:** Le decalage est calcule depuis le coin superieur gauche, pas le centre. L'overlay se retrouve en bas a droite.

#### 3. Conteneur parent avec `align` (ECHEC - FOND GRIS)

```css
.modal-container {
    layer: modal;
    width: 100%;
    height: 100%;
    align: center middle;
    background: transparent;  /* IGNORE - le layer ajoute un fond */
}

#my-overlay {
    width: 50;
    height: auto;
}
```

**Pourquoi ca echoue:** Meme avec `background: transparent`, le layer modal ajoute systematiquement un fond gris semi-transparent. C'est le comportement par defaut de Textual pour les modals.

#### 4. `margin: X auto` (ERREUR)

```css
#my-overlay {
    margin: 10 auto;  /* ERREUR: Textual n'accepte pas 'auto' */
}
```

**Pourquoi ca echoue:** Textual CSS n'est PAS du CSS web. La valeur `auto` n'existe pas pour les margins.

### LA SOLUTION QUI FONCTIONNE

#### Pattern: `dock: top` + `margin` fixes calcules

```css
#my-overlay {
    display: none;           /* Cache par defaut */
    layer: modal;            /* Au-dessus de tout */
    dock: top;               /* Ancre en haut */
    width: 50;               /* Largeur fixe */
    height: auto;            /* Hauteur selon contenu */
    max-height: 80%;         /* Limite pour scroll */
    padding: 1 2;
    margin: 10 45;           /* VERTICAL HORIZONTAL */
    background: $surface;
    border: thick $secondary;
}

#my-overlay.visible {
    display: block;
}
```

**Comment calculer le margin horizontal:**

```
Terminal standard = 140 colonnes
Largeur overlay = 50 colonnes
Espace restant = 140 - 50 = 90 colonnes
Margin horizontal = 90 / 2 = 45 colonnes

Donc: margin: VERTICAL 45;
```

**Exemples selon la largeur:**

| Largeur overlay | Calcul margin H | CSS margin |
|-----------------|-----------------|------------|
| 50 colonnes     | (140-50)/2 = 45 | `margin: 10 45` |
| 60 colonnes     | (140-60)/2 = 40 | `margin: 10 40` |
| 80 colonnes     | (140-80)/2 = 30 | `margin: 5 30` |

### Exemples Complets dans rekall

#### 1. Actions Overlay (menu contextuel)

```css
#actions-overlay {
    display: none;
    layer: modal;
    dock: top;
    width: 50;
    height: auto;
    max-height: 80%;
    padding: 1 2;
    margin: 10 45;           /* Centre pour width=50 */
    background: $surface;
    border: thick $secondary;
}

#actions-overlay.visible {
    display: block;
}
```

#### 2. Enrich Overlay (formulaire plus large)

```css
#enrich-overlay {
    display: none;
    layer: modal;
    dock: top;
    width: 80;
    height: auto;
    max-height: 80%;
    padding: 1 2;
    margin: 5 30;            /* Centre pour width=80 */
    background: $surface;
    border: thick #4367CD;   /* Couleur theme */
}

#enrich-overlay.visible {
    display: block;
}
```

#### 3. Filter Overlay (taille moyenne)

```css
#filter-overlay {
    display: none;
    layer: modal;
    dock: top;
    width: 60;
    height: auto;
    max-height: 80%;
    padding: 1 2;
    margin: 10 40;           /* Centre pour width=60 */
    background: $surface;
    border: thick $secondary;
}

#filter-overlay.visible {
    display: block;
}
```

### Toggle de Visibilite en Python

```python
def toggle_overlay(self, overlay_id: str) -> None:
    """Toggle overlay visibility."""
    overlay = self.query_one(f"#{overlay_id}")
    if overlay.has_class("visible"):
        overlay.remove_class("visible")
    else:
        overlay.add_class("visible")
        overlay.focus()
```

### Points Cles a Retenir

1. **`dock: top`** est ESSENTIEL - sans lui, le centrage ne fonctionne pas
2. **`margin: V H`** - les valeurs doivent etre calculees manuellement
3. **`layer: modal`** - necessaire pour etre au-dessus du contenu
4. **`display: none/block`** via classes CSS pour toggle
5. **PAS de `background: transparent`** sur le layer - ca ne fonctionne pas
6. **PAS de `align: center middle`** sur l'overlay - ca ne centre pas l'overlay lui-meme

### Pourquoi Cette Solution Fonctionne

1. `dock: top` ancre l'overlay en haut de l'ecran parent
2. `margin-top` (premier nombre) controle le decalage vertical depuis le haut
3. `margin-left/right` (second nombre) sont appliques des deux cotes, centrant horizontalement
4. `layer: modal` place l'overlay au-dessus de tout mais SANS fond gris puisqu'on n'utilise pas de conteneur fullscreen

### Limitations

- Le centrage depend de la taille du terminal (140 colonnes assumees)
- Si le terminal est redimensionne, le centrage peut etre approximatif
- Pour un centrage parfait adaptatif, il faudrait recalculer en Python lors du resize

---

*Document cree suite aux problemes de centrage rencontres le 2024-12-12 lors de l'implementation des overlays dans UnifiedSourcesApp.*
