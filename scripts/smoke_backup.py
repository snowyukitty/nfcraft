"""Rehearse backup/restore and original-identity recovery on synthetic copies."""
import json
from pathlib import Path
import shutil
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from nfcraft.adapters.mock import MockReader
from nfcraft.engine import Engine
from nfcraft.store import Store


def main():
    with tempfile.TemporaryDirectory(prefix="nfcraft-restore-") as directory:
        root = Path(directory)
        source = root / "source"
        restored = root / "restored"
        original = Engine(Store(source / "journal.sqlite3"), MockReader(source / "virtual-tags"))
        try:
            batch = original.create_batch({"name": "Restore drill", "target": 2, "base": "https://tap.example.com"})
            original.arm({"batch_id": batch["id"], "confirmation": "ARM Restore drill"})
            original.reader.insert()
            original.tick()
            original.reader.remove()
            original.tick()
            uncertain_uid = original.reader.insert("interrupted")
            original.tick()
            before = original.store.inventory()
            assert {c["status"] for c in before} == {"verified", "quarantined"}
            original.store.backup(root / "backup.sqlite3")
        finally:
            original.shutdown()
        restored.mkdir()
        shutil.copy2(root / "backup.sqlite3", restored / "journal.sqlite3")
        shutil.copytree(source / "virtual-tags", restored / "virtual-tags")
        engine = Engine(Store(restored / "journal.sqlite3"), MockReader(restored / "virtual-tags"))
        try:
            assert engine.store.db.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
            assert engine.store.inventory() == before
            assert engine.armed is None and engine.store.check_audit()["ok"]
            engine.reader.insert(uid=uncertain_uid)
            engine.reader.clear_fault()
            engine.arm({"batch_id": batch["id"], "confirmation": "ARM Restore drill", "limit": 1, "recover_uid": uncertain_uid})
            engine.tick()
            after = engine.store.inventory()
            assert all(c["status"] == "verified" for c in after)
            assert [(c["id"], c["uid"], c["url"]) for c in after] == [(c["id"], c["uid"], c["url"]) for c in before]
            assert engine.store.check_audit()["ok"]
        finally:
            engine.shutdown()
        archive = Store(source / "journal.sqlite3")
        try:
            assert archive.inventory() == before
        finally:
            archive.close()
    print(json.dumps({"result": "PASS", "scope": "synthetic backup/restored copies only", "checks": [
        "SQLite integrity and audit", "all identities and URLs preserved", "restore remains disarmed",
        "quarantined original identity recovers", "source archive unchanged"]}, indent=2))


if __name__ == "__main__":
    main()
