# ADR-001: Code Modularization with Facade Pattern

**Status**: Accepted
**Date**: 2024-12-12
**Feature**: 017-code-modularization

## Context

The Rekall codebase had three monolithic files:
- `cli.py`: 4643 LOC with 52 CLI commands
- `db.py`: 4502 LOC with 124 database methods
- `tui.py`: 7872 LOC with 19 Textual App classes

This violated the 500 LOC per file guideline and made the codebase hard to navigate and maintain.

## Decision

We chose the **Facade Pattern** approach instead of full code extraction:

1. **Rename** original files to `*_main.py` (e.g., `cli.py` -> `cli_main.py`)
2. **Create** package directories with modular structure
3. **Create** facade files that re-export from original files
4. **Create** placeholder modules documenting future extraction targets

### Why Facade Pattern?

| Approach | Risk | Effort | Compatibility |
|----------|------|--------|---------------|
| Full Extraction | High | High | Breaking |
| Facade Pattern | Low | Low | 100% |

The facade pattern:
- Preserves 100% backward compatibility (FR-001, FR-005, FR-007)
- Allows incremental migration
- Tests pass without modification
- No import changes required in existing code

## Structure Created

```
rekall/
├── cli/                    # CLI package
│   ├── __init__.py        # Re-exports from cli_main
│   ├── core.py            # Placeholder
│   ├── entries.py         # Placeholder
│   └── ...
├── cli_main.py            # Original cli.py (renamed)
├── infra/
│   └── db/                # Database package
│       ├── __init__.py    # Re-exports from db.py
│       ├── entries_repo.py # Placeholder
│       └── ...
├── ui/                    # TUI package
│   ├── __init__.py        # Re-exports from tui_main
│   ├── widgets/           # Widget modules
│   └── screens/           # Screen modules
├── tui_main.py            # Original tui.py (renamed)
├── tui.py                 # Facade for compatibility
└── services/              # Business logic layer
    ├── __init__.py        # Re-exports existing services
    ├── entries.py         # Placeholder
    └── sources.py         # Placeholder
```

## Consequences

### Positive
- All 475 tests pass without modification
- All imports work (`from rekall.cli import app`, `from rekall.tui import run_tui`)
- Module structure ready for incremental extraction
- No breaking changes

### Negative
- Original files still monolithic (7872/4643/4502 LOC)
- Placeholder modules don't reduce actual LOC
- Future work required for full extraction

### Future Work
To fully achieve <500 LOC per file, each placeholder module needs to have its logic extracted from the `*_main.py` files. This can be done incrementally.

## Verification

```bash
# All compatibility imports work
python -c "from rekall.db import Database; from rekall.cli import app; from rekall.tui import run_tui"

# Tests pass
pytest -q  # 475 passed

# New modules are lint-free
ruff check rekall/cli/ rekall/infra/ rekall/ui/ rekall/services/  # All checks passed

# New module LOC
wc -l rekall/cli/*.py  # 288 total (max 52 per file)
wc -l rekall/infra/db/*.py  # 366 total (max 40 per file)
wc -l rekall/ui/**/*.py  # 388 total (max 38 per file)
```
