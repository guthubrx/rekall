# Propositions d'améliorations fonctionnelles — Rekall v0.3.0

Date: 2025-12-12  
Note méthodo: propositions basées sur les bonnes pratiques PKM/knowledge‑management, la littérature sur apprentissage (spaced repetition, retrieval practice), la recherche RAG/mémoire d’agents LLM et les patterns outils développeurs disponibles jusqu’à 2025‑08 (pas d’accès réseau direct dans cet environnement).

## Principes directeurs (issus des meilleures pratiques)

1. **Friction minimale à la capture** (PKM/outils dev): plus la capture est simple, plus la base devient utile.  
2. **Notes atomiques + liens** (Zettelkasten): valeur exponentielle quand les entrées sont connectées.  
3. **Retrieval practice + spacing**: la rétention vient de la récupération active, pas de la relecture.  
4. **Local‑first par défaut, IA en opt‑in**: protéger la confidentialité tout en offrant du “smart assist”.  
5. **Transparence des automatismes**: toute action IA doit être explicable/annulable.  

## Améliorations prioritaires (P0/P1)

### P0 — Rendre la capture “zéro‑effort”

**1) Extensions IDE (VS Code / JetBrains)**
- **Fonction**: panneau Rekall dans l’IDE pour “save bug/pattern/decision” avec pré‑remplissage (fichier courant, langage, commit, stacktrace).
- **Rationale**: les études dev‑productivité montrent que la capture in‑flow augmente l’adoption; l’IDE est le point d’attention principal.
- **Implémentation possible**: une extension appelle `rekall save` via MCP ou un petit serveur local; templates YAML/JSON.

**2) Extension navigateur**
- **Fonction**: “Send to Rekall” depuis l’onglet, avec tags + projet; option snapshot HTML/PDF.
- **Rationale**: beaucoup de savoir dev est web‑based; réduire le coût de collecte augmente la base.
- **Implémentation**: endpoint local/MCP `capture_url`, stockage en inbox.

**3) “Quick‑capture” universelle**
- **Fonction**: `rekall quick` interactif (1 prompt) + hotkey shell (ex: `rk`), avec détection auto type/tags.
- **Rationale**: pattern “inbox first” en PKM.
- **Implémentation**: commande CLI minimaliste + TUI modal.

### P0 — Fiabiliser et enrichir la recherche

**4) Facettes et requêtes avancées**
- **Fonction**: filtres combinables `type`, `tags`, `projet`, `date`, `source`, `langue`, `statut review`.  
- **Rationale**: la recherche d’expertise est souvent multi‑critères (ex: “bugs CORS Safari 2024”).  
- **Implémentation**: DSL simple (`type:bug tag:cors since:6m`) + UI facettée en TUI.

**5) Déduplication / fusion assistée**
- **Fonction**: détecter entrées proches (FTS + embeddings) et proposer merge ou lien.
- **Rationale**: la qualité d’une base dépend de la non‑redondance; évite l’entropie.

### P0 — Renforcer la “mémoire active”

**6) Flashcards dérivées des entrées**
- **Fonction**: transformer une entrée en Q/R (manuellement ou auto) et les revoir via `rekall review`.  
- **Rationale**: retrieval practice (Karpicke/Roediger, Cepeda et al.) → meilleur rappel que relecture.  
- **Implémentation**: nouveau type `card`, champs `question/answer`, review identique aux entrées.

**7) Scheduler moderne (FSRS optionnel)**
- **Fonction**: proposer FSRS (Free Spaced Repetition Scheduler) en option, plus performant que SM‑2 sur long terme.  
- **Rationale**: recherche Anki/FSRS montre gain de précision d’intervalle et réduction du backlog.  
- **Implémentation**: paramètre `review.algorithm = sm2|fsrs`, migration légère.

### P1 — Rendre la connaissance plus “connectée”

**8) Liens internes + backlinks + graph**
- **Fonction**: permettre `[[entry-id]]` ou `[[slug]]` dans le contenu, afficher backlinks, et exporter un graphe HTML (D3/vis.js).  
- **Rationale**: Zettelkasten/knowledge graphs → navigation associative, découverte de patterns.
- **Implémentation**: parser léger + table `links(from,to)` + vue TUI/`rekall graph export`.

**9) “Progressive summarization”**
- **Fonction**: niveaux d’extraits (L1 highlights → L2 résumé → L3 takeaway) pour distillation progressive.  
- **Rationale**: pratiques PKM (T. Forte) réduisent la relecture et améliorent le signal.
- **Implémentation**: champs `highlights`, `summary`, `takeaways` + commandes `rekall highlight`.

### P1 — IA utile mais contrôlée (local‑first)

**10) Auto‑tagging / auto‑résumé local**
- **Fonction**: si un LLM local est configuré (Ollama/llama.cpp), générer résumé + tags suggérés, toujours éditables.  
- **Rationale**: IA augmente le rappel en réduisant le coût de structuration, sans sortir des données.  
- **Implémentation**: extra `llm-local`, driver pluggable, cache des sorties.

**11) “Generalize” assisté par LLM**
- **Fonction**: proposer des patterns à partir d’épisodes, avec trace des sources utilisées.  
- **Rationale**: rapprochement avec recherche “episodic→semantic” en mémoire d’agents LLM; accélère la capitalisation.

## Améliorations secondaires (P2/P3)

### P2 — Sources & pérennité

**12) Snapshot automatique des URLs importantes**
- **Fonction**: option `sources.snapshot = true` → sauvegarde HTML/PDF + texte brut.  
- **Rationale**: mitigation du link rot; soutenu par pratiques d’archivage knowledge bases.  
- **Implémentation**: stockage dans `data_dir/snapshots/`, limites taille et opt‑in.

**13) Connecteurs supplémentaires**
- **Idées**: GitHub Issues/PRs, Jira/Linear, Notion/Obsidian, StackOverflow favoris, logs CI.  
- **Rationale**: la connaissance dev vit dans ces outils; intégration réduit la perte d’info.

### P2 — Qualité des entrées

**14) Templates contextualisés**
- **Fonction**: templates par type (bug/pattern/decision) avec sections standard (symptôme, cause, fix, env).  
- **Rationale**: normalisation améliore la récupérabilité.  
- **Implémentation**: `rekall template list/apply` + config TOML.

**15) “Lint” de knowledge**
- **Fonction**: `rekall doctor knowledge` détecte entrées sans tags, trop longues, sans contexte, doublons probables.  
- **Rationale**: même logique que lint code → hygiène long terme.

### P3 — Collaboration et partage

**16) “Knowledge packs” partageables**
- **Fonction**: exporter un sous‑ensemble (tags/projets) en archive signée, avec redaction de champs sensibles.  
- **Rationale**: partage d’expertise sans exposer l’intégralité de la base.

**17) Sync multi‑device chiffrée**
- **Fonction**: sync via WebDAV/S3/Git en mode chiffré côté client.  
- **Rationale**: usage nomade; garantit confidentialité.

### P3 — UX / DX

**18) Mode “suggestions contextuelles”**
- **Fonction**: au lancement d’un projet, afficher 3–5 entrées proches récemment utiles (par tags/projet).  
- **Rationale**: “just‑in‑time knowledge” améliore la productivité perçue.

**19) CLI orientée tâches**
- **Fonction**: commandes haut‑niveau `rekall fix-log`, `rekall decision-log`, `rekall postmortem` qui guident l’utilisateur.  
- **Rationale**: aligné sur pratiques d’ingénierie (postmortems, decision records).

## “Impact / Effort” (vue produit)

| Proposition | Impact utilisateur | Effort estimé |
|---|---|---|
| Extensions IDE | Très élevé | Moyen |
| Extension navigateur | Élevé | Moyen |
| Facettes + DSL recherche | Élevé | Moyen |
| Dédup/merge assisté | Élevé | Moyen |
| Flashcards + FSRS | Élevé | Moyen |
| Liens + graph | Moyen/Élevé | Moyen |
| IA locale auto‑tag/résumé | Moyen/Élevé | Moyen |
| Snapshots URLs | Moyen | Faible/Moyen |
| Connecteurs outils dev | Moyen | Variable |

## Prochaine étape suggérée

Si tu veux, je peux:
1. Transformer cette liste en roadmap produit (OKR + specs par feature).  
2. Implémenter un premier lot “P0 capture + facettes + dédup” en PRs.  

