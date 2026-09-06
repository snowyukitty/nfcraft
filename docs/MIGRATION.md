# NFC Card Ops -> nfcraft: data-preserving migration

## What changed and what did not

The product, Python package and default data root are now `nfcraft`. SQLite and public manifest schema remain 1. Existing slugs/URLs/UID mappings and audit data are not renamed. `nfcctl.py`/`nfcctl` and `nfc_*` MCP tools remain compatibility aliases. A previous MCP config must point at the new repo/interpreter path and can use `nfcraftctl.py`.

Default Windows roots: old `%LOCALAPPDATA%\NfcCardOps`; new `%LOCALAPPDATA%\nfcraft`. Each contains separate `demo` and `hardware` subdirectories. A legacy journal with no corresponding new default journal makes the app stop with `LEGACY_WORKSPACE_FOUND` rather than silently open an empty inventory.

## Option 1: keep the original data in place

Stop the old application. Make a database backup via its app before switching. Use the same explicit root for the app **and every CLI/MCP client**:

```powershell
.\.venv\Scripts\python.exe run.py --data-dir "$env:LOCALAPPDATA\NfcCardOps"
.\.venv\Scripts\python.exe nfcraftctl.py --data-dir "$env:LOCALAPPDATA\NfcCardOps" status
```

The root is not the `demo` subfolder: the program appends the selected mode. This is an explicit choice, not automatic conversion. New code may append audit/recovery events when it opens existing state; keep backups. Do not run both versions at once.

## Option 2: explicit non-destructive import

Stop the old app and all writers. Keep an independent backup. The importer inspects a known **schema-1** source, checks SQLite and audit continuity, and uses SQLite's backup API to copy its journal. Demo virtual cards are copied; agent-runtime tokens/locks/approval are not. Other files and original backups remain at the source. It never merges into or overwrites an existing destination mode directory.

Inspect first (no destination is created):

```powershell
.\.venv\Scripts\python.exe scripts\import_legacy.py --source-root "$env:LOCALAPPDATA\NfcCardOps" --destination-root "$env:LOCALAPPDATA\nfcraft" --mode demo
```

After reviewing the source, destination, mode and counts:

```powershell
.\.venv\Scripts\python.exe scripts\import_legacy.py --source-root "$env:LOCALAPPDATA\NfcCardOps" --destination-root "$env:LOCALAPPDATA\nfcraft" --mode demo --apply --confirm "IMPORT demo"
```

Hardware uses a **separate invocation**, `--mode hardware --apply --confirm "IMPORT hardware"`, only after the owner approves copying that real journal. It does not write a card or enable hardware writes. Do not put `hardware` data in a `demo` directory or change the database mode marker.

The importer locks the source against the app's writer lock, validates the copied journal, writes an import report and installs it only into a new destination. It preserves the original journal; its lock file/access permissions may be touched. Filesystem/import interruption can leave a staging directory; preserve it for diagnosis and never mistake it for an active workspace. It is not a distributed transaction or a general backup product.

## After import

Start nfcraft, compare card/batch counts, original assignments, audit continuity and mode, and verify that nothing is armed. Reconnect CLI/MCP to the correct root. Pending writes are quarantined on normal app startup, never retried automatically. Keep the original and external backup as archives.

**Choose one authoritative copy.** After new writes or profile revisions in nfcraft, the old copy is stale; do not continue provisioning/publishing from both. Reader exclusivity cannot prevent two computers from using divergent copied journals. A schema-1 label alone does not make rolling back code/data safe; see `RELEASE-PROCESS.md`.

The migration helper has simulated unit coverage in this handoff. No actual owner data was imported and no Windows migration was performed here.

Reference for the backup mechanism: https://docs.python.org/3/library/sqlite3.html#sqlite3.Connection.backup (checked 2026-09-05).
