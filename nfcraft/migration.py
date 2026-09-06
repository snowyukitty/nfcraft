"""Opt-in local workspace copy; never renames or deletes the original journal.

This is for stopped v0.1 schema-1 workspaces, not distributed synchronization.
The destination must not exist. Runtime credentials are never copied.
"""
from __future__ import annotations
from contextlib import closing
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import secrets
import shutil
import sqlite3
from .errors import OpsError
from .runtime import WorkspaceLock


def _summary(db_path: Path, mode: str) -> dict:
    try:
        with closing(sqlite3.connect(db_path.as_uri() + "?mode=ro", uri=True)) as db:
            db.row_factory = sqlite3.Row
            if db.execute("PRAGMA quick_check").fetchone()[0] != "ok":
                raise OpsError("MIGRATION_INTEGRITY", "The source database failed quick_check.")
            meta = dict(db.execute("SELECT key,value FROM meta").fetchall())
            if meta.get("schema") != "1" or meta.get("mode") != mode:
                raise OpsError("MIGRATION_SCHEMA", "Expected a schema-1 journal in the selected mode.")
            previous, count = "0" * 64, 0
            for row in db.execute("SELECT * FROM audit ORDER BY seq"):
                digest = hashlib.sha256((previous + row["at"] + row["kind"] + row["data"]).encode()).hexdigest()
                if row["prev_hash"] != previous or row["hash"] != digest:
                    raise OpsError("MIGRATION_AUDIT", "Source audit continuity failed. Investigate before importing.")
                previous, count = row["hash"], count + 1
            return {"mode": mode, "schema": 1,
                    "cards": db.execute("SELECT COUNT(*) FROM cards").fetchone()[0],
                    "batches": db.execute("SELECT COUNT(*) FROM batches").fetchone()[0],
                    "audit_events": count, "audit_head": previous}
    except sqlite3.Error as exc:
        raise OpsError("MIGRATION_DATABASE", "Could not inspect the source journal; no import performed.") from exc


def import_workspace(source_root: str | Path, destination_root: str | Path, mode: str,
                     *, apply: bool = False, confirmation: str = "") -> dict:
    if mode not in ("demo", "hardware"):
        raise OpsError("INVALID_MODE", "Choose demo or hardware explicitly.")
    source_root, destination_root = Path(source_root).expanduser(), Path(destination_root).expanduser()
    if source_root.is_symlink() or destination_root.is_symlink():
        raise OpsError("MIGRATION_SYMLINK", "Use real workspace roots, not symbolic links.")
    source = source_root.resolve() / mode
    destination = destination_root.resolve() / mode
    if source == destination or source in destination.parents or destination in source.parents:
        raise OpsError("MIGRATION_OVERLAP", "Source and destination must be distinct non-overlapping mode directories.")
    if not (source / "journal.sqlite3").is_file():
        raise OpsError("MIGRATION_SOURCE", "No source journal exists for this mode.")
    if source.is_symlink() or (source / "journal.sqlite3").is_symlink():
        raise OpsError("MIGRATION_SYMLINK", "Linked journals are not imported.")
    if destination.exists() or destination.is_symlink():
        raise OpsError("MIGRATION_DESTINATION_EXISTS", "Destination already exists. No merge or overwrite is permitted.")
    summary = _summary(source / "journal.sqlite3", mode)
    result = {"apply": False, "source": str(source), "destination": str(destination), **summary,
              "notice": "Stop the old app. Import retains the original; never operate both copies as independent writers."}
    if not apply:
        return result
    if confirmation != f"IMPORT {mode}":
        raise OpsError("CONFIRMATION_REQUIRED", f"Explicit confirmation must be IMPORT {mode}.")
    lock = WorkspaceLock(source)
    staging = None
    try:
        summary = _summary(source / "journal.sqlite3", mode)
        destination.parent.mkdir(parents=True, exist_ok=True)
        staging = destination.parent / (".import-" + secrets.token_hex(8))
        staging.mkdir(mode=0o700)
        with closing(sqlite3.connect((source / "journal.sqlite3").as_uri() + "?mode=ro", uri=True)) as old:
            with closing(sqlite3.connect(staging / "journal.sqlite3")) as new:
                old.backup(new)
        if mode == "demo" and (source / "virtual-tags").exists():
            tag_root = source / "virtual-tags"
            if tag_root.is_symlink() or any(p.is_symlink() for p in tag_root.rglob("*")):
                raise OpsError("MIGRATION_SYMLINK", "Linked virtual-card files are not imported.")
            shutil.copytree(tag_root, staging / "virtual-tags")
        if _summary(staging / "journal.sqlite3", mode) != summary:
            raise OpsError("MIGRATION_VERIFY", "The copied journal failed verification.")
        report = {**result, **summary, "apply": True, "completed_at": datetime.now(timezone.utc).isoformat(),
                  "credentials_copied": False, "approval_copied": False}
        (staging / "import-report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
        # A per-destination lock coordinates this tool with another importer. No existing journal is replaced.
        from .runtime import WorkspaceLock as Lock
        gate_dir = destination.parent / ".migration-lock"
        gate = Lock(gate_dir)
        try:
            if destination.exists():
                raise OpsError("MIGRATION_DESTINATION_EXISTS", "Destination appeared during import; refusing replacement.")
            staging.rename(destination)
            staging = None
        finally:
            gate.close()
        return report
    finally:
        if staging is not None:
            shutil.rmtree(staging)
        lock.close()
