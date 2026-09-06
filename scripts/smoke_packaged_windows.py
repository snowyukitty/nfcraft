"""Launch/close the packaged native window via its own Win32 window handle.

No desktop-wide input, screenshots, owner workspace, or hardware access.
"""
import ctypes
from ctypes import wintypes
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from nfcraft.cli import Client
from nfcraft.runtime import WorkspaceLock


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    if os.name != "nt":
        raise SystemExit("NOT_RUN: Windows required")
    evidence = ROOT / ".local/evidence"
    evidence.mkdir(parents=True, exist_ok=True)
    root = Path(tempfile.mkdtemp(prefix="native package 測試 ", dir=evidence))
    package = root / "portable app"
    shutil.copytree(ROOT / "dist/nfcraft", package)
    user32 = ctypes.WinDLL("user32", use_last_error=True)
    user32.PostMessageW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
    user32.PostMessageW.restype = wintypes.BOOL
    callback_type = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    user32.EnumWindows.argtypes = [callback_type, wintypes.LPARAM]
    user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
    user32.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]

    def app_window(pid):
        found = []
        @callback_type
        def visit(handle, _):
            owner = wintypes.DWORD()
            user32.GetWindowThreadProcessId(handle, ctypes.byref(owner))
            if owner.value == pid:
                title = ctypes.create_unicode_buffer(128)
                user32.GetWindowTextW(handle, title, 128)
                if title.value == "nfcraft":
                    found.append(handle)
            return True
        user32.EnumWindows(visit, 0)
        return found[0] if found else None

    checks = []
    for run in range(2):
        with (root / f"native-{run}.stderr").open("wb") as log:
            proc = subprocess.Popen([str(package / "nfcraft.exe"), "--desktop", "--tray", "--mode", "demo",
                    "--data-dir", str(root / "workspace"), "--port", "0"], cwd=package,
                    stdout=subprocess.DEVNULL, stderr=log, creationflags=subprocess.CREATE_NO_WINDOW)
            try:
                deadline = time.monotonic() + 30
                handle = None
                while time.monotonic() < deadline and proc.poll() is None:
                    handle = app_window(proc.pid)
                    if handle and (root / "workspace/demo/agent-runtime.json").exists():
                        break
                    time.sleep(0.2)
                assert handle and proc.poll() is None, "Packaged native window failed to open"
                # Allow asynchronous WebView2 creation before sending native close.
                # DOM/render acceptance is separately covered by smoke_desktop/browser.
                time.sleep(3)
                client = Client(root=root / "workspace")
                state = client.call("/api/state")
                assert state["mode"] == "demo" and state["armed"] is None
                if run == 0:
                    client.call("/api/batches", {"name": "Portable draft", "target": 1, "base": "https://tap.example.com"})
                else:
                    assert len(state["batches"]) == 1 and state["cards"] == []
                # Only this child app's known window receives WM_CLOSE.
                assert user32.PostMessageW(handle, 0x0010, 0, 0)
                assert proc.wait(timeout=15) == 0
                assert not (root / "workspace/demo/agent-runtime.json").exists()
                lock = WorkspaceLock(root / "workspace/demo")
                lock.close()
                checks.append("native desktop/tray starts and closes cleanly" if run == 0 else "restart preserves draft without arming")
            finally:
                if proc.poll() is None:
                    subprocess.run(["taskkill", "/PID", str(proc.pid), "/T", "/F"], capture_output=True, timeout=10)
                    proc.wait(timeout=5)
        diagnostics = (root / f"native-{run}.stderr").read_text(encoding="utf-8", errors="replace")
        assert "failed" not in diagnostics.lower(), "Native runtime reported an initialization/shutdown failure"
    summary = {"result": "PASS", "scope": "unsigned packaged Windows desktop/tray; disposable mock data",
               "checks": checks, "tray_menu_visual_qa": "NOT_RUN", "clean_machine": "NOT_RUN", "physical_nfc": "NOT_RUN"}
    (root / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    print("Evidence:", root.relative_to(ROOT))


if __name__ == "__main__":
    main()
