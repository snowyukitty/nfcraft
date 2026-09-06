from __future__ import annotations
import argparse
import json
import os
import sys
import threading
import webbrowser
from pathlib import Path
from . import __version__
from .runtime import workspace, WorkspaceLock
from .store import Store
from .engine import Engine
from .server import LocalServer
from .errors import OpsError


def parser():
    p = argparse.ArgumentParser(description="nfcraft — local NTAG215 workbench")
    p.add_argument("--version", action="version", version="nfcraft " + __version__)
    p.add_argument("--mode", choices=("demo","hardware"), default="demo")
    p.add_argument("--data-dir", help="Workspace root; separate demo/hardware subfolders are always used")
    p.add_argument("--port", type=int, default=47821)
    p.add_argument("--reader", help="Exact ACR1552U PICC reader name")
    p.add_argument("--allow-experimental-hardware-writes", action="store_true")
    p.add_argument("--no-browser", action="store_true")
    p.add_argument("--desktop", action="store_true", help="Use optional pywebview window")
    p.add_argument("--tray", action="store_true", help="Use optional tray controls; Windows target")
    return p


def main(argv=None, *, on_error=None):
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    args = parser().parse_args(argv)
    if not 0 <= args.port <= 65535:
        raise SystemExit("Invalid port.")
    try:
        directory = workspace(args.mode, args.data_dir)
    except OpsError as exc:
        if on_error:
            on_error(exc.as_dict())
        print(json.dumps({"error": exc.as_dict()}), file=sys.stderr)
        return 2
    lock = None
    engine = None
    server = None
    server_thread = None
    runtime_path = directory / "agent-runtime.json"
    tray = None
    try:
        lock = WorkspaceLock(directory)
        if args.mode == "demo":
            from .adapters.mock import MockReader
            reader = MockReader(directory / "virtual-tags")
        else:
            from .adapters.pcsc import Acs1552Reader, list_readers
            available = list_readers()
            if not args.reader or args.reader not in available:
                print(json.dumps({"readers":available,"next":"Restart with --reader EXACT_NAME. Read-only is the default."}, indent=2))
                return 2
            reader = Acs1552Reader(args.reader, args.allow_experimental_hardware_writes)
        store = Store(directory / "journal.sqlite3", args.mode)
        engine = Engine(store, reader)
        server = LocalServer(engine, directory, args.port)
        # Agent credential has no arming, raw-write, profile-edit or lock privilege.
        fd = os.open(runtime_path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump({"origin":server.origin,"token":server.agent_token,"mode":args.mode}, f)
        engine.start_worker()
        server_thread = threading.Thread(target=server.serve_forever, name="local-api", daemon=True)
        server_thread.start()
        print(f"nfcraft {__version__} | {args.mode.upper()} | workspace: {directory}", flush=True)
        print(f"Operator app: {server.operator_url}", flush=True)
        print("Keep this operator URL private. Ctrl+C stops the workstation.", flush=True)
        if args.tray:
            from .desktop import start_tray
            tray = start_tray(server, engine)
        if args.desktop:
            try:
                import webview
            except ImportError:
                print("Desktop extra not installed; opening the browser app instead.", file=sys.stderr)
                webbrowser.open(server.operator_url)
            else:
                webview.create_window("nfcraft", server.operator_url, width=1320, height=920, min_size=(960,700))
                webview.start(icon=str(Path(__file__).parent / "web/icons/build/icon.ico"))
                return 0
        elif not args.no_browser:
            webbrowser.open(server.operator_url)
        while not engine.stop.wait(0.5):
            pass
    except KeyboardInterrupt:
        pass
    except OpsError as exc:
        if on_error:
            on_error(exc.as_dict())
        print(json.dumps({"error":exc.as_dict()}), file=sys.stderr)
        return 2
    except OSError as exc:
        if on_error:
            on_error({"code": "STARTUP_IO", "message": "Could not start nfcraft. Another copy may already be running, or the workspace/port may be unavailable. Close the existing app before retrying."})
        print(json.dumps({"error":{"code":"STARTUP_IO", "message":"Could not start the local workstation. Check the workspace and whether its port is already in use.", "detail":str(exc)}}), file=sys.stderr)
        return 2
    finally:
        if tray:
            tray.stop()
        if server:
            # shutdown() waits forever if serve_forever() never started.
            if server_thread is not None and server_thread.is_alive():
                server.shutdown()
                server_thread.join(timeout=5)
            server.server_close()
        if engine:
            engine.shutdown()
        if lock:
            if runtime_path.exists():
                runtime_path.unlink()
            lock.close()
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
