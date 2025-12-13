# Tasks: AI Source Enrichment

**Input**: Design documents from `/specs/021-ai-source-enrichment/`
**Prerequisites**: plan.md, spec.md, data-model.md, contracts/

**Tests**: Not explicitly requested - implementation only.

**Organization**: Tasks grouped by user story for independent implementation.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story (US1-US5)
- Exact file paths included

## Path Conventions

Project type: **Single Python package**
- Source: `rekall/`
- Tests: `tests/`

---

## Phase 1: Setup (Schema Migration)

**Purpose**: Prepare database schema for AI enrichment fields

- [ ] T001 Add migration v12 statements in `rekall/db.py` MIGRATIONS dict
- [ ] T002 Increment CURRENT_VERSION to 12 in `rekall/db.py`
- [ ] T003 [P] Add index for enrichment_status in migration v12 in `rekall/db.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Extend Source model and DB methods used by ALL user stories

**CRITICAL**: US2-US5 cannot start until this phase completes

- [ ] T004 Add enrichment fields to `_row_to_source()` method in `rekall/db.py`
- [ ] T005 [P] Add `EnrichmentStatus`, `SourceType`, `ValidatedBy` type aliases in `rekall/models.py`
- [ ] T006 [P] Update `Source` dataclass with ai_* fields in `rekall/models.py`
- [ ] T007 Test migration by running `uv run rekall info` (manual verification)

**Checkpoint**: Schema ready - user story implementation can begin

---

## Phase 3: User Story 1 - Voir URLs individuelles (Priority: P1)

**Goal**: Expose individual URLs stored for each entry via MCP tool

**Independent Test**: Create entry with 3 URLs, call tool, verify all 3 returned with domains

### Implementation for User Story 1

- [ ] T008 [US1] Add `_extract_domain()` helper function in `rekall/mcp_server.py`
- [ ] T009 [US1] Add `rekall_get_entry_urls` tool definition in `list_tools()` in `rekall/mcp_server.py`
- [ ] T010 [US1] Add `elif name == "rekall_get_entry_urls"` dispatch in `call_tool()` in `rekall/mcp_server.py`
- [ ] T011 [US1] Implement `_handle_get_entry_urls()` async handler in `rekall/mcp_server.py`
- [ ] T012 [US1] Update REKALL_HELP string with new tool in `rekall/mcp_server.py`

**Checkpoint**: US1 functional - test with `rekall_get_entry_urls(entry_id="...")`

---

## Phase 4: User Story 2 - Enrichir une source (Priority: P1)

**Goal**: Allow agent to persist enrichment (tags, summary, type, confidence) for a source

**Independent Test**: Create source without tags, call enrich tool, verify ai_* fields populated

### Implementation for User Story 2

- [ ] T013 [US2] Add `update_source_enrichment()` method in `rekall/db.py`
- [ ] T014 [US2] Add `rekall_enrich_source` tool definition in `list_tools()` in `rekall/mcp_server.py`
- [ ] T015 [US2] Add dispatch case for `rekall_enrich_source` in `call_tool()` in `rekall/mcp_server.py`
- [ ] T016 [US2] Implement `_handle_enrich_source()` async handler in `rekall/mcp_server.py`
- [ ] T017 [US2] Handle auto-validation when confidence >= 0.90 in `_handle_enrich_source()` in `rekall/mcp_server.py`

**Checkpoint**: US2 functional - test with `rekall_enrich_source(source_id, tags, summary, type, confidence)`

---

## Phase 5: User Story 3 - Enrichissement batch (Priority: P2)

**Goal**: List sources without enrichment for batch processing

**Independent Test**: Create 5 sources without tags, call list tool, verify 5 returned

### Implementation for User Story 3

- [ ] T018 [US3] Add `get_unenriched_sources()` method in `rekall/db.py`
- [ ] T019 [US3] Add `rekall_list_unenriched` tool definition in `list_tools()` in `rekall/mcp_server.py`
- [ ] T020 [US3] Add dispatch case for `rekall_list_unenriched` in `call_tool()` in `rekall/mcp_server.py`
- [ ] T021 [US3] Implement `_handle_list_unenriched()` async handler in `rekall/mcp_server.py`
- [ ] T022 [US3] Add domain_filter and include_pending options in `_handle_list_unenriched()` in `rekall/mcp_server.py`

**Checkpoint**: US3 functional - test with `rekall_list_unenriched(limit=10)`

---

## Phase 6: User Story 4 - Valider/rejeter enrichissement (Priority: P2)

**Goal**: Human-in-the-loop validation of AI-proposed enrichments

**Independent Test**: Enrich a source (proposed status), call validate, verify status changes

### Implementation for User Story 4

- [ ] T023 [US4] Add `validate_enrichment()` method in `rekall/db.py`
- [ ] T024 [US4] Handle 'modify' action with partial updates in `validate_enrichment()` in `rekall/db.py`
- [ ] T025 [US4] Add `rekall_validate_enrichment` tool definition in `list_tools()` in `rekall/mcp_server.py`
- [ ] T026 [US4] Add dispatch case for `rekall_validate_enrichment` in `call_tool()` in `rekall/mcp_server.py`
- [ ] T027 [US4] Implement `_handle_validate_enrichment()` async handler in `rekall/mcp_server.py`

**Checkpoint**: US4 functional - test validate/reject/modify actions

---

## Phase 7: User Story 5 - Suggestions Research Hub (Priority: P3)

**Goal**: Suggest quality sources from research/*.md files based on entry theme

**Independent Test**: Create entry about "RAG", call suggest, verify relevant sources returned

### Implementation for User Story 5

- [ ] T028 [US5] Add `_parse_research_sources()` helper to read `rekall/research/*.md` in `rekall/mcp_server.py`
- [ ] T029 [US5] Update existing `_handle_sources_suggest()` to include Research Hub sources in `rekall/mcp_server.py`
- [ ] T030 [US5] Add theme matching logic (keyword extraction) in `_handle_sources_suggest()` in `rekall/mcp_server.py`

**Checkpoint**: US5 functional - test with entry containing known research themes

---

## Phase 8: Polish & Documentation

**Purpose**: Final cleanup and documentation

- [ ] T031 [P] Update REKALL_HELP with all 4 new tools in `rekall/mcp_server.py`
- [ ] T032 [P] Add Source Management section to help text in `rekall/mcp_server.py`
- [ ] T033 Run `uv run pytest` to verify no regressions
- [ ] T034 Manual validation: test complete enrichment workflow

---

## Dependencies & Execution Order

### Phase Dependencies

```
Phase 1: Setup (T001-T003)
    │
    ▼
Phase 2: Foundational (T004-T007) ← BLOCKS all User Stories
    │
    ├──────────────────────────────────────┐
    ▼                                      ▼
Phase 3: US1 (T008-T012)           Phase 4: US2 (T013-T017)
    │                                      │
    │              ┌───────────────────────┤
    │              ▼                       ▼
    │      Phase 5: US3 (T018-T022) Phase 6: US4 (T023-T027)
    │              │                       │
    │              └───────────┬───────────┘
    │                          ▼
    │                  Phase 7: US5 (T028-T030)
    │                          │
    └──────────────────────────┤
                               ▼
                       Phase 8: Polish (T031-T034)
```

### User Story Dependencies

| Story | Depends On | Can Parallelize With |
|-------|------------|---------------------|
| US1 | Phase 2 | US2, US3, US4 |
| US2 | Phase 2 | US1, US3, US4 |
| US3 | Phase 2 | US1, US2, US4 |
| US4 | Phase 2 (+ US2 for testing) | US1, US3 |
| US5 | Phase 2 | US1, US2, US3, US4 |

### Within Each User Story

- DB methods before MCP tool definitions
- Tool definitions before dispatch
- Dispatch before handlers
- Core logic before edge cases

---

## Parallel Opportunities

### Phase 2 (Foundational)

```
T005 [P] models.py type aliases  ─┬─ can run together
T006 [P] models.py Source update ─┘
```

### Across User Stories (after Phase 2)

```
US1 (T008-T012) ─┬─ all can start immediately after Phase 2
US2 (T013-T017) ─┤
US3 (T018-T022) ─┤
US4 (T023-T027) ─┤
US5 (T028-T030) ─┘
```

### Phase 8 (Polish)

```
T031 [P] Help text update     ─┬─ can run together
T032 [P] Source Management docs─┘
```

---

## Implementation Strategy

### MVP First (User Story 1 + 2)

1. Complete Phase 1: Setup (migration)
2. Complete Phase 2: Foundational (schema + model)
3. Complete Phase 3: US1 (URLs) → **Quick Win!**
4. Complete Phase 4: US2 (Enrichment) → **Core Feature!**
5. **STOP and VALIDATE**: Test enrichment workflow end-to-end
6. Deploy if ready

### Incremental Delivery

| Increment | Stories | Value |
|-----------|---------|-------|
| MVP | US1 + US2 | See URLs + enrich sources |
| v1.1 | + US3 | Batch discovery |
| v1.2 | + US4 | Human validation |
| v1.3 | + US5 | Research Hub suggestions |

---

## Summary

| Metric | Count |
|--------|-------|
| Total tasks | 34 |
| Setup tasks | 3 |
| Foundational tasks | 4 |
| US1 tasks | 5 |
| US2 tasks | 5 |
| US3 tasks | 5 |
| US4 tasks | 5 |
| US5 tasks | 3 |
| Polish tasks | 4 |
| Parallel opportunities | 8 tasks marked [P] |

**Estimated effort**: ~12h total (per plan.md)

**MVP scope**: Phase 1-4 (US1 + US2) = ~6h
