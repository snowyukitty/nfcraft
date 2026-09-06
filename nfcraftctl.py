"""Agent-safe CLI. nfcctl.py remains a compatibility alias."""
from nfcraft.cli import main
if __name__ == "__main__":
    raise SystemExit(main())
