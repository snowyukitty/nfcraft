from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import tempfile
import tomllib
import unittest
from unittest.mock import patch
from nfcraft import __version__
from nfcraft.adapters.mock import MockReader
from nfcraft.engine import Engine
from nfcraft.errors import OpsError
from nfcraft.exporting import manifest_sql
from nfcraft.manifest import validate_manifest
from nfcraft.migration import import_workspace
from nfcraft.runtime import workspace, WorkspaceLock
from nfcraft.store import Store


class HandoffTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.directory = self.root / "old" / "demo"
        self.directory.mkdir(parents=True)
        self.store = Store(self.directory / "journal.sqlite3")
        self.reader = MockReader(self.directory / "virtual-tags")
        self.engine = Engine(self.store, self.reader)

    def tearDown(self):
        self.engine.shutdown()
        self.tmp.cleanup()

    def provision(self):
        batch = self.engine.create_batch({"name": "Rebrand", "target": 1, "base": "https://tap.example.com"})
        self.engine.arm({"batch_id": batch["id"], "confirmation": "ARM Rebrand"})
        self.reader.insert()
        self.engine.tick()
        return self.store.manifest()

    def resigned(self, data):
        body = {k: data[k] for k in ("schema", "simulated", "profiles", "routes")}
        data["sha256"] = hashlib.sha256(json.dumps(body, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        return data

    def test_metadata_version_agrees(self):
        project = tomllib.loads((Path(__file__).resolve().parents[1] / "pyproject.toml").read_text())
        self.assertEqual(project["project"]["name"], "nfcraft")
        self.assertEqual(project["project"]["version"], __version__)
        self.assertEqual(self.engine.snapshot()["version"], __version__)

    def test_default_workspace_name(self):
        with patch.dict(os.environ, {"LOCALAPPDATA": str(self.root)}):
            self.assertEqual(workspace(), self.root / "nfcraft" / "demo")

    def test_legacy_workspace_detected_without_creating_new(self):
        previous = self.root / "NfcCardOps" / "demo"
        previous.mkdir(parents=True)
        (previous / "journal.sqlite3").touch()
        with patch.dict(os.environ, {"LOCALAPPDATA": str(self.root)}):
            with self.assertRaises(OpsError) as e:
                workspace()
            self.assertEqual(e.exception.code, "LEGACY_WORKSPACE_FOUND")
        self.assertFalse((self.root / "nfcraft").exists())

    def test_explicit_root_can_use_existing_workspace(self):
        self.assertEqual(workspace("demo", self.root / "old"), self.directory)

    def test_invalid_mode_rejected(self):
        with self.assertRaises(OpsError):
            workspace("../escape", self.root)

    def test_import_plan_makes_no_destination(self):
        self.provision()
        result = import_workspace(self.root / "old", self.root / "new", "demo")
        self.assertFalse(result["apply"])
        self.assertEqual(result["cards"], 1)
        self.assertFalse((self.root / "new").exists())

    def test_import_keeps_identities_and_does_not_copy_tokens(self):
        self.provision()
        old_ids = [(c["id"], c["uid"], c["url"]) for c in self.store.inventory()]
        (self.directory / "agent-runtime.json").write_text('{"token":"test-only-token"}')
        result = import_workspace(self.root / "old", self.root / "new", "demo", apply=True, confirmation="IMPORT demo")
        dest = self.root / "new" / "demo"
        self.assertTrue(result["apply"])
        self.assertFalse((dest / "agent-runtime.json").exists())
        self.assertTrue((dest / "virtual-tags").exists())
        new = Store(dest / "journal.sqlite3")
        try:
            self.assertEqual(old_ids, [(c["id"], c["uid"], c["url"]) for c in new.inventory()])
            self.assertTrue(new.check_audit()["ok"])
        finally:
            new.close()
        self.assertEqual(old_ids, [(c["id"], c["uid"], c["url"]) for c in self.store.inventory()])

    def test_import_rejects_missing_confirmation(self):
        with self.assertRaises(OpsError):
            import_workspace(self.root / "old", self.root / "new", "demo", apply=True)

    def test_import_rejects_existing_destination(self):
        (self.root / "new" / "demo").mkdir(parents=True)
        with self.assertRaises(OpsError):
            import_workspace(self.root / "old", self.root / "new", "demo")

    def test_import_rejects_running_source(self):
        lock = WorkspaceLock(self.directory)
        try:
            with self.assertRaises(OpsError) as e:
                import_workspace(self.root / "old", self.root / "new", "demo", apply=True, confirmation="IMPORT demo")
            self.assertEqual(e.exception.code, "WORKSPACE_BUSY")
        finally:
            lock.close()

    def test_import_rejects_bad_audit(self):
        self.provision()
        self.store.db.execute("UPDATE audit SET data='{}' WHERE seq=1")
        with self.assertRaises(OpsError) as e:
            import_workspace(self.root / "old", self.root / "new", "demo")
        self.assertEqual(e.exception.code, "MIGRATION_AUDIT")

    def test_unknown_data_in_planned_region_not_overwritten(self):
        batch = self.engine.create_batch({"name": "Hidden", "target": 1, "base": "https://tap.example.com"})
        self.engine.arm({"batch_id": batch["id"], "confirmation": "ARM Hidden"})
        self.reader.insert()
        area = bytearray(self.reader.read_area())
        area[12] = 0x42
        self.reader.card["area"] = area.hex()
        self.engine.tick()
        self.assertEqual(self.engine.last["code"], "OCCUPIED_WRITE_REGION")
        self.assertEqual(self.reader.write_count, 0)
        self.assertEqual(len(self.store.inventory()), 0)

    def test_manifest_checksum_is_checked(self):
        manifest = self.provision()
        manifest["profiles"][0]["name"] = "Unreviewed change"
        with self.assertRaises(OpsError) as e:
            validate_manifest(manifest, allow_demo=True)
        self.assertEqual(e.exception.code, "MANIFEST_CHECKSUM")

    def test_manifest_missing_simulation_marker(self):
        manifest = self.provision()
        del manifest["simulated"]
        with self.assertRaises(OpsError):
            manifest_sql(manifest, allow_demo=True)

    def test_manifest_rejects_duplicate_slug(self):
        manifest = self.provision()
        manifest["routes"].append(dict(manifest["routes"][0]))
        with self.assertRaises(OpsError):
            manifest_sql(self.resigned(manifest), allow_demo=True)

    def test_manifest_rejects_private_uid_field(self):
        manifest = self.provision()
        manifest["routes"][0]["uid"] = "test-only"
        with self.assertRaises(OpsError):
            manifest_sql(self.resigned(manifest), allow_demo=True)

    def test_manifest_rejects_url_slug_mismatch(self):
        manifest = self.provision()
        manifest["routes"][0]["url"] = "https://tap.example.com/c/" + "B" * 22
        with self.assertRaises(OpsError):
            manifest_sql(self.resigned(manifest), allow_demo=True)

    def test_manifest_rejects_boolean_revision(self):
        manifest = self.provision()
        manifest["profiles"][0]["revision"] = True
        with self.assertRaises(OpsError):
            manifest_sql(self.resigned(manifest), allow_demo=True)

    def test_manifest_real_marker_does_not_allow_demo_host(self):
        manifest = self.provision()
        manifest["simulated"] = False
        with self.assertRaises(OpsError):
            manifest_sql(self.resigned(manifest))

    def test_valid_manifest_roundtrip(self):
        manifest = self.provision()
        self.assertIn("INSERT INTO routes", manifest_sql(manifest, allow_demo=True))
