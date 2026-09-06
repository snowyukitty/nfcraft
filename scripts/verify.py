"""Run hardware-free checks and save explicit PASS/FAIL/NOT_RUN evidence.

No package installation, cloud calls, reader access, or production state changes.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]


def main(argv=None):
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / ".local" / "verification")
    parser.add_argument("--require-node", action="store_true")
    args = parser.parse_args(argv)
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    node = shutil.which("node")
    checks = [("python-unittest", [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"]),
              ("python-compile", [sys.executable, "-m", "compileall", "-q", "nfcraft", "scripts", "tests"]),
              ("demo-process-smoke", [sys.executable, "scripts/smoke_demo.py"]),
              ("ui-syntax", [node, "--check", "nfcraft/web/app.js"] if node else None),
              ("library-syntax", [node, "--check", "nfcraft/web/library.js"] if node else None),
              ("guide-syntax", [node, "--check", "nfcraft/web/guide.js"] if node else None),
              ("worker-syntax", [node, "--check", "cloudflare/worker.mjs"] if node else None),
              ("worker-tests", [node, "--test", "cloudflare/worker.test.mjs"] if node else None)]
    results = []
    for name, command in checks:
        if command is None:
            result = {"name": name, "status": "NOT_RUN", "reason": "Node.js not available"}
        else:
            started = time.monotonic()
            try:
                run = subprocess.run(command, cwd=ROOT, capture_output=True, timeout=120)
                text = run.stdout.decode("utf-8", "replace") + run.stderr.decode("utf-8", "replace")
                text = text.replace("\r\n", "\n")
                (output / (name + ".txt")).write_text(text, encoding="utf-8", newline="\n")
                if run.returncode:
                    # Hosted runners must expose the failure, not only a local log path.
                    print(text, flush=True)
                result = {"name": name, "status": "PASS" if run.returncode == 0 else "FAIL", "exit_code": run.returncode,
                          "seconds": round(time.monotonic() - started, 3), "log": name + ".txt"}
            except (OSError, subprocess.TimeoutExpired) as exc:
                result = {"name": name, "status": "FAIL", "reason": type(exc).__name__}
        print(f"{result['name']}: {result['status']}", flush=True)
        results.append(result)
    failures = any(r["status"] == "FAIL" for r in results)
    missing = any(r["status"] == "NOT_RUN" for r in results)
    report = {"generated_at": datetime.now(timezone.utc).isoformat(), "product": "nfcraft",
              "python": platform.python_version(), "platform": platform.platform(),
              "overall": "FAIL" if failures else "INCOMPLETE" if missing else "PASS",
              "scope": "hardware-free local checks; not reader/phone/Windows-package/cloud qualification",
              "checks": results, "not_run": ["physical NFC", "phone/printed QR", "desktop/tray packaging", "Cloudflare deployment"]}
    (output / "summary.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Evidence:", output)
    return 1 if failures else 2 if missing and args.require_node else 0


if __name__ == "__main__":
    raise SystemExit(main())
