"""Compatibility alias for nfcraftctl.py (v0.1 protocol surface)."""
from nfcraft.cli import main
if __name__ == "__main__":
    raise SystemExit(main())
