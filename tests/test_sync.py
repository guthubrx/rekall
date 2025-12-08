"""Tests for rekall sync module."""

from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path

import pytest

from rekall.models import Entry


class TestConflictDetection:
    """Tests for conflict detection."""

    def test_detect_conflict_identical(self):
        """Test identical entries produce no conflict."""
        from rekall.sync import detect_conflict

        local = Entry(id="X", title="T", type="bug", content="C")
        imported = Entry(id="X", title="T", type="bug", content="C")

        conflict = detect_conflict(local, imported)
        assert conflict is None

    def test_detect_conflict_title_changed(self):
        """Test title change is detected."""
        from rekall.sync import detect_conflict

        local = Entry(id="X", title="Old", type="bug")
        imported = Entry(id="X", title="New", type="bug")

        conflict = detect_conflict(local, imported)
        assert conflict is not None
        assert "title" in conflict.fields_changed

    def test_detect_conflict_multiple_fields(self):
        """Test multiple field changes are detected."""
        from rekall.sync import detect_conflict

        local = Entry(id="X", title="T1", type="bug", content="C1", confidence=2)
        imported = Entry(id="X", title="T2", type="bug", content="C2", confidence=4)

        conflict = detect_conflict(local, imported)
        assert conflict is not None
        assert len(conflict.fields_changed) == 3  # title, content, confidence

    def test_detect_conflict_tags_order_independent(self):
        """Test tags comparison is order-independent."""
        from rekall.sync import detect_conflict

        local = Entry(id="X", title="T", type="bug", tags=["a", "b"])
        imported = Entry(id="X", title="T", type="bug", tags=["b", "a"])

        conflict = detect_conflict(local, imported)
        assert conflict is None

    def test_detect_conflict_ignores_timestamps(self):
        """Test timestamps are ignored in comparison."""
        from rekall.sync import detect_conflict

        local = Entry(
            id="X",
            title="T",
            type="bug",
            created_at=datetime(2025, 1, 1),
            updated_at=datetime(2025, 1, 1),
        )
        imported = Entry(
            id="X",
            title="T",
            type="bug",
            created_at=datetime(2025, 12, 1),
            updated_at=datetime(2025, 12, 1),
        )

        conflict = detect_conflict(local, imported)
        assert conflict is None


class TestImportPlan:
    """Tests for ImportPlan builder."""

    def test_build_plan_all_new(self, memory_db):
        """Test plan with all new entries."""
        from rekall.sync import build_import_plan

        imported = [Entry(id="A", title="T", type="bug")]
        plan = build_import_plan(memory_db, imported)

        assert len(plan.new_entries) == 1
        assert len(plan.conflicts) == 0
        assert len(plan.identical) == 0

    def test_build_plan_all_identical(self, memory_db):
        """Test plan with all identical entries."""
        from rekall.sync import build_import_plan

        existing = Entry(id="A", title="T", type="bug")
        memory_db.add(existing)

        imported = [Entry(id="A", title="T", type="bug")]
        plan = build_import_plan(memory_db, imported)

        assert len(plan.new_entries) == 0
        assert len(plan.conflicts) == 0
        assert len(plan.identical) == 1

    def test_build_plan_conflict(self, memory_db):
        """Test plan with conflicting entries."""
        from rekall.sync import build_import_plan

        existing = Entry(id="A", title="Old", type="bug")
        memory_db.add(existing)

        imported = [Entry(id="A", title="New", type="bug")]
        plan = build_import_plan(memory_db, imported)

        assert len(plan.new_entries) == 0
        assert len(plan.conflicts) == 1
        assert plan.conflicts[0].entry_id == "A"

    def test_build_plan_mixed(self, memory_db):
        """Test plan with mixed entries."""
        from rekall.sync import build_import_plan

        memory_db.add(Entry(id="A", title="Same", type="bug"))
        memory_db.add(Entry(id="B", title="Old", type="bug"))

        imported = [
            Entry(id="A", title="Same", type="bug"),  # identical
            Entry(id="B", title="New", type="bug"),  # conflict
            Entry(id="C", title="Brand", type="bug"),  # new
        ]
        plan = build_import_plan(memory_db, imported)

        assert len(plan.identical) == 1
        assert len(plan.conflicts) == 1
        assert len(plan.new_entries) == 1


class TestImportExecutorPreview:
    """Tests for ImportExecutor preview."""

    def test_preview_format(self):
        """Test preview output format."""
        from rekall.sync import Conflict, ImportExecutor, ImportPlan

        plan = ImportPlan(
            new_entries=[Entry(id="A", title="New", type="bug")],
            conflicts=[
                Conflict(
                    entry_id="B",
                    local=Entry(id="B", title="Old", type="bug"),
                    imported=Entry(id="B", title="New", type="bug"),
                    fields_changed=["title"],
                )
            ],
            identical=["C"],
        )

        preview = ImportExecutor.preview(plan)

        assert "[NEW]" in preview
        assert "A" in preview
        assert "[CONFLICT]" in preview
        assert "B" in preview
        assert "[SKIP]" in preview

    def test_preview_empty_plan(self):
        """Test preview with empty plan."""
        from rekall.sync import ImportExecutor, ImportPlan

        plan = ImportPlan(new_entries=[], conflicts=[], identical=[])
        preview = ImportExecutor.preview(plan)
        assert "nothing" in preview.lower() or "rien" in preview.lower()


class TestImportExecutorSkip:
    """Tests for skip strategy."""

    def test_execute_skip_adds_new(self, memory_db):
        """Test skip strategy adds new entries."""
        from rekall.sync import ImportExecutor, ImportPlan

        plan = ImportPlan(
            new_entries=[Entry(id="A", title="New", type="bug")],
            conflicts=[],
            identical=[],
        )
        executor = ImportExecutor(memory_db)
        result = executor.execute(plan, strategy="skip")

        assert result.success
        assert result.added == 1
        assert memory_db.get("A") is not None

    def test_execute_skip_ignores_conflicts(self, memory_db):
        """Test skip strategy ignores conflicts."""
        from rekall.sync import Conflict, ImportExecutor, ImportPlan

        existing = Entry(id="B", title="Local", type="bug")
        memory_db.add(existing)

        plan = ImportPlan(
            new_entries=[],
            conflicts=[
                Conflict(
                    entry_id="B",
                    local=existing,
                    imported=Entry(id="B", title="Imported", type="bug"),
                    fields_changed=["title"],
                )
            ],
            identical=[],
        )
        executor = ImportExecutor(memory_db)
        result = executor.execute(plan, strategy="skip")

        assert result.success
        assert result.skipped == 1
        assert memory_db.get("B").title == "Local"  # Unchanged


class TestImportExecutorReplace:
    """Tests for replace strategy."""

    def test_execute_replace_overwrites(self, memory_db):
        """Test replace strategy overwrites conflicts."""
        from rekall.sync import Conflict, ImportExecutor, ImportPlan

        existing = Entry(id="B", title="Local", type="bug")
        memory_db.add(existing)

        plan = ImportPlan(
            new_entries=[],
            conflicts=[
                Conflict(
                    entry_id="B",
                    local=existing,
                    imported=Entry(id="B", title="Imported", type="bug"),
                    fields_changed=["title"],
                )
            ],
            identical=[],
        )
        executor = ImportExecutor(memory_db)
        result = executor.execute(plan, strategy="replace")

        assert result.success
        assert result.replaced == 1
        assert memory_db.get("B").title == "Imported"

    def test_execute_replace_creates_backup(self, memory_db, tmp_path):
        """Test replace strategy creates backup."""
        from rekall.sync import Conflict, ImportExecutor, ImportPlan

        existing = Entry(id="X", title="T", type="bug")
        memory_db.add(existing)

        plan = ImportPlan(
            new_entries=[],
            conflicts=[
                Conflict(
                    entry_id="X",
                    local=existing,
                    imported=Entry(id="X", title="New", type="bug"),
                    fields_changed=["title"],
                )
            ],
            identical=[],
        )
        executor = ImportExecutor(memory_db, backup_dir=tmp_path / "backups")
        result = executor.execute(plan, strategy="replace")

        assert result.success
        assert result.backup_path is not None
        assert result.backup_path.exists()


class TestImportExecutorMerge:
    """Tests for merge strategy."""

    def test_execute_merge_creates_new_ids(self, memory_db):
        """Test merge strategy creates new entries with new IDs."""
        from rekall.sync import Conflict, ImportExecutor, ImportPlan

        existing = Entry(id="B", title="Local", type="bug")
        memory_db.add(existing)

        imported_entry = Entry(id="B", title="Different", type="bug")
        plan = ImportPlan(
            new_entries=[],
            conflicts=[
                Conflict(
                    entry_id="B",
                    local=existing,
                    imported=imported_entry,
                    fields_changed=["title"],
                )
            ],
            identical=[],
        )
        executor = ImportExecutor(memory_db)
        result = executor.execute(plan, strategy="merge")

        assert result.success
        assert result.merged == 1

        # Original preserved
        assert memory_db.get("B").title == "Local"

        # New entry created with new ID
        all_entries = memory_db.list_all()
        assert len(all_entries) == 2
        new_entry = [e for e in all_entries if e.id != "B"][0]
        assert new_entry.title == "Different"


class TestAtomicRollback:
    """Tests for atomic rollback on error."""

    def test_rollback_on_error(self, memory_db, monkeypatch):
        """Test rollback on import error."""
        from rekall.sync import ImportExecutor, ImportPlan

        original_count = len(memory_db.list_all())

        plan = ImportPlan(
            new_entries=[
                Entry(id="A", title="First", type="bug"),
                Entry(id="B", title="Second", type="bug"),
            ],
            conflicts=[],
            identical=[],
        )

        executor = ImportExecutor(memory_db)

        # Make the second insert fail by patching the executor's method
        call_count = [0]
        original_add = executor._add_entry_no_commit

        def failing_add(entry):
            call_count[0] += 1
            if call_count[0] == 2:
                raise sqlite3.IntegrityError("Simulated failure")
            original_add(entry)

        monkeypatch.setattr(executor, "_add_entry_no_commit", failing_add)

        result = executor.execute(plan, strategy="skip")

        assert not result.success
        # Rollback should have occurred - count same as before
        assert len(memory_db.list_all()) == original_count
