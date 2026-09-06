"""Deliberately narrow NFC Forum Type 2, single HTTPS URI encoder.

NTAG215 has 504 user bytes; factory CC advertises 496 NDEF-area bytes.
This product intentionally caps URLs to 200 ASCII bytes. No arbitrary TLVs,
external records, vCards or security-page writes are accepted.
"""
from __future__ import annotations
import ipaddress
import re
from urllib.parse import urlsplit
from .errors import OpsError

CC = bytes.fromhex("E1 10 3E 00")
VERSION = bytes.fromhex("00 04 04 02 01 00 11 03")
NDEF_CAPACITY = 496
FIRST_PAGE = 4
LAST_NDEF_PAGE = 127
MAX_URL_BYTES = 200


def validate_https(url: str, *, production: bool = False) -> str:
    if not isinstance(url, str) or not url.isascii() or any(ord(c) < 33 or ord(c) == 127 for c in url):
        raise OpsError("INVALID_URL", "Use an ASCII HTTPS URL; encode Unicode with IDNA / percent escapes.")
    if len(url.encode("ascii")) > MAX_URL_BYTES or "\\" in url:
        raise OpsError("INVALID_URL", "URL is too long (maximum 200 bytes) or contains a backslash.")
    try:
        p = urlsplit(url)
        port = p.port
    except ValueError as exc:
        raise OpsError("INVALID_URL", "Malformed URL.") from exc
    if p.scheme != "https" or not url.startswith("https://") or not p.hostname or p.username or p.password or p.fragment:
        raise OpsError("INVALID_URL", "An HTTPS URL without credentials or fragment is required.")
    host = p.hostname.lower()
    if len(host)>253 or not all(re.fullmatch(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?", label) for label in host.split(".")):
        raise OpsError("INVALID_URL", "Use a valid ASCII DNS hostname.")
    if production:
        reserved = ("example.com", "example.net", "example.org", "localhost")
        if any(host == h or host.endswith("." + h) for h in reserved) or host.endswith((".test", ".invalid", ".localhost", ".local")) or "." not in host:
            raise OpsError("PLACEHOLDER_DOMAIN", "Real cards require your own public hostname, not a demo/local domain.")
        try:
            ipaddress.ip_address(host)
        except ValueError:
            pass
        else:
            raise OpsError("INVALID_URL", "Use a public DNS hostname, not an IP address.")
        if port not in (None, 443):
            raise OpsError("INVALID_URL", "Production routes must use standard HTTPS port 443.")
    return url


def validate_base(base: str, *, production: bool = False) -> str:
    if not isinstance(base, str):
        raise OpsError("INVALID_BASE", "The route base must be a string.")
    base = validate_https(base.rstrip("/"), production=production)
    p = urlsplit(base)
    if p.query or p.path not in ("", "/"):
        raise OpsError("INVALID_BASE", "The route base must be an HTTPS origin with no path or query.")
    # Reserve room for '/c/' + 22-character 128-bit identifier.
    validate_https(base + "/c/" + "A" * 22, production=production)
    return base


def uri_record(url: str) -> bytes:
    validate_https(url)
    payload = b"\x04" + url[8:].encode("ascii")  # NFC URI prefix 04 = https://
    return bytes((0xD1, 1, len(payload), 0x55)) + payload


def encode_area(url: str) -> bytes:
    record = uri_record(url)
    if len(record) >= 255:
        raise OpsError("TOO_LARGE", "Only short NDEF TLVs are supported.")
    area = b"\x03" + bytes((len(record),)) + record + b"\xfe"
    padded = area + b"\x00" * (-len(area) % 4)
    if len(padded) > NDEF_CAPACITY:
        raise OpsError("TOO_LARGE", "Payload exceeds the NTAG215 CC-advertised area.")
    return padded


def decode_area(area: bytes) -> str | None:
    """Strictly decode our own canonical record; do not interpret arbitrary tag data."""
    if len(area) < 8 or area[0] != 3 or area[1] == 0:
        return None
    n = area[1]
    r = area[2:2+n]
    if len(r) != n or len(r) < 5 or r[:2] != b"\xd1\x01" or r[3:5] != b"U\x04" or r[2] != len(r)-4:
        return None
    if len(area) <= n+2 or area[n+2] != 0xFE:
        return None
    try:
        return validate_https("https://" + r[5:].decode("ascii"))
    except (UnicodeError, OpsError):
        return None


def is_empty(area: bytes) -> bool:
    # Factory NTAG215 initialized empty TLV, or all-zero unpopulated user area.
    return len(area) == NDEF_CAPACITY and (not any(area) or area[:3] == b"\x03\x00\xfe")


def write_plan(url: str) -> list[tuple[int, bytes]]:
    target = encode_area(url)
    # Expose an empty message first; make message length visible only after body.
    # This reduces partially advertised records; it does NOT make EEPROM atomic.
    staged = bytes((target[0], 0, target[2], target[3]))
    steps = [(4, staged)]
    steps.extend((4 + i//4, target[i:i+4]) for i in range(4, len(target), 4))
    steps.append((4, target[:4]))
    return steps


def assert_safe_page(page: int, data: bytes) -> None:
    if type(page) is not int or not FIRST_PAGE <= page <= LAST_NDEF_PAGE or len(data) != 4:
        raise OpsError("FORBIDDEN_PAGE", "Writes are restricted to four-byte NDEF pages 0x04..0x7F.")


def recovery_matches(current: bytes, original: bytes, target: bytes) -> bool:
    """Allow only whole pages attributable to the recorded interrupted operation.
    Torn/foreign pages do not pass this check; require separate manual diagnosis.
    """
    if len(current) != NDEF_CAPACITY or len(original) != NDEF_CAPACITY:
        return False
    stage = bytes((3, 0, target[2], target[3]))
    for i in range(0, len(target), 4):
        options = [original[i:i+4], target[i:i+4]]
        if i == 0:
            options.append(stage)
        if current[i:i+4] not in options:
            return False
    return current[len(target):] == original[len(target):]
