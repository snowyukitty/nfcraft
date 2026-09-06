"""Optional native tray shell. Core remains usable without these dependencies."""
import threading
import webbrowser
from pathlib import Path
from .errors import OpsError


def start_tray(server, engine):
    try:
        import pystray
        from PIL import Image
    except ImportError as exc:
        raise OpsError("DESKTOP_DEPENDENCY_MISSING", "Install the [desktop] extra for tray mode.") from exc
    with Image.open(Path(__file__).parent / "web/icons/tray/tray.png") as source:
        image = source.convert("RGBA")
    def open_app(*_): webbrowser.open(server.operator_url)
    def pause(*_): engine.pause()
    def stop(icon, _):
        engine.pause_requested.set()
        engine.stop.set()
        icon.stop()
    icon = pystray.Icon("nfcraft", image, "nfcraft · " + engine.store.mode,
                        pystray.Menu(pystray.MenuItem("Open workbench",open_app,default=True),
                                     pystray.MenuItem("Pause writes",pause),pystray.MenuItem("Quit",stop)))
    threading.Thread(target=icon.run, daemon=True).start()
    return icon
