# Plan : Feature 007 - Migration & Maintenance

**Date** : 2025-12-10
**Statut** : Planifié

---

## Phases

### Phase 1 : CLI & Détection (F1, F7)
- `rekall version` : affiche app version + schema version + upgrades dispo
- `rekall migrate` : applique migrations avec backup auto
- `rekall changelog` : affiche CHANGELOG.md
- Détection auto au démarrage si migration nécessaire

### Phase 2 : Overlay TUI Migration (F1)
- Overlay centré au lancement si migration dispo
- Navigation `<` `>` entre Migration / Changelog
- Boutons Migrer / Plus tard
- Checkbox "Activer contexte obligatoire"

### Phase 3 : Compression & Unification (F2, F3)
- Compression zlib pour `context_structured`
- Migration `context_compressed` → nouveau format
- Suppression ancien champ après migration
- Tests de non-régression

### Phase 4 : Enrichissement Legacy (F5)
- Commande `rekall migrate --enrich-context`
- Extraction keywords depuis title/content existants
- Génération situation/solution basique
- Marquage `extraction_method = "migrated"`

### Phase 5 : TUI Settings (F6, F8)
- Écran Settings accessible depuis TUI
- Option `context_mode` : required/recommended/optional
- Option `max_context_size` : slider ou input
- Sauvegarde dans config.toml

### Phase 6 : Défaut Required (F8)
- Changer défaut `context_mode` de "optional" à "required"
- Vérifier CLI refuse sans contexte
- Vérifier MCP refuse sans contexte
- Message d'erreur clair

---

## Dépendances entre phases

```
Phase 1 ──┬──▶ Phase 2
          │
          └──▶ Phase 3 ──▶ Phase 4

Phase 5 (indépendant)

Phase 6 (indépendant, peut être fait en premier)
```

---

## Risques

| Risque | Mitigation |
|--------|------------|
| Perte données migration | Backup obligatoire avant |
| Anciennes entrées mal enrichies | Marquage "migrated" + review manuel possible |
| Users bloqués par required | Option dans TUI pour revenir à optional |

---

*Créé le 2025-12-10*
