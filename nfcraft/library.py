"""Shared inventory selection and public export review. Never contacts a cloud."""
from urllib.parse import urlsplit
from .errors import OpsError
from .manifest import validate_manifest


def normalize_filters(value=None):
    value = {} if value is None else value
    if not isinstance(value, dict) or set(value) - {"q", "batch", "status", "route"}:
        raise OpsError("INVALID_FILTER", "Use search, batch, write status and route intent filters only.")
    result = {key: value.get(key, "") for key in ("q", "batch", "status", "route")}
    if any(not isinstance(v, str) or len(v) > 200 or any(ord(c) < 32 for c in v) for v in result.values()):
        raise OpsError("INVALID_FILTER", "Filter text must be at most 200 characters without control characters.")
    if result["status"] not in ("", "verified", "quarantined", "reserved", "writing", "verifying"):
        raise OpsError("INVALID_FILTER", "Unknown write status.")
    if result["route"] not in ("", "enabled", "suspended"):
        raise OpsError("INVALID_FILTER", "Unknown route intent.")
    result["q"] = result["q"].strip()
    return result


def select_cards(cards, filters=None):
    filters = normalize_filters(filters)
    query = filters["q"].casefold()
    def matches(card):
        if any(filters[key] and filters[key] != card[field] for key, field in
               (("batch", "batch_id"), ("status", "status"), ("route", "route_state"))):
            return False
        label = f"{card['batch_name']} / {card['ordinal']:04d}"
        haystack = " ".join(str(card.get(key) or "") for key in ("id", "uid", "slug", "url", "last_error"))
        return not query or query in (label + " " + haystack).casefold()
    return [card for card in cards if matches(card)]


def inventory_page(store, filters=None, offset=0, limit=50):
    if type(offset) is not int or offset < 0 or type(limit) is not int or not 1 <= limit <= 100:
        raise OpsError("INVALID_PAGE", "Use a nonnegative offset and 1–100 rows per page.")
    all_cards = store.inventory()
    selected = select_cards(all_cards, filters)
    # Keep a disappearing last page usable after filtering or a state change.
    offset = min(offset, max(0, (len(selected) - 1) // limit * limit))
    return {"cards": selected[offset:offset + limit], "total": len(all_cards), "matched": len(selected),
            "exportable": sum(c["status"] == "verified" for c in selected), "offset": offset, "limit": limit}


def publication_review(store, filters=None):
    filters = normalize_filters(filters)
    cards = select_cards(store.inventory(), filters)
    manifest = store.manifest(cards=cards)
    validate_manifest(manifest, allow_demo=True)
    origins = sorted({f"{urlsplit(r['url']).scheme}://{urlsplit(r['url']).netloc}" for r in manifest["routes"]})
    included = {r["slug"] for r in manifest["routes"]}
    profiles = {p["id"] for p in manifest["profiles"]}
    shared = sum(r["slug"] not in included and r["profile_id"] in profiles for r in store.manifest()["routes"])
    return {"filters": filters, "manifest": manifest, "origins": origins,
            "other_local_routes_sharing_profiles": shared,
            "matched": len(cards), "excluded": sum(c["status"] != "verified" for c in cards),
            "enabled": sum(r["state"] == "enabled" for r in manifest["routes"]),
            "suspended": sum(r["state"] == "suspended" for r in manifest["routes"]),
            "publication": "Not checked. Exporting does not deploy or verify a public URL."}
