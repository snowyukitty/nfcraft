"""Exercise the real pywebview window and orderly close on disposable demo data."""
import contextlib
import io
import json
from pathlib import Path
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import webview
from nfcraft.__main__ import main
from nfcraft.runtime import WorkspaceLock


def smoke():
    real_start = webview.start
    checks = []
    failure = []

    def inspect_and_close():
        window = webview.windows[0]
        try:
            deadline = time.monotonic() + 25
            while time.monotonic() < deadline:
                text = window.evaluate_js("document.querySelector('#connection')?.textContent")
                if text and "Connected locally" in text:
                    break
                time.sleep(0.2)
            else:
                raise AssertionError("Native window did not connect to the demo app")
            assert window.evaluate_js("document.querySelector('#mode-title').textContent") == "Simulation workspace"
            assert window.evaluate_js("location.hash") == ""
            checks.extend(["native WebView2 loads authenticated demo UI", "operator fragment removed"])
        except Exception as exc:
            failure.append(type(exc).__name__)
        finally:
            window.destroy()

    def start(*args, **kwargs):
        return real_start(inspect_and_close, *args, **kwargs)

    with tempfile.TemporaryDirectory(prefix="nfcraft desktop 測試 ") as directory:
        webview.start = start
        try:
            # Do not persist or emit the synthetic operator URL from app startup.
            with contextlib.redirect_stdout(io.StringIO()):
                code = main(["--desktop", "--mode", "demo", "--data-dir", directory, "--port", "0"])
            assert code == 0 and not failure, failure
            workspace = Path(directory) / "demo"
            assert not (workspace / "agent-runtime.json").exists()
            lock = WorkspaceLock(workspace)
            lock.close()
            checks.append("window close stops server and releases runtime/lock")
        finally:
            webview.start = real_start
    print(json.dumps({"result": "PASS", "scope": "source native desktop, disposable demo", "checks": checks,
                      "packaged_desktop": "NOT_RUN", "tray_menu": "NOT_RUN"}, indent=2))


if __name__ == "__main__":
    smoke()
