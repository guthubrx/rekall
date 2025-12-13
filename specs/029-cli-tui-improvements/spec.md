# Feature Specification: CLI/TUI Improvements

**Feature Branch**: `029-cli-tui-improvements`
**Created**: 2025-12-13
**Project**: Rekall Home (16.devKMS)
**Priority**: P2
**Timeline**: 2-3 semaines

## Executive Summary

Améliorations UX CLI/TUI : interface review plus intuitive, graph visualization ASCII, auto-completion, shortcuts.

## Améliorations

### 1. TUI Review Interface
```
┌─ Review Session (5 entries due) ────────────────────┐
│                                                     │
│  Entry: "Fix CORS Safari credentials"               │
│  Last review: 14 days ago                           │
│                                                     │
│  [Preview content]                                  │
│                                                     │
│  Rate difficulty:                                   │
│  [1] Again  [2] Hard  [3] Good  [4] Easy            │
│                                                     │
│  Progress: ████░░░░░░ 2/5                           │
└─────────────────────────────────────────────────────┘
```

### 2. Graph Visualization ASCII
```bash
rekall graph 01HX7
#     ┌─────────┐
#     │ CORS    │
#     │ Safari  │
#     └────┬────┘
#          │
#     ┌────┴─────┬──────────┐
#     │          │          │
#  ┌──▼──┐   ┌──▼──┐   ┌───▼──┐
#  │Auth │   │Fetch│   │Cookie│
#  │Bug  │   │API  │   │ Fix  │
#  └─────┘   └─────┘   └──────┘
```

### 3. Auto-completion
```bash
rekall add <TAB>
# → bug, pattern, decision, pitfall, config, reference

rekall search --type=<TAB>
# → bug, pattern, decision
```

### 4. Shortcuts
```bash
rekall s "query"  # shortcut for search
rekall a         # shortcut for add (interactive)
rekall r         # shortcut for review
```

## Requirements

- **FR-01** : TUI review interface avec preview + rating
- **FR-02** : ASCII graph visualization (depth=2)
- **FR-03** : Shell auto-completion (bash, zsh, fish)
- **FR-04** : Command shortcuts (s, a, r)

## Success Criteria

- **SC-001** : Review session time -30% (plus rapide)
- **SC-002** : Graph viz compréhensible (user test)
- **SC-003** : Auto-completion works dans bash/zsh

## Timeline

- Week 1: TUI review interface
- Week 2: Graph viz ASCII
- Week 3: Auto-completion + shortcuts
