"""Optional native tray shell. Core remains usable without these dependencies."""
import threading
import webbrowser
from .errors import OpsError


def start_tray(server, engine):
    try:
        import pystray
        from PIL import Image, ImageDraw
    except ImportError as exc:
        raise OpsError("DESKTOP_DEPENDENCY_MISSING", "Install the [desktop] extra for tray mode.") from exc
    image = Image.new("RGBA", (64,64), (0,0,0,0))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((6,10,58,54), radius=10, fill=(30,64,58))
    draw.arc((20,19,47,48), -75,75, fill="white", width=3)
    draw.arc((18,25,36,43), -75,75, fill="white", width=3)
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
