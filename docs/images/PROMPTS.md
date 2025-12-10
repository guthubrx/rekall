# Prompts pour Génération d'Images

## 1. Logo Principal (logo.png / logo.svg)

### Option A - Style Cerveau/Mémoire
```
Create a minimalist, modern logo icon for "Rekall" - a developer knowledge management tool inspired by the Total Recall movie concept of perfect memory.

Concept: A stylized brain silhouette merged with a database cylinder or memory chip circuit pattern, suggesting "total recall" of developer knowledge.

Style:
- Flat design, works in single color (monochrome compatible)
- Clean geometric shapes
- No text, icon only
- Transparent background
- SVG-friendly (simple vector paths, no gradients)

Color: Deep purple (#7C3AED) as primary

Mood: Professional, tech-forward, subtly sci-fi but corporate-appropriate

Dimensions: Square aspect ratio, 512x512px minimum
Export: PNG with transparency + SVG if possible

DO NOT include: Text, complex gradients, realistic brain imagery, too many details
```

### Option B - Style Graphe/Connexions
```
Create a minimalist logo icon for "Rekall" - a knowledge management system for developers.

Concept: Interconnected nodes forming a subtle "R" shape, representing a knowledge graph where memories/entries are linked together.

Style:
- Flat geometric design
- 4-6 circular nodes connected by lines
- Nodes arranged to suggest the letter "R" without being obvious
- Single color, works in monochrome
- Transparent background
- Clean, modern, tech aesthetic

Color: Teal (#0D9488) or Purple (#7C3AED)

Dimensions: 512x512px square
Format: PNG transparent + SVG

DO NOT include: Text, gradients, 3D effects, too many nodes
```

### Option C - Style Terminal/CLI
```
Create a minimalist logo for "Rekall" - a CLI tool for developer knowledge management.

Concept: A command prompt cursor (block or underscore) combined with a circular "recall" arrow or refresh symbol, suggesting retrieving stored memories.

Style:
- Ultra-minimal, 2-3 elements max
- Geometric shapes only
- Works at small sizes (favicon)
- Single flat color
- Transparent background

Color: Green (#10B981) terminal-style or Purple (#7C3AED)

Dimensions: 512x512px
Format: PNG + SVG

DO NOT include: Text, realistic elements, complex shapes
```

---

## 2. Banner/Header (banner.png)

```
Create a wide banner image for a GitHub README header.

Content: The word "REKALL" in a clean, modern tech font with a subtle brain/circuit pattern in the background.

Style:
- Dark background (#0D1117 GitHub dark) or transparent
- Text in white or light purple (#A78BFA)
- Subtle geometric pattern (hexagons, circuits, or neural network nodes)
- Very clean, not cluttered

Dimensions: 1200x300px (4:1 ratio)
Format: PNG

Mood: Professional developer tool, not gaming or entertainment
```

---

## 3. Diagramme Architecture (architecture.png)

```
Create a clean technical architecture diagram for a knowledge management system.

Components to show (left to right flow):
1. Input sources: "CLI" and "TUI" boxes
2. Core engine: "SQLite + FTS5" database icon, "Embeddings" brain icon, "SM-2 Scheduler" calendar icon
3. Output: "MCP Server" connected to "AI Assistants" (Claude, Cursor icons)

Style:
- Flat design with rounded rectangles
- Arrows showing data flow
- Color scheme: Purple (#7C3AED) primary, Gray (#6B7280) secondary
- White or transparent background
- Icons inside boxes, labels below

Dimensions: 1000x400px
Format: PNG or SVG

DO NOT include: 3D effects, photos, complex illustrations
```

---

## 4. Amélioration Screenshot Terminal

Si tu as un screenshot terminal à améliorer:

```
Enhance this terminal screenshot for documentation:
- Add subtle drop shadow (10px blur, 20% opacity black)
- Round corners (12px radius)
- Add thin border (1px #333333)
- Ensure crisp text rendering
- Add slight padding around the terminal (20px)
- Background: Keep terminal black, outer padding transparent or #0D1117

Keep authentic terminal aesthetic, don't over-stylize or add fake elements.
```

---

## Outils Recommandés

| Outil | Usage | Lien |
|-------|-------|------|
| **Midjourney** | Logos créatifs | midjourney.com |
| **DALL-E 3** | Logos simples | ChatGPT Plus |
| **Ideogram** | Texte dans images | ideogram.ai |
| **Recraft** | Logos vectoriels | recraft.ai |
| **Figma** | Retouches finales | figma.com |

## Fichiers Attendus

```
docs/images/
├── logo.png          # 512x512, transparent
├── logo.svg          # Version vectorielle
├── banner.png        # 1200x300, header README
├── architecture.png  # Diagramme technique
└── PROMPTS.md        # Ce fichier
```
