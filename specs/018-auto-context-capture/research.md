# Recherche Technique - Feature 018: Auto-Capture Contexte Enrichi

**Date**: 2025-12-12
**Branche**: `018-auto-context-capture`

## Résumé des Décisions Techniques

### 1. Architecture Mode Hybride Capture

**Décision**: Implémenter un mode hybride avec 2 chemins d'exécution via MCP.

**Rationale**:
- Mode 1 (Agent Direct) : Plus rapide (1 appel), portable tous CLIs
- Mode 2 (Système Assisté) : Nécessaire quand contexte compacté, utilise transcript complet
- L'agent décide du mode basé sur sa connaissance de son propre contexte

**Alternatives considérées**:
- Mode unique extraction automatique → Rejeté : pas portable, agent n'a pas de contrôle
- Mode unique manuel → Rejeté : friction trop élevée, perte du bénéfice d'automation
- Extraction LLM-assisted → Rejeté : latence + coût, overkill pour filtrage simple

### 2. Parsers Transcript Multi-Format

**Décision**: Implémenter 4 parsers v1, extensibles v2.

| Format | Parser | Structure Attendue |
|--------|--------|-------------------|
| `claude-jsonl` | `ClaudeTranscriptParser` | `{type: "human"|"assistant", content: [...], timestamp}` |
| `cline-json` | `ClineTranscriptParser` | `{role: "user"|"assistant", content: string}` |
| `continue-json` | `ContinueTranscriptParser` | `{messages: [{role, content}]}` |
| `raw-json` | `GenericJsonParser` | `[{role, content}]` array |

**Rationale**:
- Couvre 80%+ des CLIs MCP actuels (Claude Code, Cline, Roo Code, Continue.dev)
- Interface commune `TranscriptParser` pour extensibilité
- Auto-détection par extension comme fallback

**Alternatives considérées**:
- Parser unique générique → Rejeté : trop de variations entre formats
- Conversion externe → Rejeté : friction utilisateur, maintenance externe

### 3. Git Auto-Détection

**Décision**: Utiliser subprocess avec timeout 5s, combiner staged + unstaged.

**Commandes**:
```bash
git diff --cached --name-only  # Staged
git diff --name-only           # Unstaged
```

**Rationale**:
- Timeout 5s évite blocage sur gros repos
- Déduplication automatique (set)
- Filtrage binaires par extension (configurable)

**Alternatives considérées**:
- GitPython library → Rejeté : dépendance lourde, subprocess suffit
- libgit2 binding → Rejeté : complexité, pas de bénéfice pour use case simple

### 4. Temporal Markers

**Décision**: Auto-génération basée sur datetime locale, override manuel possible.

**Mapping time_of_day**:
```python
HOUR_TO_TIME_OF_DAY = {
    (5, 12): "morning",
    (12, 17): "afternoon",
    (17, 21): "evening",
    (21, 5): "night"  # wrap-around
}
```

**Rationale**:
- Simple, déterministe, pas de dépendance externe
- Override manuel préserve contrôle utilisateur
- Utile pour recherche contextuelle ("bug du vendredi soir")

### 5. Hook Stop Rappel Proactif

**Décision**: Script bash avec pattern matching regex sur stdout de l'agent.

**Patterns de résolution détectés**:
```bash
RESOLUTION_PATTERNS=(
    "bug.*résolu"
    "fixed"
    "corrigé"
    "problème.*réglé"
    "fonctionne.*maintenant"
    "✅"
)
```

**Anti-spam**: Skip si "rekall" déjà mentionné dans la réponse.

**Rationale**:
- Léger, pas de dépendance
- Configurable via fichier patterns
- Cooldown configurable (évite spam)

---

## Sources Techniques Consultées

### Architecture Patterns
- Source: `~/.speckit/research/04-architectures-patterns.md`
- Applicable: Strategy Pattern pour parsers transcript

### Testing Quality
- Source: `~/.speckit/research/08-testing-quality.md`
- Applicable: Pyramide tests (unit parsers, integration MCP, e2e hook)

### DevOps Infrastructure
- Source: `~/.speckit/research/09-devops-infrastructure.md`
- Applicable: Hook installation idempotent, rollback possible

---

## Points Non Résolus (Deferred)

1. **SQLite parser (Cursor)**: Complexité requête SQL, reporté v2
2. **LMDB parser (Zed)**: Format binaire propriétaire, reporté v2
3. **Windsurf**: Format non documenté, fallback Mode 1 uniquement

---

## Validation Constitution

| Article | Statut | Justification |
|---------|--------|---------------|
| III. Processus SpecKit | ✅ | Cycle complet respecté |
| VII. ADR | ✅ | Ce document + plan.md |
| VIII. Débogage Forensic | N/A | Pas de débogage |
| XV. Test-Before-Next | ✅ | Tests unitaires prévus pour chaque parser |
