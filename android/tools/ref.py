"""Print nfcraft/ndef.py's output for tools/parity.sh to diff against the Java encoder."""
import os
import sys

# The Python reference lives two directories up, at the repository root,
# unless NFCRAFT_ROOT points somewhere else.
sys.path.insert(0, os.environ.get(
    "NFCRAFT_ROOT",
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")),
))
from nfcraft.ndef import encode_area, write_plan, decode_area, is_empty, validate_https, NDEF_CAPACITY
from nfcraft.errors import OpsError

URLS = [
    "https://tgs.best",
    "https://tgs.best/",
    "https://tap.example.com/c/AAAAAAAAAAAAAAAAAAAAAA",
    "https://a.co/x?y=1",
    "https://" + "a" * 60 + ".example.com/" + "b" * 100,
]
BAD = [
    "http://tgs.best",
    "https://",
    "https://tgs.best#f",
    "https://user:pw@tgs.best",
    "https://-bad.example.com",
    "https://tgs.best" + chr(92) + "x",
    "https://" + "a" * 200,
    "https://\u00e6.example.com",
]


def problem(url):
    try:
        validate_https(url)
        return None
    except OpsError as exc:
        return str(exc)


def hides(area, planned):
    return area[:3] == b"\x03\x00\xfe" and any(area[3:planned])


for url in URLS:
    print("URL " + url)
    print("  validate " + ("null" if problem(url) is None else problem(url)))
    area = encode_area(url)
    print("  area " + area.hex().upper())
    print("  plan " + " ".join("%02X:%s" % (p, d.hex().upper()) for p, d in write_plan(url)))
    full = area + b"\x00" * (NDEF_CAPACITY - len(area))
    print("  decode " + str(decode_area(full)))
    print("  empty " + ("true" if is_empty(full) else "false"))

# Indexed, not echoed: one case is deliberately non-ASCII and a console
# encoding must not show up as an encoder difference.
for i, url in enumerate(BAD):
    print("BAD[%d] rejected %s" % (i, "true" if problem(url) is not None else "false"))

blank = bytearray(NDEF_CAPACITY)
print("blank empty " + ("true" if is_empty(bytes(blank)) else "false"))
blank[0:3] = b"\x03\x00\xfe"
print("emptytlv empty " + ("true" if is_empty(bytes(blank)) else "false"))
print("emptytlv hides " + ("true" if hides(bytes(blank), 24) else "false"))
blank[9] = 0x41
print("emptytlv+data empty " + ("true" if is_empty(bytes(blank)) else "false"))
print("emptytlv+data hides " + ("true" if hides(bytes(blank), 24) else "false"))
print("emptytlv+data hides(short) " + ("true" if hides(bytes(blank), 8) else "false"))
