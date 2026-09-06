"""Portable exports; never include UID in the public route manifest."""
from __future__ import annotations
import csv
import io
import json
from .errors import OpsError
from .manifest import validate_manifest


def inventory_csv(cards):
    out = io.StringIO(newline="")
    fields = ["id","batch_name","ordinal","uid","url","status","route_state","last_error"]
    writer = csv.DictWriter(out, fieldnames=fields, extrasaction="ignore")
    writer.writeheader()
    for card in cards:
        row = {}
        for field in fields:
            value = str(card.get(field) or "")
            row[field] = "'" + value if value.startswith(("=","+","-","@","\t","\r","\n")) else value
        writer.writerow(row)
    return out.getvalue()


def qr_svg(url):
    try:
        import qrcode
        from qrcode.image.svg import SvgPathImage
    except ImportError as exc:
        raise OpsError("QR_DEPENDENCY_MISSING", "Install the [qr] extra to generate QR SVG files.") from exc
    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M, border=4)
    qr.add_data(url)
    qr.make(fit=True)
    output = io.BytesIO()
    qr.make_image(image_factory=SvgPathImage).save(output)
    return output.getvalue()


def sql_quote(value):
    return "'" + str(value).replace("'", "''") + "'"


def manifest_sql(manifest, *, allow_demo=False):
    validate_manifest(manifest, allow_demo=allow_demo)
    lines = ["-- Generated route migration. Review before executing. No UIDs are included."]
    for p in manifest["profiles"]:
        body = json.dumps(p, ensure_ascii=False)
        lines.append("INSERT INTO profiles(id,body,revision) VALUES(" + ",".join((sql_quote(p["id"]),sql_quote(body),str(int(p["revision"])))) + ") ON CONFLICT(id) DO UPDATE SET body=excluded.body,revision=excluded.revision WHERE excluded.revision>=profiles.revision;")
    for r in manifest["routes"]:
        vals = (sql_quote(r["slug"]),sql_quote(r["profile_id"]),sql_quote(r["state"]),str(int(r["revision"])))
        lines.append("INSERT INTO routes(slug,profile_id,state,revision) VALUES(" + ",".join(vals) + ") ON CONFLICT(slug) DO UPDATE SET profile_id=excluded.profile_id,state=excluded.state,revision=excluded.revision WHERE excluded.revision>=routes.revision;")
    return "\n".join(lines) + "\n"
