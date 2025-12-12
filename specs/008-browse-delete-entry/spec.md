# Feature Specification: Delete Entry from Browse Screen

**Feature Branch**: `008-browse-delete-entry`
**Created**: 2025-12-10
**Status**: Ready for Planning
**Input**: User description: "Dans l'interface TUI, je veux que depuis l'écran dans lequel on navigue dans les souvenirs, on puisse effacer une entrée en tapant 'd'. Bien entendu, il doit y avoir un message de confirmation dans un Overlay qui soit centré verticalement et horizontalement sans background. Attention à la gestion des liens et autres impacts sur le graphe ou autre que je n'aurais pas anticipé."

## Context

Currently, the Browse screen has a 'd' key binding that triggers `action_delete_entry()`, which exits the app and uses an external `SimpleMenuApp` for confirmation. This breaks the user flow by leaving the Browse screen.

The request is to implement an **in-app confirmation overlay** that:
- Stays within the Browse screen
- Is centered both vertically and horizontally
- Has no visible background (transparent)
- Properly informs the user of cascading impacts (links, embeddings, etc.)

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Basic Entry Deletion (Priority: P1)

As a user browsing my knowledge entries, I want to delete an obsolete entry by pressing 'd' and confirming in a centered overlay, so that I can manage my knowledge base without leaving the browse screen.

**Why this priority**: Core functionality - without this, users cannot delete entries using the new overlay system.

**Independent Test**: Can be fully tested by selecting an entry without links, pressing 'd', confirming deletion, and verifying the entry is removed from the list.

**Acceptance Scenarios**:

1. **Given** an entry is selected in Browse screen, **When** user presses 'd', **Then** a centered confirmation overlay appears without background
2. **Given** the confirmation overlay is displayed, **When** user selects "Yes" or presses 'y', **Then** the entry is deleted and overlay closes
3. **Given** the confirmation overlay is displayed, **When** user selects "No" or presses 'n' or 'Escape', **Then** the overlay closes without deleting
4. **Given** the entry was deleted, **When** the overlay closes, **Then** the entry list refreshes and cursor moves to next entry

---

### User Story 2 - Deletion with Link Warning (Priority: P2)

As a user deleting an entry that has links to other entries, I want to see how many links will be removed before confirming, so that I understand the impact on my knowledge graph.

**Why this priority**: Important for data integrity awareness - users need to know they're breaking connections in their knowledge graph.

**Independent Test**: Can be tested by creating an entry with 2+ links, pressing 'd', and verifying the overlay shows link count before confirmation.

**Acceptance Scenarios**:

1. **Given** the selected entry has 3 incoming and 2 outgoing links, **When** user presses 'd', **Then** the overlay shows "5 links will be removed"
2. **Given** the selected entry has no links, **When** user presses 'd', **Then** no link warning is displayed
3. **Given** the user confirms deletion of a linked entry, **When** deletion completes, **Then** all related links are removed from the database

---

### User Story 3 - Deletion with Keyboard Shortcuts (Priority: P3)

As a power user, I want to use keyboard shortcuts (y/n) to confirm or cancel deletion quickly, so that I can manage entries efficiently without using arrow keys.

**Why this priority**: Enhances efficiency for frequent users but not blocking for basic functionality.

**Independent Test**: Can be tested by pressing 'd' then 'y' to confirm, or 'd' then 'n' to cancel, without using arrow keys.

**Acceptance Scenarios**:

1. **Given** the confirmation overlay is displayed, **When** user presses 'y', **Then** the entry is deleted
2. **Given** the confirmation overlay is displayed, **When** user presses 'n', **Then** the overlay closes without deletion
3. **Given** the confirmation overlay is displayed, **When** user presses 'Escape', **Then** the overlay closes without deletion

---

### Edge Cases

- What happens when the last entry is deleted? → User sees "No entries" message, browse screen remains open
- What happens if deletion fails (database error)? → Error toast is displayed, entry remains in list
- What happens when user presses 'd' with no entry selected? → Nothing happens (no overlay shown)
- What happens to FTS index when entry is deleted? → FTS trigger handles automatic cleanup (existing behavior)
- What happens to embeddings when entry is deleted? → CASCADE foreign key removes embeddings automatically
- What happens to context keywords when entry is deleted? → CASCADE foreign key removes keywords automatically

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST display a confirmation overlay when user presses 'd' on a selected entry
- **FR-002**: The overlay MUST be centered both vertically and horizontally on the screen
- **FR-003**: The overlay MUST have a transparent or minimal background (no full-screen dimming)
- **FR-004**: The overlay MUST show the entry title (truncated if longer than 30 characters) in the confirmation message
- **FR-005**: If the entry has links, the overlay MUST display the total number of links that will be removed
- **FR-006**: Users MUST be able to confirm deletion by pressing 'y' or selecting "Yes"
- **FR-007**: Users MUST be able to cancel deletion by pressing 'n', 'Escape', or selecting "No"
- **FR-008**: After successful deletion, the entry list MUST refresh automatically
- **FR-009**: After deletion, cursor MUST move to the next entry (or previous if last entry was deleted)
- **FR-010**: System MUST display a success toast message after deletion
- **FR-011**: System MUST display an error toast if deletion fails
- **FR-012**: The overlay MUST be dismissable without side effects when cancelled

### Key Entities

- **Entry**: The knowledge entry to be deleted (id, title, type, content, etc.)
- **Links**: Relationships between entries (source_id, target_id, relation_type) - automatically cascaded on delete
- **Embeddings**: Vector representations of entries - automatically cascaded on delete
- **Context Keywords**: Searchable keywords extracted from context - automatically cascaded on delete

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can delete an entry in under 3 seconds (press 'd', confirm, done)
- **SC-002**: 100% of cascading deletions (links, embeddings, keywords) happen automatically without errors
- **SC-003**: Users always see the impact (link count) before confirming deletion of linked entries
- **SC-004**: Overlay appears centered within 100ms of pressing 'd'
- **SC-005**: No data loss occurs when user cancels deletion

## Assumptions

- The existing database CASCADE constraints are working correctly (verified in db.py schema)
- The FTS trigger for deletion is functioning properly (TRIGGER_DELETE in db.py)
- The 'd' binding already exists in BrowseApp BINDINGS (confirmed at tui.py:813)
- The overlay will be implemented using Textual's existing modal/overlay patterns
- The confirmation will replace the current `SimpleMenuApp` approach entirely
