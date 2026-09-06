"""Windowed entrypoint with visible, capability-free startup errors."""
from contextlib import redirect_stderr, redirect_stdout
import os
import sys

from .__main__ import main as run_workstation


def show_startup_error(message):
    import ctypes
    ctypes.windll.user32.MessageBoxW(None, message, "nfcraft - Unable to start", 0x10010)


def main(argv=None, *, show_error=None):
    show_error = show_error or show_startup_error
    arguments = list(sys.argv[1:] if argv is None else argv)
    if "--desktop" not in arguments:
        arguments.append("--desktop")
    if "--tray" not in arguments:
        arguments.append("--tray")
    errors = []
    try:
        # Windowed executables have no console. Never persist the operator URL
        # or raw third-party output just to make startup diagnostics available.
        with open(os.devnull, "w", encoding="utf-8") as sink:
            with redirect_stdout(sink), redirect_stderr(sink):
                result = run_workstation(arguments, on_error=errors.append)
    except SystemExit as exc:
        result = exc.code if isinstance(exc.code, int) else 2
    except Exception as exc:
        result = 2
        errors.append({"code": type(exc).__name__, "message": "The desktop could not initialize. Check the complete app folder and WebView2 installation."})
    if result:
        error = errors[-1] if errors else {"code": "STARTUP_FAILED", "message": "The app could not start. Check startup arguments and desktop dependencies."}
        show_error(f"{error['message']}\n\nCode: {error['code']}\n\nYour existing card data has not been reset.")
    return result


if __name__ == "__main__":
    raise SystemExit(main())
