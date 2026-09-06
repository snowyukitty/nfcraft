"""Validate an export and generate SQL for human review; never deploys it."""
from pathlib import Path
import argparse
import json
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from nfcraft.exporting import manifest_sql
from nfcraft.errors import OpsError


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("manifest", type=Path)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--allow-demo", action="store_true", help="Local/disposable preview testing only")
    a = p.parse_args(argv)
    try:
        if a.manifest.resolve() == a.output.resolve():
            raise OpsError("OUTPUT_OVERLAP", "The output must not replace its input manifest.")
        if a.manifest.stat().st_size > 16 * 1024 * 1024:
            raise OpsError("MANIFEST_TOO_LARGE", "Review exports in files smaller than 16 MiB.")
        value = json.loads(a.manifest.read_text(encoding="utf-8-sig"))
        sql = manifest_sql(value, allow_demo=a.allow_demo)
        # Exclusive creation prevents silent replacement of an already-reviewed migration.
        with a.output.open("x", encoding="utf-8", newline="\n") as f:
            f.write(sql)
    except (OpsError, OSError, ValueError, KeyError, TypeError) as exc:
        print(json.dumps({"error": exc.as_dict() if isinstance(exc, OpsError) else str(exc)}), file=sys.stderr)
        return 2
    print("Wrote reviewable SQL:", a.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
