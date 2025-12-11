<div align="center">

<!-- LOGO: Décommenter quand logo.png est prêt
<img src="docs/images/logo.png" alt="Logo Rekall" width="120">
-->

# Rekall

**Tes connaissances de développeur, rappelées instantanément.**

<p>
  <img src="https://img.shields.io/badge/100%25-Local-blue?style=flat-square" alt="100% Local">
  <img src="https://img.shields.io/badge/Pas_de_clé_API-green?style=flat-square" alt="Pas de clé API">
  <img src="https://img.shields.io/badge/MCP-Compatible-purple?style=flat-square" alt="Compatible MCP">
  <img src="https://img.shields.io/badge/Python-3.9+-yellow?style=flat-square" alt="Python 3.9+">
</p>

*« Get your ass to Mars. Quaid... crush those bugs »*

[Documentation](#sommaire) · [Installation](#pour-commencer) · [Intégration MCP](#serveur-mcp--compatible-avec-tous-les-assistants-ia)

**Traductions :** [English](README.md) | [Español](README.es.md) | [Deutsch](README.de.md) | [中文](README.zh-CN.md)

</div>

---

## Sommaire

- [TL;DR](#tldr)
- [Le problème](#tu-as-déjà-résolu-ce-problème)
- [La solution](#et-si-ton-assistant-ia-se-souvenait-pour-toi-)
- [Comment ça marche](#comment-ça-marche-en-pratique)
- [Interface](#linterface)
- [Ce qu'il automatise](#ce-que-rekall-fait-pour-toi)
- [Types d'entrées](#quest-ce-que-tu-peux-capturer-)
- [Vie privée](#100--local-100--à-toi)
- [Pour commencer](#pour-commencer)
- [Serveur MCP](#serveur-mcp--compatible-avec-tous-les-assistants-ia)
- [Intégration Speckit](#intégration-avec-speckit)
- [Sous le capot](#sous-le-capot--comment-fonctionne-la-recherche) *(technique)*
- [Basé sur la science](#basé-sur-la-science) *(recherche)*

---

### TL;DR

**Le problème :** Chaque développeur a résolu le même bug deux fois. Pas par négligence — parce qu'on est humains, et les humains oublient. Les études montrent que les entreprises Fortune 500 perdent 31,5 milliards de dollars par an en connaissances jamais capturées.

**Notre approche :** Rekall est une base de connaissances personnelle construite sur la recherche en sciences cognitives. On a étudié comment la mémoire humaine fonctionne vraiment — mémoire épisodique vs sémantique, répétition espacée, graphes de connaissances — et on l'a appliqué aux workflows développeur.

**Ce que ça fait :** Capture bugs, patterns, décisions, configs au fil du travail. Recherche par le sens, pas juste les mots-clés — Rekall utilise des embeddings locaux optionnels (EmbeddingGemma) combinés avec la recherche full-text pour trouver les entrées pertinentes même quand tes mots ne correspondent pas exactement. Stocke un contexte riche (situation, solution, ce qui a échoué) pour désambiguïser les problèmes similaires plus tard.

**Compatible avec tes outils :** Rekall expose un serveur MCP compatible avec la plupart des outils de développement IA — Claude Code, Claude Desktop, Cursor, Windsurf, Continue.dev, et tout client MCP. Une commande (`rekall mcp`) et ton IA consulte tes connaissances avant chaque fix.

**Ce qu'il automatise :** Extraction de mots-clés, score de consolidation, détection de patterns, suggestions de liens, planification des révisions (répétition espacée SM-2). Tu te concentres sur la capture — Rekall gère le reste.

```bash
# Installation
uv tool install git+https://github.com/guthubrx/rekall.git

# Capture (le mode interactif te guide)
rekall add bug "CORS échoue sur Safari" --context-interactive

# Recherche (comprend le sens, pas juste les mots-clés)
rekall search "navigateur bloque API"

# Connecte ton IA (une commande, marche avec Claude/Cursor/Windsurf)
rekall mcp
```

---

<br>

## Tu as déjà résolu ce problème.

Il y a trois mois, tu as passé deux heures à débuguer une erreur cryptique. Tu as trouvé la solution. Tu es passé à autre chose.

Aujourd'hui, la même erreur apparaît. Tu la regardes. Elle te dit quelque chose. Mais où était cette solution déjà ?

Tu repars de zéro. Encore deux heures de perdues.

**Ça arrive à tous les développeurs.** Selon les études, les entreprises du Fortune 500 perdent 31,5 milliards de dollars par an parce que les leçons apprises ne sont jamais capturées. Pas par négligence — mais parce qu'on est humains, et les humains oublient.

<br>

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

<p align="center">
  <img src="docs/screenshots/demo.gif" alt="Rekall en action" width="700">
</p>

<!--
Placeholder screenshots - ajoute tes images dans docs/screenshots/
Options:
- demo.gif: GIF animé montrant le workflow (recommandé)
- tui.png: Screenshot de l'interface terminal
- search.png: Résultats de recherche
- mcp.png: Intégration MCP avec Claude/Cursor
-->

<br>

## Un second cerveau qui pense comme toi

> **Idée clé :** Rekall est construit sur le fonctionnement réel de la mémoire humaine — connecter les connaissances liées, extraire des patterns des épisodes, et faire remonter l'information oubliée avant qu'elle ne s'efface.

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

Chaque bug que tu corriges est un **épisode** — un événement spécifique avec son contexte. Mais des patterns émergent. Après avoir corrigé trois bugs de timeout similaires, Rekall t'aide à extraire le **principe** : « Toujours ajouter du retry avec backoff exponentiel pour les APIs externes. »

Les épisodes sont la matière première. Les patterns sont la connaissance réutilisable.

<br>

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

Tu ne te souviens plus si tu avais appelé ça « CORS » ou « cross-origin » ? Peu importe.

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

<br>

## Ce que Rekall fait pour toi

> **Philosophie :** Tu te concentres sur capturer tes connaissances. Rekall gère tout le reste.

### À chaque entrée que tu ajoutes

- **Extraction de mots-clés** — Analyse ton titre et contenu, suggère des keywords pertinents
- **Validation du contexte** — Avertit si la situation/solution est trop vague ou générique
- **Génération d'embeddings** — Crée des vecteurs sémantiques pour la recherche intelligente (si activé)
- **Indexation automatique** — L'index de recherche full-text est mis à jour en temps réel

### À chaque recherche

- **Matching hybride** — Combine mots exacts (FTS5) + sens (embeddings) + déclencheurs (keywords)
- **Zéro configuration** — Fonctionne out of the box, pas de tuning nécessaire
- **Entrées liées** — Affiche automatiquement les connaissances connexes

### En arrière-plan (tu ne fais rien)

- **Tracking d'accès** — Chaque consultation met à jour les stats de fréquence et récence
- **Score de consolidation** — Calcule à quel point chaque mémoire est « stable » (60% fréquence + 40% fraîcheur)
- **Détection de patterns** — Trouve les clusters d'entrées similaires, suggère de créer un pattern
- **Suggestions de liens** — Détecte les entrées connexes, propose des connections
- **Planification des révisions** — L'algorithme SM-2 planifie les moments optimaux de révision (répétition espacée)
- **Compression du contexte** — Stocke le contexte verbeux à 70-85% de taille en moins

### Quand tu lances `rekall review`

- **Charge les entrées dues** — Basé sur la planification SM-2, pas des dates arbitraires
- **Ajuste la difficulté** — Ta note (0-5) met à jour le facteur de facilité automatiquement
- **Replanifie** — Calcule la prochaine date de révision optimale

---

## Qu'est-ce que tu peux capturer ?

| Type | Pour | Exemple |
|------|------|---------|
| `bug` | Problèmes résolus | « CORS Safari avec credentials » |
| `pattern` | Approches réutilisables | « Retry avec backoff exponentiel » |
| `decision` | Pourquoi X plutôt que Y | « PostgreSQL plutôt que MongoDB pour ce projet » |
| `pitfall` | Erreurs à éviter | « Jamais de SELECT * en production » |
| `config` | Config qui marche | « Config debug Python VS Code » |
| `reference` | Docs/liens utiles | « Cette réponse StackOverflow là » |
| `snippet` | Code à garder | « Fonction debounce générique » |
| `til` | Apprentissages rapides | « Git rebase -i peut réordonner les commits » |

---

## 100 % local. 100 % à toi.

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

---

## Serveur MCP : Compatible avec tous les assistants IA

Rekall expose ta base de connaissances via le **Model Context Protocol (MCP)** — le standard ouvert pour connecter les assistants IA à des outils externes.

### Une commande, accès universel

```bash
rekall mcp  # Démarre le serveur MCP
```

### Compatible avec les principaux outils IA

| Outil | Statut | Configuration |
|-------|--------|---------------|
| **Claude Code** | ✅ Natif | Auto-détecté |
| **Claude Desktop** | ✅ Natif | Ajouter à `claude_desktop_config.json` |
| **Cursor** | ✅ Supporté | Paramètres MCP |
| **Windsurf** | ✅ Supporté | Paramètres MCP |
| **Continue.dev** | ✅ Supporté | Configuration MCP |
| **Tout client MCP** | ✅ Compatible | Protocole MCP standard |

### Exemple de configuration (Claude Desktop)

Ajoute à ton `claude_desktop_config.json` :

```json
{
  "mcpServers": {
    "rekall": {
      "command": "rekall",
      "args": ["mcp"]
    }
  }
}
```

### Ce que ton IA peut faire

Une fois connecté, ton assistant IA peut :

- **Chercher** dans ta base de connaissances avant de répondre
- **Citer** tes solutions passées dans ses réponses
- **Suggérer** de capturer de nouvelles connaissances après avoir résolu des problèmes
- **Lier** automatiquement les entrées connexes
- **Faire remonter** les patterns dans ton historique de debug

Tes connaissances s'accumulent automatiquement — plus tu l'utilises, plus il devient intelligent.

---

## Intégration avec Speckit

[Speckit](https://github.com/YOUR_USERNAME/speckit) est un toolkit de développement piloté par les spécifications. Combiné avec Rekall, il crée un workflow puissant où tes spécifications alimentent ta base de connaissances.

### Pourquoi intégrer ?

- **Les specs deviennent des connaissances recherchables** : Les décisions prises pendant la rédaction des specs sont capturées
- **Des patterns émergent** : Les choix architecturaux communs remontent à travers les projets
- **Le contexte est préservé** : Le « pourquoi » derrière les specs n'est jamais perdu

### Installation

1. Installe les deux outils :
```bash
uv tool install git+https://github.com/guthubrx/rekall.git
uv tool install git+https://github.com/YOUR_USERNAME/speckit.git
```

2. Configure Speckit pour utiliser Rekall (dans ton `.speckit/config.yaml`) :
```yaml
integrations:
  rekall:
    enabled: true
    auto_capture: true  # Capture automatique des décisions
    types:
      - decision
      - pattern
      - pitfall
```

3. Pendant le travail de spec, Speckit va :
   - Interroger Rekall pour les décisions passées pertinentes
   - Suggérer de capturer les nouveaux choix architecturaux
   - Lier les specs aux entrées de connaissances connexes

### Exemple de workflow

```bash
# Commence à spécifier une feature
speckit specify "Système d'authentification utilisateur"

# Speckit interroge Rekall : « As-tu déjà pris des décisions d'auth ? »
# → Montre ta décision passée OAuth vs JWT d'un autre projet

# Après avoir finalisé la spec
speckit plan

# Rekall capture : decision "JWT pour auth stateless en microservices"
```

<br>

<details>
<summary><h2>Sous le capot : Comment fonctionne la recherche</h2></summary>

> **TL;DR :** Recherche hybride combinant FTS5 (50%) + embeddings sémantiques (30%) + mots-clés (20%). Modèle local optionnel, pas de clé API.

Rekall ne fait pas juste du matching de mots-clés. Il comprend ce que tu veux dire.

### Le problème avec la recherche simple

Tu as capturé un bug « Erreur CORS sur Safari ». Plus tard, tu cherches « navigateur qui bloque mes appels API ». Une recherche par mots-clés ne trouve rien — les mots ne correspondent pas.

### Recherche hybride : exhaustive ET rapide

Rekall combine trois stratégies de recherche :

```
┌──────────────────────────────────────────────────────────────┐
│                     TA REQUÊTE                               │
│              "navigateur bloque appels API"                  │
└──────────────────────────────────┬───────────────────────────┘
                                   │
           ┌───────────────────────┼───────────────────────┐
           ▼                       ▼                       ▼
    ┌─────────────┐        ┌─────────────┐        ┌─────────────┐
    │   FTS5      │        │ Sémantique  │        │ Mots-clés   │
    │  (50%)      │        │   (30%)     │        │   (20%)     │
    │             │        │             │        │             │
    │ Matching    │        │ Sens via    │        │ Déclencheurs│
    │ exact       │        │ embeddings  │        │ structurés  │
    └──────┬──────┘        └──────┬──────┘        └──────┬──────┘
           │                      │                      │
           └───────────────────────┼───────────────────────┘
                                   ▼
                        ┌─────────────────┐
                        │  SCORE FINAL    │
                        │  85% match      │
                        └─────────────────┘
```

- **Recherche full-text (50%)** : SQLite FTS5 trouve les correspondances exactes et partielles
- **Recherche sémantique (30%)** : Les embeddings trouvent le contenu conceptuellement similaire — « navigateur » correspond à « Safari », « bloque » correspond à « erreur CORS »
- **Index de mots-clés (20%)** : Tes mots-clés de contexte structuré fournissent des déclencheurs explicites

### Embeddings locaux : Optionnels mais puissants

La recherche sémantique est **optionnelle**. Rekall fonctionne parfaitement avec la recherche full-text FTS5 seule — aucun modèle requis.

Mais si tu veux la compréhension sémantique, Rekall utilise **EmbeddingGemma** (308M paramètres), un modèle d'embedding état de l'art qui tourne entièrement sur ta machine :

- **100% local** : Aucune donnée ne quitte ton ordinateur, pas de clé API, pas de cloud
- **Multilingue** : Fonctionne dans plus de 100 langues
- **Rapide** : ~500ms par embedding sur un CPU standard
- **Léger** : ~200MB de RAM avec quantification int8

```bash
# Mode FTS uniquement (par défaut, pas de modèle nécessaire)
rekall search "erreur CORS"

# Activer la recherche sémantique (télécharge le modèle à la première utilisation)
rekall config set embeddings.enabled true
```

### Double embedding : Le contexte compte

Quand tu captures une connaissance, Rekall stocke deux embeddings :

1. **Embedding de résumé** : Titre + contenu + tags — pour les recherches ciblées
2. **Embedding de contexte** : La situation/solution complète — pour les recherches exploratoires

Ça résout un problème fondamental de la récupération : les résumés perdent le contexte. Si tu cherches « stack trace Safari », le résumé « Fix CORS » ne matchera pas — mais le contexte complet que tu as capturé (qui mentionne la stack trace) oui.

### Contexte structuré : Désambiguïsation qui fonctionne

Tu as fixé 5 bugs « timeout » différents. Comment retrouver le bon plus tard ? Les mots-clés seuls n'aident pas — ils sont tous taggés « timeout ».

Rekall capture un **contexte structuré** pour chaque entrée :

```
┌─────────────────────────────────────────────────────────────┐
│  situation        │  "Appels API timeout après déploiement" │
│  solution         │  "Augmenté la taille du pool de connexions" │
│  what_failed      │  "La logique de retry n'a pas aidé"     │
│  trigger_keywords │  ["timeout", "déploiement", "pool connexions"]│
│  error_messages   │  "ETIMEDOUT après 30s"                  │
│  files_modified   │  ["config/database.yml"]                │
└─────────────────────────────────────────────────────────────┘
```

Quand tu cherches, Rekall utilise ce contexte pour désambiguïser :

- **« timeout après déploiement »** → Trouve le bug du pool de connexions (match situation)
- **« ETIMEDOUT »** → Trouve les entrées avec ce message d'erreur exact
- **« retry n'a pas marché »** → Trouve les entrées où le retry a été essayé et a échoué

Le flag `--context-interactive` te guide pour capturer ça :

```bash
rekall add bug "Timeout en prod" --context-interactive
# Rekall demande : Que se passait-il ? Qu'est-ce qui a fixé ? Qu'est-ce qui n'a pas marché ?
# Tes réponses deviennent du contexte de désambiguïsation recherchable
```

### Stockage compressé

Le contexte peut être verbeux. Rekall compresse le contexte structuré avec zlib et maintient un index de mots-clés séparé pour la recherche rapide :

```
┌─────────────────────────────────────────────────────────────┐
│                    STOCKAGE ENTRÉE                          │
├─────────────────────────────────────────────────────────────┤
│  context_blob     │  JSON compressé (zlib)    │  ~70% plus petit│
│  context_keywords │  Table indexée            │  Lookup O(1)    │
│  emb_summary      │  Vecteur 768-dim          │  Sémantique     │
│  emb_context      │  Vecteur 768-dim          │  Sémantique     │
└─────────────────────────────────────────────────────────────┘
```

Le résultat : recherche **exhaustive** (rien n'est manqué) avec **rapidité** (réponses sub-seconde sur des milliers d'entrées).

</details>

<br>

<details>
<summary><h2>Basé sur la science</h2></summary>

> **TL;DR :** Graphes de connaissances (+20% de précision), répétition espacée (+6-9% de rétention), récupération contextuelle (-67% d'échecs), le tout basé sur la recherche évaluée par les pairs.

Rekall n'est pas une collection d'intuitions — il est construit sur la recherche en sciences cognitives et en récupération d'information évaluée par les pairs. Voici ce qu'on a appris et comment on l'a appliqué :

### Graphes de connaissances : +20% de précision de récupération

**Recherche** : Les études sur les graphes de connaissances dans les systèmes RAG montrent que l'information connectée est plus facile à récupérer que les faits isolés.

**Application** : Rekall te permet de lier les entrées avec des relations typées (`related`, `supersedes`, `derived_from`, `contradicts`). Quand tu cherches, les entrées liées boostent leurs scores mutuellement. Quand tu fixes un nouveau bug de timeout, Rekall fait remonter les trois autres problèmes de timeout que tu as résolus — et le pattern que tu en as extrait.

### Mémoire épisodique vs sémantique : Comment ton cerveau s'organise

**Recherche** : Tulving (1972) a établi que la mémoire humaine a deux systèmes distincts — épisodique (événements spécifiques : « J'ai fixé ce bug mardi ») et sémantique (connaissance générale : « Toujours ajouter du retry pour les APIs externes »).

**Application** : Rekall distingue les entrées `episodic` (ce qui s'est passé) des entrées `semantic` (ce que tu as appris). La commande `generalize` t'aide à extraire des patterns des épisodes. Ça reflète comment l'expertise se développe : tu accumules des expériences, puis tu les distilles en principes.

### Répétition espacée : +6-9% de rétention

**Recherche** : L'effet d'espacement (Ebbinghaus, 1885) et l'algorithme SM-2 montrent que réviser l'information à intervalles croissants améliore dramatiquement la rétention.

**Application** : Rekall suit quand tu accèdes à chaque entrée et calcule un score de consolidation. La commande `review` fait remonter les connaissances qui sont sur le point de s'effacer. La commande `stale` trouve les entrées que tu n'as pas touchées depuis des mois — avant qu'elles ne soient oubliées.

### Récupération contextuelle : -67% d'échecs de recherche

**Recherche** : Le papier Contextual Retrieval d'Anthropic a montré que les systèmes RAG traditionnels échouent parce qu'ils enlèvent le contexte à l'encodage. Ajouter 50-100 tokens de contexte réduit les échecs de récupération de 67%.

**Application** : Le contexte structuré de Rekall (situation, solution, mots-clés) préserve le « pourquoi » avec le « quoi ». La stratégie de double embedding assure que les requêtes ciblées et les recherches exploratoires trouvent les entrées pertinentes.

### Divulgation progressive : -98% d'utilisation de tokens

**Recherche** : Le blog engineering d'Anthropic a documenté que retourner des résumés compacts au lieu du contenu complet réduit l'utilisation de tokens de 98% tout en maintenant le succès des tâches.

**Application** : Le serveur MCP de Rekall retourne des résultats compacts (id, titre, score, extrait) avec un hint pour récupérer les détails complets. Ton assistant IA obtient ce dont il a besoin sans exploser sa fenêtre de contexte.

### Score de consolidation : Modéliser l'oubli

**Recherche** : La courbe de l'oubli montre que les souvenirs se dégradent exponentiellement sans renforcement. La fréquence et la récence d'accès comptent toutes les deux.

**Application** : Rekall calcule un score de consolidation pour chaque entrée :

```python
score = 0.6 × facteur_fréquence + 0.4 × facteur_fraîcheur
```

Les entrées que tu accèdes souvent et récemment ont une haute consolidation (connaissance stable). Les entrées que tu n'as pas touchées depuis des mois ont une basse consolidation (à risque d'être oubliées).

**On a lu les papiers pour que tu n'aies pas à le faire. Puis on a construit un outil qui les applique.**

</details>

<br>

## En savoir plus

| Ressource | Description |
|-----------|-------------|
| [Premiers pas](docs/getting-started.md) | Installation et premiers pas |
| [Référence CLI](docs/usage.md) | Documentation complète des commandes |
| [Intégration MCP](docs/mcp-integration.md) | Connexion aux assistants IA |
| [Architecture](docs/architecture.md) | Diagrammes techniques et internals |
| [Contribuer](CONTRIBUTING.md) | Comment contribuer |
| [Changelog](CHANGELOG.md) | Historique des versions |

---

## Prérequis

- Python 3.9+
- C'est tout. Pas de services cloud. Pas de clés API. Pas de compte.

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
