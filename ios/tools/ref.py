"""Print nfcraft/ndef.py's output for ios/tools/check.sh to diff against the Swift encoder.

Usage: python ios/tools/ref.py ios/tools/parity-cases.json
NFCRAFT_ROOT selects the checkout holding nfcraft/ndef.py (default: two levels up).
"""
import json
import os
import sys

sys.path.insert(0, os.environ.get(
    "NFCRAFT_ROOT",
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")),
))
from nfcraft.ndef import encode_area, write_plan, decode_area, is_empty, validate_https, NDEF_CAPACITY
from nfcraft.errors import OpsError

# Windows would otherwise write CRLF, and every line would differ from Swift's.
sys.stdout.reconfigure(newline=chr(10))


def rejected(url):
    try:
        validate_https(url)
        return "false"
    except OpsError:
        return "true"


def hides(area, planned):
    return "true" if area[:3] == b"\x03\x00\xfe" and any(area[3:planned]) else "false"


def flag(value):
    return "true" if value else "false"


with open(sys.argv[1], encoding="utf-8") as handle:
    cases = json.load(handle)

for url in cases["urls"]:
    print("URL " + url)
    try:
        validate_https(url)
        print("  validate null")
    except OpsError as exc:
        print("  validate " + str(exc))
    area = encode_area(url)
    print("  area " + area.hex().upper())
    print("  plan " + " ".join("%02X:%s" % (p, d.hex().upper()) for p, d in write_plan(url)))
    full = area + b"\x00" * (NDEF_CAPACITY - len(area))
    print("  decode " + str(decode_area(full)))
    print("  empty " + flag(is_empty(full)))

for i, url in enumerate(cases["bad"]):
    print("BAD[%d] rejected %s" % (i, rejected(url)))
for i, url in enumerate(cases["edge"]):
    print("EDGE[%d] rejected %s" % (i, rejected(url)))

blank = bytearray(NDEF_CAPACITY)
print("blank empty " + flag(is_empty(bytes(blank))))
blank[0:3] = b"\x03\x00\xfe"
print("emptytlv empty " + flag(is_empty(bytes(blank))))
print("emptytlv hides " + hides(bytes(blank), 24))
blank[9] = 0x41
print("emptytlv+data empty " + flag(is_empty(bytes(blank))))
print("emptytlv+data hides " + hides(bytes(blank), 24))
print("emptytlv+data hides(short) " + hides(bytes(blank), 8))
