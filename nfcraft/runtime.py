from __future__ import annotations
import os
from pathlib import Path
from .errors import OpsError


def default_root() -> Path:
    return Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "nfcraft"


def legacy_root() -> Path:
    return Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "NfcCardOps"


def workspace(mode="demo", root=None):
    if mode not in ("demo", "hardware"):
        raise OpsError("INVALID_MODE", "Workspace mode must be demo or hardware.")
    if root:
        return Path(root).expanduser().resolve() / mode
    destination = default_root() / mode
    previous = legacy_root() / mode
    if (previous / "journal.sqlite3").exists() and not (destination / "journal.sqlite3").exists():
        raise OpsError("LEGACY_WORKSPACE_FOUND", (
            f"Existing NFC Card Ops data found at {previous}. Stop the old app and follow "
            "docs/MIGRATION.md before using nfcraft. No new empty journal was created. "
            "An explicit --data-dir can select the original root without moving its data."
        ))
    return destination


class WorkspaceLock:
    """OS-held lock prevents two daemon processes from sharing a writer journal."""
    def __init__(self, directory: Path):
        directory.mkdir(parents=True, exist_ok=True, mode=0o700)
        if os.name != "nt":
            directory.chmod(0o700)
        self.file = open(directory / "writer.lock", "a+b")
        try:
            # Windows byte-range locks also deny reads by a second process.
            # Inspect size without touching the locked byte and close on failure.
            if os.fstat(self.file.fileno()).st_size == 0:
                self.file.write(b"0")
                self.file.flush()
            self.file.seek(0)
            if os.name == "nt":
                import msvcrt
                msvcrt.locking(self.file.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(self.file, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            self.file.close()
            raise OpsError("WORKSPACE_BUSY", "Another daemon owns this workspace. Connect to it; do not start a second writer.") from exc

    def close(self):
        self.file.close()
