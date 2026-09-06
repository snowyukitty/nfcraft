"""Inspect first; copy only with --apply and explicit confirmation."""
from pathlib import Path
import argparse
import json
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from nfcraft.migration import import_workspace
from nfcraft.errors import OpsError


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source-root", required=True, type=Path)
    p.add_argument("--destination-root", required=True, type=Path)
    p.add_argument("--mode", required=True, choices=("demo", "hardware"))
    p.add_argument("--apply", action="store_true")
    p.add_argument("--confirm", default="")
    a = p.parse_args(argv)
    try:
        result = import_workspace(a.source_root, a.destination_root, a.mode, apply=a.apply, confirmation=a.confirm)
    except (OpsError, OSError) as exc:
        print(json.dumps({"error": exc.as_dict() if isinstance(exc, OpsError) else str(exc)}), file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
