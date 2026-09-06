"""Inventory scope, public export review, and operator authority regressions."""
import csv
import io
import json
from pathlib import Path
import tempfile
import threading
import unittest
from urllib.request import Request, build_opener, ProxyHandler
from urllib.error import HTTPError

from nfcraft.adapters.mock import MockReader
from nfcraft.engine import Engine
from nfcraft.errors import OpsError
from nfcraft.library import inventory_page, normalize_filters, publication_review, select_cards
from nfcraft.manifest import validate_manifest
from nfcraft.server import LocalServer
from nfcraft.store import Store


class LibraryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.store = Store(self.root / "journal.sqlite3")
        self.reader = MockReader(self.root / "tags")
        self.engine = Engine(self.store, self.reader)
        self.batch = self.engine.create_batch({"name": "Studio 測試", "target": 4, "base": "https://tap.example.com"})
        self.engine.arm({"batch_id": self.batch["id"], "confirmation": "ARM Studio 測試"})
        for _ in range(3):
            self.reader.insert(); self.engine.tick(); self.reader.remove(); self.engine.tick()
        self.reader.insert("interrupted"); self.engine.tick()
        self.cards = self.store.inventory()
        self.store.set_route_state(self.cards[1]["id"], "suspended")
        self.server = LocalServer(self.engine, self.root, 0)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.opener = build_opener(ProxyHandler({}))

    def tearDown(self):
        self.server.shutdown(); self.server.server_close(); self.thread.join()
        self.engine.shutdown(); self.temp.cleanup()

    def request(self, path, payload=None, agent=False):
        token = self.server.agent_token if agent else self.server.operator_token
        request = Request(self.server.origin + path,
            data=json.dumps(payload).encode() if payload is not None else None,
            headers={"Authorization": "Bearer " + token, "Content-Type": "application/json"})
        try:
            with self.opener.open(request) as response:
                text = response.read().decode("utf-8")
                return response.status, json.loads(text) if "json" in response.headers["Content-Type"] else text
        except HTTPError as exc:
            return exc.code, json.load(exc)

    def test_guide_assets_are_allowlisted_without_exposing_workspace(self):
        for path, marker in (("/guide.html", "繁體中文"), ("/guide.css", "--paper"),
                             ("/guide.js", "data-language"), ("/icons/favicon.svg", "<svg")):
            with self.opener.open(self.server.origin + path) as response:
                self.assertEqual(response.status, 200)
                self.assertIn(marker, response.read().decode("utf-8"))
                self.assertIn("default-src 'self'", response.headers["Content-Security-Policy"])
        for path in ("/icons/../../journal.sqlite3", "/icons/build/icon.ico", "/guide.html/../journal.sqlite3"):
            with self.assertRaises(HTTPError) as caught:
                self.opener.open(self.server.origin + path)
            self.assertEqual(caught.exception.code, 404)

    def test_unicode_case_insensitive_label_and_uid_search(self):
        for query in ("sTuDiO 測試 / 0001", self.cards[-1]["uid"].upper(), self.cards[-1]["url"]):
            self.assertEqual([c["id"] for c in select_cards(self.cards, {"q": query})], [self.cards[-1]["id"]])

    def test_literal_search_has_no_sql_wildcards(self):
        for query in ("%", "_not_a_card_", "' OR 1=1 --"):
            self.assertEqual(select_cards(self.cards, {"q": query}), [])

    def test_combined_filters_and_empty_selection(self):
        page = inventory_page(self.store, {"batch": self.batch["id"], "status": "verified", "route": "suspended"})
        self.assertEqual((page["matched"], page["exportable"]), (1, 1))
        self.assertEqual(inventory_page(self.store, {"batch": "missing"})["matched"], 0)

    def test_pagination_is_stable_and_does_not_duplicate(self):
        first = inventory_page(self.store, {}, 0, 2)
        second = inventory_page(self.store, {}, 2, 2)
        self.assertEqual([c["id"] for c in first["cards"] + second["cards"]], [c["id"] for c in self.store.inventory()])
        self.assertEqual(inventory_page(self.store, {}, 999, 2)["offset"], 2)

    def test_invalid_filters_and_pages_fail_closed(self):
        for value in ({"status": "issued"}, {"q": []}, {"route": "live"}, {"q": "x" * 201}, {"q": "\n"}, {"private": "yes"}):
            with self.subTest(value=value), self.assertRaises(OpsError): normalize_filters(value)
        for offset, limit in ((-1, 2), (0, 101), (0, 0), (True, 2)):
            with self.assertRaises(OpsError): inventory_page(self.store, {}, offset, limit)

    def test_api_csv_matches_entire_filter_not_page(self):
        status, page = self.request("/api/inventory?status=verified&limit=1", agent=True)
        self.assertEqual(status, 200); self.assertEqual(len(page["cards"]), 1)
        status, text = self.request("/api/inventory.csv?status=verified", agent=True)
        rows = list(csv.DictReader(io.StringIO(text)))
        self.assertEqual(len(rows), page["matched"])
        self.assertTrue(all(row["status"] == "verified" for row in rows))
        self.assertIn("uid", rows[0])

    def test_api_refuses_repeated_or_unknown_filter(self):
        for path in ("/api/inventory?status=verified&status=quarantined", "/api/inventory?unknown=1", "/api/inventory?limit=no", "/api/inventory?" + "q=x&" * 9):
            self.assertEqual(self.request(path)[0], 409)

    def test_public_review_excludes_private_and_quarantined_data(self):
        review = publication_review(self.store)
        self.assertEqual((review["matched"], review["excluded"], review["enabled"], review["suspended"]), (4, 1, 2, 1))
        validate_manifest(review["manifest"], allow_demo=True)
        text = json.dumps(review["manifest"])
        for card in self.cards: self.assertNotIn(card["uid"], text)
        self.assertNotIn("original_hex", text)
        self.assertEqual(len(publication_review(self.store, {"q": "0001"})["manifest"]["routes"]), 1)
        self.assertEqual(publication_review(self.store, {"q": "0001"})["other_local_routes_sharing_profiles"], 2)

    def test_empty_review_does_not_export(self):
        _, review = self.request("/api/publication/review", {"filters": {"status": "quarantined"}})
        status, result = self.request("/api/publication/export", {"filters": review["filters"], "sha256": review["manifest"]["sha256"]})
        self.assertEqual(status, 409); self.assertEqual(result["error"]["code"], "NOTHING_TO_EXPORT")

    def test_reviewed_export_matches_hash_and_remains_not_deployed(self):
        _, review = self.request("/api/publication/review", {"filters": {"q": "0001"}})
        status, manifest = self.request("/api/publication/export", {"filters": review["filters"], "sha256": review["manifest"]["sha256"]})
        self.assertEqual(status, 200); self.assertEqual(manifest["sha256"], review["manifest"]["sha256"])
        self.assertEqual(len(manifest["routes"]), 1)
        event = json.loads(self.store.events()[0]["data"])
        self.assertFalse(event["deployed"])
        self.assertTrue(self.store.check_audit()["ok"])

    def test_profile_or_route_change_invalidates_review(self):
        for change in (lambda: self.store.update_profile({"name": "Changed"}),
                       lambda: self.store.set_route_state(self.cards[-1]["id"], "suspended")):
            _, review = self.request("/api/publication/review", {})
            change()
            status, error = self.request("/api/publication/export", {"sha256": review["manifest"]["sha256"]})
            self.assertEqual(status, 409); self.assertEqual(error["error"]["code"], "EXPORT_CHANGED")

    def test_review_permissions_and_legacy_manifest_compatibility(self):
        for path in ("/api/publication/review", "/api/publication/export"):
            self.assertEqual(self.request(path, {}, agent=True)[0], 403)
        status, value = self.request("/api/manifest", agent=True)
        self.assertEqual(status, 200); self.assertEqual(len(value["routes"]), 3)
        validate_manifest(value, allow_demo=True)
