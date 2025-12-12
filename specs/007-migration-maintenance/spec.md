# Feature 007 - Migration & Maintenance

**Date** : 2025-12-10
**Statut** : Spécification

---

## Résumé

Système complet de gestion du cycle de vie de Rekall : migrations de schéma, compression des données, enrichissement des entrées legacy, et outils de maintenance.

---

## Features

### F1 : CLI Version & Migrate

**Commandes :**
- `rekall version` : Affiche version app + schéma DB + upgrades disponibles
- `rekall migrate` : Applique les migrations en attente avec backup auto
- `rekall migrate --dry-run` : Prévisualise sans modifier
- `rekall migrate --enrich-context` : Enrichit les anciennes entrées
- `rekall changelog` : Affiche les changements par version

**TUI - Overlay de migration au démarrage :**
- Si migration disponible → Overlay centré (sans background) au lancement
- Affiche : version actuelle → nouvelle version + nb entrées à enrichir
- Navigation `<` `>` cyclique entre :
  - Vue "Migration disponible" (avec boutons Migrer / Plus tard)
  - Vue "Changelog" (liste des changements par version)
- Escape pour fermer et continuer sans migrer

---

### F2 : Compression context_structured

**Problème :** Le champ `context_structured` stocke du JSON brut (~600 bytes) vs `context_compressed` qui est compressé (~200 bytes).

**Solution :** Appliquer zlib compression au JSON avant stockage, comme pour `context_compressed`.

---

### F3 : Unification des champs contexte

**Problème :** Deux champs redondants :
- `context_compressed` : Ancien système (texte compressé)
- `context_structured` : Nouveau système (JSON non compressé)

**Solution :** Un seul champ `context` stockant le JSON structuré compressé. Migration des anciennes données.

---

### F4 : Auto-capture conversation_excerpt

**Problème :** Le champ `conversation_excerpt` existe mais n'est jamais rempli automatiquement.

**Solution :** Quand l'agent appelle `rekall_add`, il peut fournir un extrait des derniers échanges. Le MCP guide l'agent pour le faire systématiquement.

---

### F5 : Enrichissement anciennes entrées

**Problème :** 37 entrées legacy sans `context_structured`.

**Solution :** Commande `rekall migrate --enrich-context` qui :
1. Parcourt les entrées sans contexte structuré
2. Extrait keywords du title/content
3. Génère situation/solution depuis le content existant
4. Marque `extraction_method = "migrated"`

---

### F6 : Limite taille configurable

**Problème :** Pas de contrôle sur la taille des contextes stockés.

**Solution :**
- Config `max_context_size` (défaut: 10KB)
- Truncate ou warn si dépassé
- **Paramétrable dans le TUI** : Écran Settings avec slider/input pour ajuster la limite
- Aussi modifiable via `rekall config set max_context_size 20KB`

---

### F8 : Contexte obligatoire par défaut

**Problème :** Le défaut est `context_mode = "optional"` → les entrées sans contexte structuré sont acceptées silencieusement.

**Solution :**
- Changer le défaut à `"required"`
- Refus des entrées sans contexte structuré (CLI + MCP)
- **Paramétrable dans le TUI** : Écran Settings avec choix required/recommended/optional
- Proposé dans l'overlay de migration au premier lancement post-upgrade

---

### F7 : Changelog visible

**Problème :** L'utilisateur ne sait pas ce qui a changé entre versions.

**Solution :** Fichier CHANGELOG.md + commande `rekall changelog` affichant les changements par version de schéma.

---

## Critères d'acceptation

- [ ] `rekall version` affiche version app et schéma
- [ ] `rekall migrate` applique migrations avec backup
- [ ] Overlay TUI migration au démarrage si upgrade dispo
- [ ] `context_structured` compressé (ratio ~3x)
- [ ] Un seul champ contexte après migration
- [ ] Anciennes entrées enrichies automatiquement
- [ ] Limite taille configurable (TUI + CLI)
- [ ] `context_mode` défaut = "required"
- [ ] `context_mode` configurable dans TUI Settings
- [ ] Changelog accessible (CLI + TUI overlay)

---

## Dépendances

- Feature 006 (Contexte Enrichi) : Terminée

---

## Estimation

- Complexité : Moyenne
- Impact : Maintenance long terme

---

*Créé le 2025-12-10*
