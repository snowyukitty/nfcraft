"""Exercise a child demo daemon plus CLI/MCP in a disposable temp workspace.

Never uses the user's workspace, a physical reader, or any operator token.
The token inside the generated agent-runtime file is used locally, never logged.
"""
from __future__ import annotations
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import time
from urllib.request import Request, build_opener, ProxyHandler
from urllib.error import HTTPError

ROOT = Path(__file__).resolve().parents[1]


def main():
    with tempfile.TemporaryDirectory(prefix="nfcraft-smoke-") as directory:
        root = Path(directory)
        proc = subprocess.Popen([sys.executable, str(ROOT / "run.py"), "--mode", "demo", "--data-dir", str(root),
                                 "--port", "0", "--no-browser"], cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        try:
            runtime_file = root / "demo" / "agent-runtime.json"
            deadline = time.monotonic() + 15
            while not runtime_file.is_file():
                if proc.poll() is not None or time.monotonic() > deadline:
                    raise RuntimeError("Demo daemon did not start.")
                time.sleep(0.1)
            runtime = json.loads(runtime_file.read_text(encoding="utf-8"))
            opener = build_opener(ProxyHandler({}))
            req = Request(runtime["origin"] + "/api/state", headers={"Authorization": "Bearer " + runtime["token"]})
            with opener.open(req, timeout=5) as response:
                state = json.load(response)
            assert state["mode"] == "demo" and state["hardware_qualified"] is False
            prefix = [sys.executable, str(ROOT / "nfcraftctl.py"), "--data-dir", str(root)]
            result = subprocess.run(prefix + ["status"], cwd=ROOT, capture_output=True, timeout=10, check=True)
            assert json.loads(result.stdout)["mode"] == "demo"
            result = subprocess.run(prefix + ["batch-create", "--name", "Process smoke", "--count", "2", "--base", "https://tap.example.com"], cwd=ROOT, capture_output=True, timeout=10, check=True)
            assert json.loads(result.stdout)["target"] == 2
            # The machine credential must not arm even a synthetic test batch.
            req = Request(runtime["origin"] + "/api/arm", data=b"{}", headers={"Authorization": "Bearer " + runtime["token"], "Content-Type": "application/json"})
            try:
                opener.open(req, timeout=5)
                raise AssertionError("Machine credential unexpectedly armed a batch")
            except HTTPError as exc:
                assert exc.code == 403
            messages = [{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2025-11-25"}},
                        {"jsonrpc": "2.0", "method": "notifications/initialized"},
                        {"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {"name": "nfc_status", "arguments": {}}}]
            result = subprocess.run(prefix + ["mcp"], input="".join(json.dumps(m) + "\n" for m in messages),
                                    cwd=ROOT, capture_output=True, text=True, timeout=10, check=True)
            replies = [json.loads(line) for line in result.stdout.splitlines()]
            assert len(replies) == 2 and replies[0]["result"]["serverInfo"]["name"] == "nfcraft"
            payload = json.loads(replies[1]["result"]["content"][0]["text"])
            assert payload["mode"] == "demo" and payload["armed"] is None
            print(json.dumps({"result": "PASS", "scope": "temporary mock workspace only", "checks": ["daemon startup", "CLI state", "CLI draft batch", "agent arming denied", "MCP initialize/notification/tool"], "physical_nfc": "NOT_RUN"}, indent=2))
        finally:
            proc.terminate()
            try:
                proc.wait(timeout=8)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=5)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
