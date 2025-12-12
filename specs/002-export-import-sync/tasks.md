# Tâches d'Implémentation - Export/Import Sync

## Phase 1: Archive Foundation

### T001: Dataclasses Archive
**Dépendances**: Aucune
**Fichiers**: `rekall/archive.py`
**Tests**: `tests/test_archive.py`

**TDD RED**:
```python
def test_manifest_to_dict():
    stats = ArchiveStats(entries_count=10, projects=["p1"], types={"bug": 5})
    manifest = Manifest(
        format_version="1.0",
        created_at=datetime(2025, 12, 7, 14, 30),
        rekall_version="0.1.0",
        checksum="sha256:abc123",
        stats=stats,
    )
    d = manifest.to_dict()
    assert d["format_version"] == "1.0"
    assert d["stats"]["entries_count"] == 10

def test_manifest_from_dict():
    data = {
        "format_version": "1.0",
        "created_at": "2025-12-07T14:30:00",
        "rekall_version": "0.1.0",
        "checksum": "sha256:abc",
        "stats": {"entries_count": 5, "projects": [], "types": {}}
    }
    manifest = Manifest.from_dict(data)
    assert manifest.format_version == "1.0"

def test_validation_result_bool():
    valid = ValidationResult(valid=True, errors=[], warnings=[])
    invalid = ValidationResult(valid=False, errors=["err"], warnings=[])
    assert valid
    assert not invalid
```

**GREEN**: Implémenter `ArchiveStats`, `Manifest`, `ValidationResult` dataclasses.

**Critères**:
- [ ] `Manifest.to_dict()` sérialise correctement
- [ ] `Manifest.from_dict()` désérialise correctement
- [ ] `ValidationResult.__bool__` fonctionne

---

### T002: Checksum Calculation
**Dépendances**: T001
**Fichiers**: `rekall/archive.py`
**Tests**: `tests/test_archive.py`

**TDD RED**:
```python
def test_calculate_checksum():
    data = b'{"entries": []}'
    checksum = calculate_checksum(data)
    assert checksum.startswith("sha256:")
    assert len(checksum) == 71  # "sha256:" + 64 hex chars

def test_checksum_deterministic():
    data = b'same content'
    assert calculate_checksum(data) == calculate_checksum(data)

def test_checksum_different_content():
    assert calculate_checksum(b'a') != calculate_checksum(b'b')
```

**GREEN**: Implémenter `calculate_checksum(data: bytes) -> str`.

**Critères**:
- [ ] Format `sha256:<64 hex chars>`
- [ ] Déterministe
- [ ] Différent pour contenu différent

---

### T003: Entry Serialization Round-trip
**Dépendances**: T001
**Fichiers**: `rekall/archive.py`
**Tests**: `tests/test_archive.py`

**TDD RED**:
```python
def test_entries_to_json():
    entries = [
        Entry(id="ABC123", title="Test", type="bug"),
    ]
    json_str = entries_to_json(entries)
    data = json.loads(json_str)
    assert len(data) == 1
    assert data[0]["id"] == "ABC123"

def test_entries_from_json():
    json_str = '[{"id": "X", "title": "T", "type": "bug", "content": "", "project": null, "tags": [], "confidence": 2, "status": "active", "superseded_by": null, "created_at": "2025-12-07T10:00:00", "updated_at": "2025-12-07T10:00:00"}]'
    entries = entries_from_json(json_str)
    assert len(entries) == 1
    assert entries[0].id == "X"

def test_round_trip_preserves_all_fields():
    original = Entry(
        id="TEST123",
        title="Test Entry",
        type="pattern",
        content="Some content",
        project="myproj",
        tags=["a", "b"],
        confidence=4,
        status="active",
        created_at=datetime(2025, 12, 7, 10, 0),
        updated_at=datetime(2025, 12, 7, 12, 0),
    )
    json_str = entries_to_json([original])
    restored = entries_from_json(json_str)[0]

    assert restored.id == original.id
    assert restored.title == original.title
    assert restored.tags == original.tags
    assert restored.created_at == original.created_at
```

**GREEN**: Implémenter `entries_to_json()` et `entries_from_json()`.

**Critères**:
- [ ] Tous les champs Entry préservés
- [ ] Dates ISO8601
- [ ] Tags en liste
- [ ] None/null correctement gérés

---

### T004: RekallArchive.create()
**Dépendances**: T001, T002, T003
**Fichiers**: `rekall/archive.py`
**Tests**: `tests/test_archive.py`

**TDD RED**:
```python
def test_create_archive_empty(tmp_path):
    archive_path = tmp_path / "test.rekall"
    archive = RekallArchive.create(archive_path, entries=[])

    assert archive_path.exists()
    assert zipfile.is_zipfile(archive_path)

def test_create_archive_contains_manifest(tmp_path):
    archive_path = tmp_path / "test.rekall"
    RekallArchive.create(archive_path, entries=[])

    with zipfile.ZipFile(archive_path) as zf:
        assert "manifest.json" in zf.namelist()

def test_create_archive_contains_entries(tmp_path):
    archive_path = tmp_path / "test.rekall"
    entries = [Entry(id="X", title="T", type="bug")]
    RekallArchive.create(archive_path, entries=entries)

    with zipfile.ZipFile(archive_path) as zf:
        assert "entries.json" in zf.namelist()
        data = json.loads(zf.read("entries.json"))
        assert len(data) == 1

def test_create_archive_manifest_stats(tmp_path):
    archive_path = tmp_path / "test.rekall"
    entries = [
        Entry(id="1", title="Bug1", type="bug", project="p1"),
        Entry(id="2", title="Pattern1", type="pattern", project="p1"),
        Entry(id="3", title="Bug2", type="bug", project="p2"),
    ]
    RekallArchive.create(archive_path, entries=entries)

    with zipfile.ZipFile(archive_path) as zf:
        manifest = json.loads(zf.read("manifest.json"))
        assert manifest["stats"]["entries_count"] == 3
        assert set(manifest["stats"]["projects"]) == {"p1", "p2"}
        assert manifest["stats"]["types"]["bug"] == 2
```

**GREEN**: Implémenter `RekallArchive.create()`.

**Critères**:
- [ ] Crée fichier ZIP valide
- [ ] Contient manifest.json
- [ ] Contient entries.json
- [ ] Stats correctes dans manifest

---

### T005: RekallArchive.open() et validate()
**Dépendances**: T004
**Fichiers**: `rekall/archive.py`
**Tests**: `tests/test_archive.py`

**TDD RED**:
```python
def test_open_valid_archive(tmp_path):
    archive_path = tmp_path / "test.rekall"
    RekallArchive.create(archive_path, entries=[])

    archive = RekallArchive.open(archive_path)
    assert archive is not None

def test_open_invalid_file(tmp_path):
    bad_file = tmp_path / "bad.rekall"
    bad_file.write_text("not a zip")

    result = RekallArchive.open(bad_file)
    # ou raise InvalidArchiveError
    assert result is None or isinstance(result, ValidationResult)

def test_validate_missing_manifest(tmp_path):
    archive_path = tmp_path / "bad.rekall"
    with zipfile.ZipFile(archive_path, 'w') as zf:
        zf.writestr("entries.json", "[]")

    archive = RekallArchive.open(archive_path)
    result = archive.validate()
    assert not result.valid
    assert "manifest" in str(result.errors).lower()

def test_validate_checksum_mismatch(tmp_path):
    archive_path = tmp_path / "test.rekall"
    # Créer archive valide puis corrompre
    RekallArchive.create(archive_path, entries=[Entry(id="X", title="T", type="bug")])

    # Modifier entries.json sans update checksum
    with zipfile.ZipFile(archive_path, 'a') as zf:
        zf.writestr("entries.json", '[{"id": "Y"}]')  # Différent

    archive = RekallArchive.open(archive_path)
    result = archive.validate()
    assert not result.valid
    assert "checksum" in str(result.errors).lower()

def test_validate_success(tmp_path):
    archive_path = tmp_path / "test.rekall"
    RekallArchive.create(archive_path, entries=[])

    archive = RekallArchive.open(archive_path)
    result = archive.validate()
    assert result.valid
```

**GREEN**: Implémenter `RekallArchive.open()` et `validate()`.

**Critères**:
- [ ] Détecte fichier non-ZIP
- [ ] Détecte manifest manquant
- [ ] Détecte checksum invalide
- [ ] Retourne ValidationResult

---

## Phase 2: Sync Logic

### T006: Conflict Detection
**Dépendances**: T005
**Fichiers**: `rekall/sync.py`
**Tests**: `tests/test_sync.py`

**TDD RED**:
```python
def test_detect_conflict_identical():
    local = Entry(id="X", title="T", type="bug", content="C")
    imported = Entry(id="X", title="T", type="bug", content="C")

    conflict = detect_conflict(local, imported)
    assert conflict is None  # Pas de conflit

def test_detect_conflict_title_changed():
    local = Entry(id="X", title="Old", type="bug")
    imported = Entry(id="X", title="New", type="bug")

    conflict = detect_conflict(local, imported)
    assert conflict is not None
    assert "title" in conflict.fields_changed

def test_detect_conflict_multiple_fields():
    local = Entry(id="X", title="T1", type="bug", content="C1", confidence=2)
    imported = Entry(id="X", title="T2", type="bug", content="C2", confidence=4)

    conflict = detect_conflict(local, imported)
    assert len(conflict.fields_changed) == 3  # title, content, confidence

def test_detect_conflict_tags_order_independent():
    local = Entry(id="X", title="T", type="bug", tags=["a", "b"])
    imported = Entry(id="X", title="T", type="bug", tags=["b", "a"])

    conflict = detect_conflict(local, imported)
    assert conflict is None  # Même tags, ordre différent = pas de conflit
```

**GREEN**: Implémenter `detect_conflict()`.

**Critères**:
- [ ] None si identiques
- [ ] Liste champs modifiés
- [ ] Tags order-independent
- [ ] Ignore created_at/updated_at

---

### T007: ImportPlan Builder
**Dépendances**: T006
**Fichiers**: `rekall/sync.py`
**Tests**: `tests/test_sync.py`

**TDD RED**:
```python
def test_build_plan_all_new(memory_db):
    # DB vide
    imported = [Entry(id="A", title="T", type="bug")]

    plan = build_import_plan(memory_db, imported)

    assert len(plan.new_entries) == 1
    assert len(plan.conflicts) == 0
    assert len(plan.identical) == 0

def test_build_plan_all_identical(memory_db):
    # Ajouter entry existante
    existing = Entry(id="A", title="T", type="bug")
    memory_db.add(existing)

    imported = [Entry(id="A", title="T", type="bug")]
    plan = build_import_plan(memory_db, imported)

    assert len(plan.new_entries) == 0
    assert len(plan.conflicts) == 0
    assert len(plan.identical) == 1

def test_build_plan_conflict(memory_db):
    existing = Entry(id="A", title="Old", type="bug")
    memory_db.add(existing)

    imported = [Entry(id="A", title="New", type="bug")]
    plan = build_import_plan(memory_db, imported)

    assert len(plan.new_entries) == 0
    assert len(plan.conflicts) == 1
    assert plan.conflicts[0].entry_id == "A"

def test_build_plan_mixed(memory_db):
    memory_db.add(Entry(id="A", title="Same", type="bug"))
    memory_db.add(Entry(id="B", title="Old", type="bug"))

    imported = [
        Entry(id="A", title="Same", type="bug"),  # identical
        Entry(id="B", title="New", type="bug"),   # conflict
        Entry(id="C", title="Brand", type="bug"), # new
    ]
    plan = build_import_plan(memory_db, imported)

    assert len(plan.identical) == 1
    assert len(plan.conflicts) == 1
    assert len(plan.new_entries) == 1
```

**GREEN**: Implémenter `build_import_plan()`.

**Critères**:
- [ ] Classifie new/identical/conflict
- [ ] Requiert accès DB pour lookup
- [ ] ImportPlan complet

---

### T008: ImportExecutor Preview
**Dépendances**: T007
**Fichiers**: `rekall/sync.py`
**Tests**: `tests/test_sync.py`

**TDD RED**:
```python
def test_preview_format():
    plan = ImportPlan(
        new_entries=[Entry(id="A", title="New", type="bug")],
        conflicts=[Conflict(
            entry_id="B",
            local=Entry(id="B", title="Old", type="bug"),
            imported=Entry(id="B", title="New", type="bug"),
            fields_changed=["title"],
        )],
        identical=["C"],
    )

    preview = ImportExecutor.preview(plan)

    assert "[NEW]" in preview or "nouveau" in preview.lower()
    assert "A" in preview
    assert "[CONFLICT]" in preview or "conflit" in preview.lower()
    assert "B" in preview
    assert "[SKIP]" in preview or "skip" in preview.lower()

def test_preview_empty_plan():
    plan = ImportPlan(new_entries=[], conflicts=[], identical=[])
    preview = ImportExecutor.preview(plan)
    assert "rien" in preview.lower() or "nothing" in preview.lower()
```

**GREEN**: Implémenter `ImportExecutor.preview()`.

**Critères**:
- [ ] Format lisible style rsync
- [ ] [NEW], [CONFLICT], [SKIP] tags
- [ ] Gère plan vide

---

### T009: Execute Skip Strategy
**Dépendances**: T008
**Fichiers**: `rekall/sync.py`
**Tests**: `tests/test_sync.py`

**TDD RED**:
```python
def test_execute_skip_adds_new(memory_db):
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

def test_execute_skip_ignores_conflicts(memory_db):
    existing = Entry(id="B", title="Local", type="bug")
    memory_db.add(existing)

    plan = ImportPlan(
        new_entries=[],
        conflicts=[Conflict(
            entry_id="B",
            local=existing,
            imported=Entry(id="B", title="Imported", type="bug"),
            fields_changed=["title"],
        )],
        identical=[],
    )
    executor = ImportExecutor(memory_db)
    result = executor.execute(plan, strategy="skip")

    assert result.success
    assert result.skipped == 1
    assert memory_db.get("B").title == "Local"  # Inchangé
```

**GREEN**: Implémenter `execute()` avec strategy="skip".

**Critères**:
- [ ] Ajoute new_entries
- [ ] Ignore conflicts
- [ ] ImportResult correct

---

### T010: Execute Replace Strategy
**Dépendances**: T009
**Fichiers**: `rekall/sync.py`
**Tests**: `tests/test_sync.py`

**TDD RED**:
```python
def test_execute_replace_overwrites(memory_db):
    existing = Entry(id="B", title="Local", type="bug")
    memory_db.add(existing)

    plan = ImportPlan(
        new_entries=[],
        conflicts=[Conflict(
            entry_id="B",
            local=existing,
            imported=Entry(id="B", title="Imported", type="bug"),
            fields_changed=["title"],
        )],
        identical=[],
    )
    executor = ImportExecutor(memory_db)
    result = executor.execute(plan, strategy="replace")

    assert result.success
    assert result.replaced == 1
    assert memory_db.get("B").title == "Imported"

def test_execute_replace_creates_backup(memory_db, tmp_path):
    memory_db.add(Entry(id="X", title="T", type="bug"))

    plan = ImportPlan(
        new_entries=[],
        conflicts=[Conflict(...)],
        identical=[],
    )
    executor = ImportExecutor(memory_db, backup_dir=tmp_path / "backups")
    result = executor.execute(plan, strategy="replace")

    assert result.backup_path is not None
    assert result.backup_path.exists()
```

**GREEN**: Implémenter `execute()` avec strategy="replace" + backup.

**Critères**:
- [ ] Écrase entrées en conflit
- [ ] Crée backup automatique
- [ ] backup_path dans result

---

### T011: Execute Merge Strategy
**Dépendances**: T009
**Fichiers**: `rekall/sync.py`
**Tests**: `tests/test_sync.py`

**TDD RED**:
```python
def test_execute_merge_creates_new_ids(memory_db):
    existing = Entry(id="B", title="Local", type="bug")
    memory_db.add(existing)

    imported_entry = Entry(id="B", title="Different", type="bug")
    plan = ImportPlan(
        new_entries=[],
        conflicts=[Conflict(
            entry_id="B",
            local=existing,
            imported=imported_entry,
            fields_changed=["title"],
        )],
        identical=[],
    )
    executor = ImportExecutor(memory_db)
    result = executor.execute(plan, strategy="merge")

    assert result.success
    assert result.merged == 1

    # Original préservé
    assert memory_db.get("B").title == "Local"

    # Nouvelle entrée créée avec nouvel ID
    all_entries = memory_db.list_all()
    assert len(all_entries) == 2
    new_entry = [e for e in all_entries if e.id != "B"][0]
    assert new_entry.title == "Different"
```

**GREEN**: Implémenter `execute()` avec strategy="merge".

**Critères**:
- [ ] Génère nouvel ULID
- [ ] Préserve local
- [ ] Crée copie importée

---

### T012: Atomic Rollback
**Dépendances**: T009, T010, T011
**Fichiers**: `rekall/sync.py`
**Tests**: `tests/test_sync.py`

**TDD RED**:
```python
def test_rollback_on_error(memory_db, monkeypatch):
    # Simuler erreur pendant import
    original_count = len(memory_db.list_all())

    plan = ImportPlan(
        new_entries=[
            Entry(id="A", title="First", type="bug"),
            Entry(id="B", title="Second", type="bug"),  # Échouera
        ],
        conflicts=[],
        identical=[],
    )

    # Faire échouer le 2ème add
    call_count = [0]
    original_add = memory_db.add
    def failing_add(entry):
        call_count[0] += 1
        if call_count[0] == 2:
            raise sqlite3.IntegrityError("Simulated failure")
        original_add(entry)

    monkeypatch.setattr(memory_db, "add", failing_add)

    executor = ImportExecutor(memory_db)
    result = executor.execute(plan, strategy="skip")

    assert not result.success
    assert len(memory_db.list_all()) == original_count  # Rollback complet
```

**GREEN**: Implémenter transaction atomique avec rollback.

**Critères**:
- [ ] BEGIN TRANSACTION
- [ ] ROLLBACK on error
- [ ] Aucune modification partielle

---

## Phase 3: CLI Integration

### T013: Export Command Refactor
**Dépendances**: T004
**Fichiers**: `rekall/cli.py`
**Tests**: `tests/test_cli.py`

**TDD RED**:
```python
def test_cli_export_creates_rekall(runner, temp_db):
    # Add some entries
    result = runner.invoke(app, ["export", "backup.rekall"])

    assert result.exit_code == 0
    assert Path("backup.rekall").exists()
    assert zipfile.is_zipfile("backup.rekall")

def test_cli_export_with_project_filter(runner, temp_db):
    # Add entries with different projects
    runner.invoke(app, ["add", "bug", "Bug1", "-p", "proj1"])
    runner.invoke(app, ["add", "bug", "Bug2", "-p", "proj2"])

    result = runner.invoke(app, ["export", "backup.rekall", "--project", "proj1"])

    with zipfile.ZipFile("backup.rekall") as zf:
        data = json.loads(zf.read("entries.json"))
        assert len(data) == 1
        assert data[0]["project"] == "proj1"
```

**GREEN**: Refactorer `export` pour créer .rekall au lieu de .json/.md.

**Critères**:
- [ ] Format .rekall par défaut
- [ ] Filtres --project, --type, --since
- [ ] Rétrocompatibilité --format json/md

---

### T014: Import Command Base
**Dépendances**: T005, T007
**Fichiers**: `rekall/cli.py`
**Tests**: `tests/test_cli.py`

**TDD RED**:
```python
def test_cli_import_basic(runner, temp_db, tmp_path):
    # Create archive
    archive_path = tmp_path / "backup.rekall"
    entries = [Entry(id="A", title="Imported", type="bug")]
    RekallArchive.create(archive_path, entries)

    result = runner.invoke(app, ["import", str(archive_path), "--yes"])

    assert result.exit_code == 0
    assert "A" in result.output or "Imported" in result.output

def test_cli_import_invalid_file(runner, tmp_path):
    bad_file = tmp_path / "bad.rekall"
    bad_file.write_text("not a zip")

    result = runner.invoke(app, ["import", str(bad_file)])

    assert result.exit_code != 0
    assert "erreur" in result.output.lower() or "error" in result.output.lower()
```

**GREEN**: Implémenter commande `import_archive`.

**Critères**:
- [ ] Nom `import` (mot réservé → `import_archive`)
- [ ] Validation avant import
- [ ] Message de succès

---

### T015: --dry-run Flag
**Dépendances**: T014
**Fichiers**: `rekall/cli.py`
**Tests**: `tests/test_cli.py`

**TDD RED**:
```python
def test_cli_import_dry_run(runner, temp_db, tmp_path):
    # Setup: create archive + existing entry
    archive_path = tmp_path / "backup.rekall"
    RekallArchive.create(archive_path, [Entry(id="A", title="New", type="bug")])

    result = runner.invoke(app, ["import", str(archive_path), "--dry-run"])

    assert result.exit_code == 0
    assert "[NEW]" in result.output or "nouveau" in result.output.lower()
    # Vérifier que rien n'a été importé
    db_result = runner.invoke(app, ["show", "A"])
    assert db_result.exit_code != 0  # Entry not found
```

**GREEN**: Implémenter `--dry-run`.

**Critères**:
- [ ] Affiche preview sans modifier
- [ ] Format rsync-like
- [ ] Exit code 0

---

### T016: --yes Flag
**Dépendances**: T014
**Fichiers**: `rekall/cli.py`
**Tests**: `tests/test_cli.py`

**TDD RED**:
```python
def test_cli_import_prompts_without_yes(runner, temp_db, tmp_path):
    archive_path = tmp_path / "backup.rekall"
    RekallArchive.create(archive_path, [Entry(id="A", title="T", type="bug")])

    # Sans --yes, devrait demander confirmation
    result = runner.invoke(app, ["import", str(archive_path)], input="n\n")

    assert "confirm" in result.output.lower() or "continuer" in result.output.lower()

def test_cli_import_skips_prompt_with_yes(runner, temp_db, tmp_path):
    archive_path = tmp_path / "backup.rekall"
    RekallArchive.create(archive_path, [Entry(id="A", title="T", type="bug")])

    # Avec --yes, pas de prompt
    result = runner.invoke(app, ["import", str(archive_path), "--yes"])

    assert result.exit_code == 0
```

**GREEN**: Implémenter `--yes` pour skip confirmation.

**Critères**:
- [ ] Prompt par défaut
- [ ] --yes skip prompt
- [ ] Mode script friendly

---

### T017: --strategy Options
**Dépendances**: T009, T010, T011, T014
**Fichiers**: `rekall/cli.py`
**Tests**: `tests/test_cli.py`

**TDD RED**:
```python
def test_cli_import_strategy_skip(runner, temp_db, tmp_path):
    # Setup conflict
    runner.invoke(app, ["add", "bug", "Local", "-i", "CONFLICT_ID"])

    archive_path = tmp_path / "backup.rekall"
    RekallArchive.create(archive_path, [
        Entry(id="CONFLICT_ID", title="Imported", type="bug")
    ])

    result = runner.invoke(app, ["import", str(archive_path), "--strategy", "skip", "--yes"])

    # Local preserved
    show_result = runner.invoke(app, ["show", "CONFLICT_ID"])
    assert "Local" in show_result.output

def test_cli_import_strategy_replace(runner, temp_db, tmp_path):
    # Setup conflict
    runner.invoke(app, ["add", "bug", "Local", "-i", "CONFLICT_ID"])

    archive_path = tmp_path / "backup.rekall"
    RekallArchive.create(archive_path, [
        Entry(id="CONFLICT_ID", title="Imported", type="bug")
    ])

    result = runner.invoke(app, ["import", str(archive_path), "--strategy", "replace", "--yes"])

    # Imported overwrote
    show_result = runner.invoke(app, ["show", "CONFLICT_ID"])
    assert "Imported" in show_result.output
```

**GREEN**: Implémenter `--strategy skip|replace|merge`.

**Critères**:
- [ ] skip (défaut)
- [ ] replace + backup
- [ ] merge

---

### T018: Error Messages
**Dépendances**: T014
**Fichiers**: `rekall/cli.py`
**Tests**: `tests/test_cli.py`

**TDD RED**:
```python
def test_cli_import_file_not_found(runner):
    result = runner.invoke(app, ["import", "nonexistent.rekall"])
    assert result.exit_code != 0
    assert "not found" in result.output.lower() or "introuvable" in result.output.lower()

def test_cli_import_corrupted_archive(runner, tmp_path):
    archive_path = tmp_path / "corrupted.rekall"
    # Create then corrupt
    RekallArchive.create(archive_path, [Entry(id="A", title="T", type="bug")])
    archive_path.write_bytes(b"corrupted")

    result = runner.invoke(app, ["import", str(archive_path)])
    assert result.exit_code != 0
    assert "corrupt" in result.output.lower() or "invalide" in result.output.lower()

def test_cli_import_version_incompatible(runner, tmp_path):
    # Create archive with future version
    archive_path = tmp_path / "future.rekall"
    with zipfile.ZipFile(archive_path, 'w') as zf:
        zf.writestr("manifest.json", '{"format_version": "99.0", ...}')
        zf.writestr("entries.json", "[]")

    result = runner.invoke(app, ["import", str(archive_path)])
    assert result.exit_code != 0
    assert "version" in result.output.lower()
```

**GREEN**: Messages d'erreur détaillés et localisés.

**Critères**:
- [ ] Fichier introuvable
- [ ] Archive corrompue
- [ ] Version incompatible
- [ ] Suggestions correction

---

## Phase 4: TUI Integration

### T019: Menu Export/Import
**Dépendances**: T013, T014
**Fichiers**: `rekall/tui.py`
**Tests**: `tests/test_tui.py`

**TDD RED**:
```python
def test_tui_menu_has_export_import():
    from rekall.tui import MAIN_MENU_ITEMS

    menu_texts = [item.lower() for item in MAIN_MENU_ITEMS]
    assert any("export" in t and "import" in t for t in menu_texts)

def test_tui_export_import_submenu():
    from rekall.tui import get_export_import_submenu

    submenu = get_export_import_submenu()
    labels = [item["label"] for item in submenu]

    assert "Export complet" in labels or "Full export" in labels
    assert "Import" in labels
```

**GREEN**: Renommer menu "Export" → "Export / Import" avec sous-menu.

**Critères**:
- [ ] Menu principal mis à jour
- [ ] Sous-menu avec options
- [ ] Navigation ↑↓ Enter Esc

---

### T020: TUI Export Flow
**Dépendances**: T019
**Fichiers**: `rekall/tui.py`
**Tests**: `tests/test_tui.py`

**TDD RED**:
```python
def test_tui_export_prompts_path(monkeypatch):
    inputs = iter(["backup.rekall"])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))

    from rekall.tui import handle_export
    result = handle_export()

    assert result["path"] == "backup.rekall"

def test_tui_export_shows_success(capsys):
    from rekall.tui import handle_export
    # Mock successful export
    handle_export(path="test.rekall")

    captured = capsys.readouterr()
    assert "succès" in captured.out.lower() or "success" in captured.out.lower()
```

**GREEN**: Implémenter flow export TUI.

**Critères**:
- [ ] Prompt chemin fichier
- [ ] Option filtres (projet/type)
- [ ] Message succès avec stats

---

### T021: TUI Import Flow
**Dépendances**: T019
**Fichiers**: `rekall/tui.py`
**Tests**: `tests/test_tui.py`

**TDD RED**:
```python
def test_tui_import_prompts_path(monkeypatch):
    inputs = iter(["backup.rekall"])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))

    from rekall.tui import handle_import
    result = handle_import()

    assert result["path"] == "backup.rekall"

def test_tui_import_shows_preview():
    from rekall.tui import handle_import
    # Mock archive with entries
    result = handle_import(path="test.rekall", dry_run=True)

    assert "preview" in str(result).lower() or "[NEW]" in str(result)
```

**GREEN**: Implémenter flow import TUI.

**Critères**:
- [ ] Prompt chemin fichier
- [ ] Affiche preview
- [ ] Confirmation avant import

---

### T022: TUI Conflict Resolution Interactive
**Dépendances**: T021
**Fichiers**: `rekall/tui.py`
**Tests**: `tests/test_tui.py`

**TDD RED**:
```python
def test_tui_conflict_menu():
    from rekall.tui import show_conflict_menu

    conflict = Conflict(
        entry_id="X",
        local=Entry(id="X", title="Local", type="bug"),
        imported=Entry(id="X", title="Imported", type="bug"),
        fields_changed=["title"],
    )

    options = show_conflict_menu(conflict)

    assert "Garder local" in options or "Keep local" in options
    assert "Remplacer" in options or "Replace" in options
    assert "Fusionner" in options or "Merge" in options
```

**GREEN**: Menu interactif pour chaque conflit.

**Critères**:
- [ ] Affiche diff
- [ ] Options: garder/remplacer/fusionner
- [ ] Applique choix par conflit

---

## Phase 5: Polish

### T023: Progress Indicators
**Dépendances**: T013, T014
**Fichiers**: `rekall/cli.py`, `rekall/tui.py`
**Tests**: `tests/test_cli.py`

**TDD RED**:
```python
def test_cli_export_shows_progress(runner, temp_db):
    # Add many entries
    for i in range(100):
        runner.invoke(app, ["add", "bug", f"Bug{i}"])

    result = runner.invoke(app, ["export", "backup.rekall"])

    # Should show progress or spinner
    assert "%" in result.output or "exporting" in result.output.lower()
```

**GREEN**: Ajouter rich progress bars.

**Critères**:
- [ ] Progress bar export
- [ ] Progress bar import
- [ ] Spinner pour validation

---

### T024: Performance Optimization
**Dépendances**: T012
**Fichiers**: `rekall/sync.py`, `rekall/db.py`
**Tests**: `tests/test_performance.py`

**TDD RED**:
```python
def test_export_1000_entries_under_5s(memory_db, tmp_path, benchmark):
    # Add 1000 entries
    for i in range(1000):
        memory_db.add(Entry(id=f"E{i:04d}", title=f"Entry {i}", type="bug"))

    def export():
        RekallArchive.create(tmp_path / "big.rekall", memory_db.list_all())

    result = benchmark(export)
    assert result.stats.mean < 5.0  # < 5 secondes

def test_import_1000_entries_under_10s(memory_db, tmp_path, benchmark):
    # Create archive with 1000 entries
    entries = [Entry(id=f"E{i:04d}", title=f"Entry {i}", type="bug") for i in range(1000)]
    archive_path = tmp_path / "big.rekall"
    RekallArchive.create(archive_path, entries)

    def import_all():
        archive = RekallArchive.open(archive_path)
        plan = build_import_plan(memory_db, archive.get_entries())
        ImportExecutor(memory_db).execute(plan, strategy="skip")

    result = benchmark(import_all)
    assert result.stats.mean < 10.0  # < 10 secondes
```

**GREEN**: Batch inserts, optimize queries.

**Critères**:
- [ ] Export 1000 entries < 5s
- [ ] Import 1000 entries < 10s
- [ ] Compression > 50%

---

### T025: Documentation
**Dépendances**: Toutes les phases
**Fichiers**: `README.md`

**Critères**:
- [ ] Section Export/Import dans README
- [ ] Exemples CLI
- [ ] Exemples TUI
- [ ] Troubleshooting erreurs communes

---

## Résumé des Dépendances

```
T001 (dataclasses) ──┬── T002 (checksum) ──┬── T004 (create) ──── T005 (open/validate)
                     │                     │                            │
                     └── T003 (serialize) ─┘                            │
                                                                        │
T006 (conflict) ─── T007 (plan) ─── T008 (preview) ─── T009 (skip) ─── T010 (replace)
                                                              │              │
                                                              └── T011 (merge)
                                                                      │
                                                              T012 (rollback)

T004 ─── T013 (CLI export)
T005 + T007 ─── T014 (CLI import) ─── T015 (dry-run) ─── T016 (yes) ─── T017 (strategy)
                      │
                T018 (errors)

T013 + T014 ─── T019 (TUI menu) ─── T020 (TUI export) ─── T021 (TUI import) ─── T022 (interactive)

T012 + T013 + T014 ─── T023 (progress) ─── T024 (perf) ─── T025 (docs)
```

---

## Checklist Validation

- [ ] Tous les tests RED écrits avant implémentation
- [ ] Chaque tâche a critères d'acceptation clairs
- [ ] Dépendances respectées
- [ ] Pas d'import partiel (atomicité)
- [ ] Backup créé avant `--replace`
- [ ] Messages d'erreur détaillés
