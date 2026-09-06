"""Validate public exports before generating reviewable SQL.

The checksum catches accidental edits, not a malicious author who can recompute
it. Neither a checksum nor a `simulated: false` field proves a physical write.
"""
from __future__ import annotations
import hashlib
import hmac
import json
import re
from urllib.parse import urlsplit
from .errors import OpsError
from .ndef import validate_https


def validate_manifest(value, *, allow_demo=False):
    def reject(message):
        raise OpsError("INVALID_MANIFEST", message)
    if not isinstance(value, dict):
        reject("Manifest must be an object.")
    if type(value.get("schema")) is not int or value["schema"] != 1:
        raise OpsError("MANIFEST_VERSION", "Unsupported manifest version.")
    if set(value) != {"schema", "simulated", "profiles", "routes", "sha256", "generated_at"}:
        reject("Manifest fields do not match the public schema.")
    if type(value["simulated"]) is not bool:
        reject("The simulation marker must be an explicit boolean.")
    if value["simulated"] and not allow_demo:
        raise OpsError("DEMO_PUBLICATION_BLOCKED", "Refusing a simulated manifest. --allow-demo is for disposable local/preview data only.")
    if not isinstance(value["generated_at"], str) or len(value["generated_at"]) > 80:
        reject("Invalid export timestamp.")
    digest = value["sha256"]
    if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
        reject("Missing or malformed export checksum.")
    body = {k: value[k] for k in ("schema", "simulated", "profiles", "routes")}
    try:
        actual = hashlib.sha256(json.dumps(body, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode()).hexdigest()
    except (TypeError, ValueError, UnicodeError):
        reject("Manifest contains invalid JSON values.")
    if not hmac.compare_digest(actual, digest):
        raise OpsError("MANIFEST_CHECKSUM", "Export content changed. Re-export the intended data instead of editing the checksum.")
    profiles, routes = value["profiles"], value["routes"]
    if not isinstance(profiles, list) or not 1 <= len(profiles) <= 1000:
        reject("Expected 1–1000 public profiles.")
    if not isinstance(routes, list) or len(routes) > 100000:
        reject("Invalid or oversized route list.")
    ids, slugs = set(), set()
    for p in profiles:
        fields = {"id", "name", "headline", "bio", "email", "website", "revision"}
        if not isinstance(p, dict) or set(p) != fields:
            reject("Unexpected profile fields; private fields must not be exported.")
        if not isinstance(p["id"], str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,80}", p["id"]) or p["id"] in ids:
            reject("Invalid or duplicate profile ID.")
        ids.add(p["id"])
        if type(p["revision"]) is not int or not 1 <= p["revision"] <= 2147483647:
            reject("Profile revision must be a positive integer.")
        for name in ("name", "headline", "bio", "email", "website"):
            if not isinstance(p[name], str) or len(p[name]) > (1200 if name == "bio" else 160):
                reject("Invalid profile text.")
            if any(ord(c) < 32 and c != "\n" for c in p[name]):
                reject("Control characters in profile text.")
        if not p["name"].strip() or any(c in p["email"] for c in "\r\n"):
            reject("Invalid display name or email.")
        if p["website"]:
            validate_https(p["website"])
    for r in routes:
        if not isinstance(r, dict) or set(r) != {"slug", "url", "state", "revision", "profile_id"}:
            reject("Unexpected route fields; raw UIDs must not be exported.")
        if not isinstance(r["slug"], str) or not re.fullmatch(r"[A-Za-z0-9_-]{22}", r["slug"]) or r["slug"] in slugs:
            reject("Invalid or duplicate route slug.")
        slugs.add(r["slug"])
        if not isinstance(r["profile_id"], str) or r["profile_id"] not in ids:
            reject("Route refers to a missing profile.")
        if r["state"] not in ("enabled", "suspended") or type(r["revision"]) is not int or not 1 <= r["revision"] <= 2147483647:
            reject("Invalid route state or revision.")
        validate_https(r["url"], production=not value["simulated"])
        u = urlsplit(r["url"])
        if u.path != "/c/" + r["slug"] or u.query or u.fragment:
            reject("Route URL does not match its slug.")
    return value
