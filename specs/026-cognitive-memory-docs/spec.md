# Feature Specification: Documentation Cognitive Memory

**Feature Branch**: `026-cognitive-memory-docs`
**Created**: 2025-12-13
**Status**: Draft
**Project**: Rekall Home (16.devKMS)
**Priority**: P1
**Timeline**: 1 semaine

## Executive Summary

Documentation complète des features Cognitive Memory déjà implémentées : Structured Context, Spaced Repetition SM-2, Episodic/Semantic Memory. Objectif : Rendre ces différenciateurs UNIQUES compréhensibles et utilisables par nouveaux users.

---

## Objectif

**Features déjà implémentées mais sous-documentées** :
- ✅ Structured Context (situation/solution/whatFailed)
- ✅ SM-2 Spaced Repetition
- ✅ Consolidation Score
- ✅ Episodic vs Semantic

**Problème** : Users ne comprennent pas POURQUOI ces features = killer differentiators.

**Solution** : Documentation explicative avec exemples concrets, science cognitive, ROI.

---

## Documentation à Créer

### 1. Guide Structured Context

**Fichier** : `docs/cognitive-memory/structured-context.md`

**Contenu** :
- Qu'est-ce que structured context ?
- Pourquoi situation/solution/whatFailed ?
- Exemples avant/après
- Best practices capture
- Impact sur chatbot (60% précision)

### 2. Guide Spaced Repetition

**Fichier** : `docs/cognitive-memory/spaced-repetition.md`

**Contenu** :
- Science : Courbe d'oubli Ebbinghaus
- Algorithme SM-2 expliqué
- Comment utiliser `rekall review`
- Consolidation score formule
- Exemples scheduling

### 3. Guide Episodic vs Semantic

**Fichier** : `docs/cognitive-memory/episodic-semantic.md`

**Contenu** :
- Distinction episodic (bug) vs semantic (pattern)
- Quand généraliser ?
- Command `rekall generalize`
- Exemples transformation

### 4. Tutorial Complet

**Fichier** : `docs/tutorials/cognitive-workflow.md`

**Contenu** :
- Workflow day 1 : Capturer premier bug
- Workflow week 1 : Review + généraliser pattern
- Workflow month 1 : Capitaliser sur knowledge base

---

## Success Criteria

- **SC-001** : Nouveau user comprend structured context en < 5 min (tutorial)
- **SC-002** : NPS documentation ≥ 50
- **SC-003** : Time-to-first-value < 10 min (setup → first review)

---

## Timeline

**Semaine 1** :
- Day 1-2 : Guide Structured Context
- Day 3-4 : Guide Spaced Repetition
- Day 5 : Tutorial complet + review
