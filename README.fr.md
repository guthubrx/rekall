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

**Traductions :** [English](README.md) | [Español](README.es.md) | [Deutsch](README.de.md) | [中文](README.zh-CN.md)

---

## Tu as déjà résolu ce problème.

Il y a trois mois, tu as passé deux heures à débuguer une erreur cryptique. Tu as trouvé la solution. Tu es passé à autre chose.

Aujourd'hui, la même erreur apparaît. Tu la regardes. Elle te dit quelque chose. Mais où était cette solution déjà ?

Tu repars de zéro. Encore deux heures de perdues.

**Ça arrive à tous les développeurs.** Selon les études, les entreprises du Fortune 500 perdent 31,5 milliards de dollars par an parce que les leçons apprises ne sont jamais capturées. Pas par négligence — mais parce qu'on est humains, et les humains oublient.

---

## Et si ton assistant IA se souvenait pour toi ?

Imagine : tu demandes à Claude ou Cursor de corriger un bug. Avant d'écrire une seule ligne de code, il consulte ta base de connaissances personnelle :

```
🔍 Recherche dans tes connaissances...

2 entrées pertinentes trouvées :

[1] bug: Erreur CORS sur Safari (85% de correspondance)
    "Ajouter credentials: include et les bons headers Access-Control"
    → Tu as résolu ça il y a 3 mois

[2] pattern: Gestion des requêtes cross-origin (72% de correspondance)
    "Toujours tester sur Safari - il est plus strict sur CORS"
    → Pattern extrait de 4 bugs similaires
```

Ton assistant IA a maintenant du contexte. Il sait ce qui a marché avant. Il ne va pas réinventer la roue — il va construire sur ton expérience passée.

**C'est ça, Rekall.**

---

## Un second cerveau qui pense comme toi

Rekall n'est pas juste une appli de notes. Il est construit sur le fonctionnement réel de la mémoire humaine :

### Tes connaissances, connectées

Quand tu résous quelque chose, les connaissances liées remontent automatiquement. Tu as corrigé un bug de timeout ? Rekall te montre les trois autres problèmes de timeout que tu as résolus et le pattern de retry que tu en as extrait.

```
              ┌──────────────┐
              │ Auth Timeout │
              │ (aujourd'hui)│
              └──────┬───────┘
                     │ similaire à...
        ┌────────────┼────────────┐
        ▼            ▼            ▼
  ┌──────────┐ ┌──────────┐ ┌──────────┐
  │ DB #47   │ │ API #52  │ │ Cache #61│
  │(2 semaines)│ │ (1 mois) │ │ (3 mois) │
  └────┬─────┘ └────┬─────┘ └──────────┘
       └──────┬─────┘
              ▼
     ┌─────────────────┐
     │ PATTERN: Retry  │
     │ avec backoff    │
     └─────────────────┘
```

### Les événements deviennent sagesse

Chaque bug que tu corriges est un **épisode** — un événement spécifique avec son contexte. Mais des patterns émergent. Après avoir corrigé trois bugs de timeout similaires, Rekall t'aide à extraire le **principe** : "Toujours ajouter du retry avec backoff exponentiel pour les APIs externes."

Les épisodes sont la matière première. Les patterns sont la connaissance réutilisable.

### Les connaissances oubliées refont surface

Rekall suit ce que tu consultes et quand. Une connaissance que tu n'as pas touchée depuis des mois ? Il te la rappellera avant qu'elle ne s'efface complètement. Pense à ça comme de la répétition espacée pour ton cerveau de dev.

---

## Comment ça marche en pratique

### 1. Capture tes connaissances au fil du travail

Après avoir résolu quelque chose de compliqué, capture-le en 10 secondes :

```bash
rekall add bug "CORS échoue sur Safari" --context-interactive
```

Rekall demande : *Que se passait-il ? Qu'est-ce qui a corrigé ? Quels mots-clés devraient déclencher cette entrée ?*

```
> Situation: Safari bloque les requêtes même avec les headers CORS
> Solution: Ajouter credentials: 'include' et Allow-Origin explicite
> Mots-clés: cors, safari, cross-origin, fetch, credentials
```

C'est fait. Ton futur toi te remerciera.

### 2. Cherche par le sens, pas juste les mots-clés

Tu ne te souviens plus si tu avais appelé ça "CORS" ou "cross-origin" ? Peu importe.

```bash
rekall search "navigateur qui bloque mes appels API"
```

Rekall comprend le sens. Il trouve les entrées pertinentes même quand tes mots ne correspondent pas exactement.

### 3. Laisse ton assistant IA l'utiliser

Connecte Rekall à Claude, Cursor, ou tout IA compatible MCP :

```bash
rekall mcp  # Démarre le serveur
```

Maintenant ton IA consulte tes connaissances avant chaque correction. Il cite tes solutions passées. Il propose d'en sauvegarder de nouvelles. Tes connaissances s'accumulent au fil du temps.

---

## L'interface

### Interface terminal
```bash
rekall  # Lance l'interface visuelle
```

```
┌─ Rekall ────────────────────────────────────────────────┐
│  🔍 Recherche: cors safari                              │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  [1] bug: CORS échoue sur Safari           85% ██████   │
│      safari, cors, fetch  •  il y a 3 mois              │
│      "Ajouter credentials: include..."                  │
│                                                         │
│  [2] pattern: Gestion cross-origin         72% █████    │
│      architecture  •  il y a 1 mois                     │
│      "Safari est plus strict sur CORS"                  │
│                                                         │
│  [3] reference: Guide CORS MDN             68% ████     │
│      docs, mdn  •  il y a 6 mois                        │
│                                                         │
├─────────────────────────────────────────────────────────┤
│  [/] Recherche  [a] Ajouter  [Enter] Voir  [q] Quitter  │
└─────────────────────────────────────────────────────────┘
```

### Ligne de commande
```bash
rekall add bug "Fix: null pointer dans auth" -t auth,null
rekall search "erreur authentification"
rekall show 01HX7...
rekall link 01HX7 01HY2 --type related
rekall review  # Session de répétition espacée
```

---

## Qu'est-ce que tu peux capturer ?

| Type | Pour | Exemple |
|------|------|---------|
| `bug` | Problèmes résolus | "CORS Safari avec credentials" |
| `pattern` | Approches réutilisables | "Retry avec backoff exponentiel" |
| `decision` | Pourquoi X plutôt que Y | "PostgreSQL plutôt que MongoDB pour ce projet" |
| `pitfall` | Erreurs à éviter | "Jamais de SELECT * en production" |
| `config` | Config qui marche | "Config debug Python VS Code" |
| `reference` | Docs/liens utiles | "Cette réponse StackOverflow là" |
| `snippet` | Code à garder | "Fonction debounce générique" |
| `til` | Apprentissages rapides | "Git rebase -i peut réordonner les commits" |

---

## 100% local. 100% à toi.

```
Ta machine
     │
     ▼
┌─────────────────────────────────────┐
│  ~/.local/share/rekall/             │
│                                     │
│  Tout reste ici.                    │
│  Pas de cloud. Pas de compte.       │
│  Pas de tracking.                   │
│                                     │
└─────────────────────────────────────┘
     │
     ▼
  Nulle part ailleurs. Jamais.
```

Tes connaissances t'appartiennent. Rekall ne téléphone pas à la maison. Il ne nécessite pas de compte. Il marche hors ligne. Ton historique de debug, tes décisions d'architecture, ta sagesse durement acquise — tout privé, tout local.

---

## Pour commencer

### Installation

```bash
# Avec uv (recommandé)
uv tool install git+https://github.com/guthubrx/rekall.git

# Avec pipx
pipx install git+https://github.com/guthubrx/rekall.git
```

### Essaie

```bash
# Ajoute ta première entrée
rekall add bug "Mon premier bug capturé" -t test

# Recherche-la
rekall search "premier"

# Ouvre l'interface visuelle
rekall
```

### Connecte ton assistant IA

Pour Claude Code, Cursor, ou tout outil compatible MCP :

```bash
rekall mcp  # Expose Rekall à ton IA
```

Maintenant ton IA peut chercher dans tes connaissances, suggérer des liens, et aider à capturer de nouvelles entrées — le tout automatiquement.

---

## Basé sur la science

Rekall n'est pas juste pratique — il est construit sur la recherche en sciences cognitives :

- **Les graphes de connaissances** améliorent la précision de récupération de 20% (les connaissances connectées sont plus faciles à trouver)
- **La répétition espacée** améliore la rétention de 6-9% (réviser au bon moment compte)
- **Mémoire épisodique vs sémantique** — c'est comme ça que ton cerveau organise vraiment l'information
- **La localisation de bugs basée sur l'historique** montre que les fichiers avec des bugs passés ont plus de chances d'en avoir de nouveaux

On a lu les papiers de recherche pour que tu n'aies pas à le faire. Puis on a construit un outil qui les applique.

---

## En savoir plus

| Ressource | Description |
|-----------|-------------|
| `rekall --help` | Référence complète des commandes |
| `rekall version` | Version et info base de données |
| `rekall changelog` | Quoi de neuf |
| [CHANGELOG.md](CHANGELOG.md) | Historique détaillé des versions |

---

## Prérequis

- Python 3.9+
- C'est tout. Pas de services cloud. Pas de clés API (sauf si tu veux la recherche sémantique). Pas de compte.

---

## Licence

MIT — Fais-en ce que tu veux.

---

<p align="center">
<strong>Arrête de perdre tes connaissances. Commence à te souvenir.</strong>
<br><br>

```bash
uv tool install git+https://github.com/guthubrx/rekall.git
rekall
```
</p>
