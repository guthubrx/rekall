# Feature Specification: Database Maintenance

**Feature Branch**: `005-db-maintenance`
**Created**: 2025-12-09
**Status**: Draft
**Input**: User description: "Database maintenance: info command, backup/restore, and TUI menu integration"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - View Database Information (Priority: P1)

As a developer, I want to see my Rekall database information (path, schema version, statistics) so I can understand the state of my knowledge base and troubleshoot issues.

**Why this priority**: Essential for debugging and support. Users need visibility into their database state before performing any maintenance operations.

**Independent Test**: Run `rekall info` command and verify it displays database path, schema version, entry count, link count, and file size.

**Acceptance Scenarios**:

1. **Given** a Rekall database exists, **When** user runs `rekall info`, **Then** system displays database path, schema version, entry count, link count, and file size
2. **Given** no database exists, **When** user runs `rekall info`, **Then** system displays clear message indicating no database found
3. **Given** database exists with schema version 2, **When** user runs `rekall info`, **Then** system shows "v2 (current)" indicating schema is up to date

---

### User Story 2 - Create Database Backup (Priority: P1)

As a developer, I want to create a backup of my Rekall database before performing updates or migrations so I can restore my data if something goes wrong.

**Why this priority**: Critical for data safety. Backups must be available before any destructive operation.

**Independent Test**: Run `rekall backup` command and verify a timestamped backup file is created in the backups directory.

**Acceptance Scenarios**:

1. **Given** a database exists, **When** user runs `rekall backup`, **Then** system creates a backup file with timestamp in filename (e.g., `knowledge_2025-12-09_143022.db`)
2. **Given** a database exists, **When** user runs `rekall backup --output custom.db`, **Then** system creates backup at specified location
3. **Given** backup completes, **When** user checks backup file, **Then** backup file size matches original database size
4. **Given** backups directory doesn't exist, **When** user runs `rekall backup`, **Then** system creates backups directory automatically

---

### User Story 3 - Restore Database from Backup (Priority: P1)

As a developer, I want to restore my Rekall database from a backup so I can recover from data loss or failed migrations.

**Why this priority**: Critical complement to backup. Without restore capability, backups have no value.

**Independent Test**: Create a backup, modify database, run `rekall restore <backup>`, and verify database returns to backup state.

**Acceptance Scenarios**:

1. **Given** a valid backup file, **When** user runs `rekall restore backup.db`, **Then** system replaces current database with backup
2. **Given** a backup file, **When** user runs `rekall restore backup.db`, **Then** system creates automatic backup of current state before restoring (safety net)
3. **Given** an invalid backup file, **When** user runs `rekall restore invalid.db`, **Then** system shows error and does not modify current database
4. **Given** restore completes, **When** user runs `rekall info`, **Then** database statistics match the backup state

---

### User Story 4 - TUI Installation & Maintenance Menu (Priority: P2)

As a developer using the TUI, I want to access database maintenance features from the graphical interface so I can manage my database without remembering CLI commands.

**Why this priority**: Improves discoverability and user experience for TUI users, but CLI functionality is sufficient for MVP.

**Independent Test**: Open TUI, navigate to "Installation & Maintenance" menu, and verify all maintenance options are accessible and functional.

**Acceptance Scenarios**:

1. **Given** user is in TUI, **When** user opens Installation menu, **Then** menu is named "Installation & Maintenance"
2. **Given** user is in maintenance menu, **When** user selects "Database Info", **Then** system displays same info as `rekall info` command
3. **Given** user is in maintenance menu, **When** user selects "Create Backup", **Then** system creates backup and shows success message
4. **Given** user is in maintenance menu, **When** user selects "Restore from Backup", **Then** system shows file picker to select backup file

---

### Edge Cases

- What happens when database file is locked by another process?
- How does system handle corrupted backup files during restore?
- What happens when disk is full during backup?
- How does system handle very large databases (> 1GB)?
- What happens when user tries to restore while TUI is running?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST display database path when `rekall info` is executed
- **FR-002**: System MUST display current schema version with indication if up-to-date
- **FR-003**: System MUST display entry count (total, active, obsolete) in info command
- **FR-004**: System MUST display link count in info command
- **FR-005**: System MUST display database file size in human-readable format
- **FR-006**: System MUST create timestamped backup files in `~/.rekall/backups/` directory
- **FR-007**: System MUST support custom backup path via `--output` option
- **FR-008**: System MUST create automatic backup before restore operation (safety net)
- **FR-009**: System MUST validate backup file integrity before restore
- **FR-010**: System MUST show clear error messages for invalid operations
- **FR-011**: TUI MUST rename "Installation" menu to "Installation & Maintenance"
- **FR-012**: TUI MUST include "Database Info" section showing all database statistics
- **FR-013**: TUI MUST include "Backup" button to create backups
- **FR-014**: TUI MUST include "Restore" option with file selection

### Key Entities

- **Backup File**: A complete copy of the SQLite database file with timestamp metadata
- **Database Info**: Composite view of path, schema version, statistics (entries, links, size)

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can view database information in under 1 second via CLI or TUI
- **SC-002**: Backup operation completes in under 5 seconds for databases up to 100MB
- **SC-003**: Restore operation completes in under 10 seconds for databases up to 100MB
- **SC-004**: 100% of backup files can be successfully restored
- **SC-005**: Users can complete backup/restore workflow without consulting documentation
- **SC-006**: Zero data loss when restore fails (automatic pre-restore backup ensures recovery)

## Assumptions

- Backup directory defaults to `~/.rekall/backups/` following XDG conventions
- Backup filenames use format `knowledge_YYYY-MM-DD_HHMMSS.db` for chronological sorting
- Schema version display uses format "vN (current)" or "vN (outdated - run init to upgrade)"
- File sizes use human-readable format (KB, MB, GB)
- TUI backup creates backup in default location (no file picker for simplicity)
- TUI restore shows list of available backups from default directory
