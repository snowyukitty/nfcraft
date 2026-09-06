"""Read-only development preflight: no driver install, network, or NFC commands."""
import json
import os
from pathlib import Path
import platform
import shutil
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from nfcraft import __version__
from nfcraft.runtime import default_root, legacy_root

report = {
    "product": "nfcraft", "version": __version__,
    "python": platform.python_version(), "python_executable": sys.executable,
    "python_ok": sys.version_info >= (3, 11), "os": platform.system(),
    "wsl_detected": "microsoft" in platform.release().lower() or bool(os.environ.get("WSL_DISTRO_NAME")),
    "tools": {name: shutil.which(name) for name in ("git", "node", "npm")},
    "default_data_root": str(default_root()),
    "legacy_modes_found": [mode for mode in ("demo", "hardware") if (legacy_root() / mode / "journal.sqlite3").is_file()],
    "reader_accessed": False,
    "next": "Read AGENTS.md. Run scripts/verify.py. Use Windows-native Python for a Windows-owned PC/SC reader."
}
print(json.dumps(report, ensure_ascii=False, indent=2))
raise SystemExit(0 if report["python_ok"] else 2)
