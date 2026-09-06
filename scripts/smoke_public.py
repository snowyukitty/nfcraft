"""Real local Wrangler/D1 smoke using disposable simulated exports only.

No account selection, remote bindings, cloud mutation, or owner data access.
Run npm ci in cloudflare first. Evidence/state remain under .local.
"""
from __future__ import annotations
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import time
from urllib.request import build_opener, ProxyHandler, Request
from urllib.error import HTTPError

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from nfcraft.adapters.mock import MockReader
from nfcraft.engine import Engine
from nfcraft.exporting import manifest_sql
from nfcraft.store import Store


def main():
    node = shutil.which("node")
    wrangler = ROOT / "cloudflare/node_modules/wrangler/bin/wrangler.js"
    if not node or not wrangler.is_file():
        raise SystemExit("NOT_RUN: install Node and run npm ci in cloudflare first.")
    evidence = ROOT / ".local/evidence"
    evidence.mkdir(parents=True, exist_ok=True)
    root = Path(tempfile.mkdtemp(prefix="public-", dir=evidence))
    config = root / "wrangler.json"
    config.write_text(json.dumps({"name": "nfcraft-local-test", "main": str(ROOT / "cloudflare/worker.mjs"),
        "compatibility_date": "2026-09-01", "workers_dev": False,
        "d1_databases": [{"binding": "DB", "database_name": "nfcraft-local-test",
                          "database_id": "00000000-0000-0000-0000-000000000000"}]}), encoding="utf-8")
    engine = Engine(Store(root / "demo.sqlite3"), MockReader(root / "virtual-tags"))
    try:
        batch = engine.create_batch({"name": "Local integration", "target": 2, "base": "https://tap.example.com"})
        engine.arm({"batch_id": batch["id"], "confirmation": "ARM Local integration"})
        for _ in range(2):
            engine.reader.insert()
            engine.tick()
            engine.reader.remove()
            engine.tick()
        manifest = engine.store.manifest()
        assert len(manifest["routes"]) == 2
        stale_sql = root / "older-fixture.sql"
        stale_sql.write_text(manifest_sql(manifest, allow_demo=True), encoding="utf-8")
        # All fixture changes stay explicitly simulated and are re-exported.
        engine.store.update_profile({"name": "Local <script> & 測試", "headline": "Demo only",
                                     "bio": "Local integration", "email": "demo@example.com", "website": "https://example.com"})
        manifest = engine.store.manifest()
        suspended_slug = manifest["routes"][1]["slug"]
        card = next(c for c in engine.store.inventory() if c["slug"] == suspended_slug)
        engine.store.set_route_state(card["id"], "suspended")
        manifest = engine.store.manifest()
        sql = root / "fixture.sql"
        sql.write_text(manifest_sql(manifest, allow_demo=True), encoding="utf-8")
    finally:
        engine.shutdown()
    env = {k: v for k, v in os.environ.items() if not k.startswith(("CLOUDFLARE_", "CF_"))}
    env.update({"WRANGLER_SEND_METRICS": "false", "CI": "true"})
    common = [node, str(wrangler)]
    local = ["--config", str(config), "--local", "--persist-to", str(root / "state")]
    for name, file in (("schema", ROOT / "cloudflare/schema.sql"), ("fixture", sql), ("retry", sql), ("older-revision", stale_sql)):
        result = subprocess.run(common + ["d1", "execute", "DB", *local, "--file", str(file)],
                                cwd=root, env=env, capture_output=True, timeout=60)
        (root / (name + ".log")).write_bytes(result.stdout + result.stderr)
        if result.returncode:
            raise RuntimeError(f"Local D1 {name} failed; inspect {root.name}/{name}.log")
    log = (root / "worker.log").open("wb")
    proc = subprocess.Popen(common + ["dev", *local, "--ip", "127.0.0.1", "--port", "0",
                            "--inspector-port", "0", "--show-interactive-dev-session=false"],
                            cwd=root, env=env, stdout=log, stderr=subprocess.STDOUT)
    try:
        deadline = time.monotonic() + 45
        origin = None
        while time.monotonic() < deadline and proc.poll() is None:
            match = re.search(r"Ready on (http://127\.0\.0\.1:\d+)", (root / "worker.log").read_text(encoding="utf-8", errors="replace"))
            if match:
                origin = match[1]
                break
            time.sleep(0.2)
        if not origin:
            raise RuntimeError(f"Local Worker did not start; inspect {root.name}/worker.log")
        opener = build_opener(ProxyHandler({}))
        active, suspended = ["/c/" + row["slug"] for row in manifest["routes"]]
        checks = []
        for path, method, expected in ((active, "GET", 200), (active, "HEAD", 200),
                (active + "/contact.vcf", "GET", 200), (suspended, "GET", 410),
                ("/c/" + "x" * 22, "GET", 404), ("/", "GET", 404), (active, "POST", 405)):
            try:
                response = opener.open(Request(origin + path, method=method), timeout=10)
            except HTTPError as exc:
                response = exc
            with response:
                content = response.read().decode("utf-8")
                assert response.status == expected, (method, expected, response.status)
                assert response.headers["X-Content-Type-Options"] == "nosniff"
                assert response.headers["Cache-Control"] == "no-store"
                assert "frame-ancestors 'none'" in response.headers["Content-Security-Policy"]
                if path == active and method == "GET":
                    assert "Local &lt;script&gt; &amp; 測試" in content and "<script>" not in content
                if path.endswith(".vcf"):
                    assert "BEGIN:VCARD\r\n" in content and "text/vcard" in response.headers["Content-Type"]
                if method == "HEAD":
                    assert not content
                checks.append({"method": method, "route": "vcard" if path.endswith(".vcf") else "card/root", "status": response.status})
        summary = {"result": "PASS", "scope": "real local Wrangler + D1; simulated fixtures", "checks": checks,
                   "idempotent_reimport": "PASS", "older_revision_preserved": "PASS", "remote_deployment": "NOT_RUN"}
        if "--browser" in sys.argv:
            result = subprocess.run([node, str(ROOT / "scripts/smoke_recipient.mjs"), origin, active, str(root)],
                                    cwd=ROOT, capture_output=True, timeout=45)
            (root / "browser.log").write_bytes(result.stdout + result.stderr)
            if result.returncode:
                raise RuntimeError(f"Recipient browser check failed; inspect {root.name}/browser.log")
            summary["recipient_browser"] = "PASS: 375px isolated Edge, not physical phone QA"
        (root / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
        print(json.dumps(summary, indent=2))
        print("Evidence:", root.relative_to(ROOT))
    finally:
        if os.name == "nt" and proc.poll() is None:
            subprocess.run(["taskkill", "/PID", str(proc.pid), "/T", "/F"], capture_output=True, timeout=10)
        elif proc.poll() is None:
            proc.terminate()
        proc.wait(timeout=10)
        log.close()


if __name__ == "__main__":
    main()
