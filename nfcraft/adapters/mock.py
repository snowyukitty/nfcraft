"""Persistent virtual tags, including write-interruption injection. Never hardware."""
from __future__ import annotations
import json
import secrets
from pathlib import Path
from .base import Reader, Inspection
from ..ndef import VERSION, CC, NDEF_CAPACITY, encode_area, assert_safe_page
from ..errors import OpsError

class MockReader(Reader):
    simulated = True
    name = "Virtual NTAG215 · simulation"

    def __init__(self, directory: Path):
        self.directory = directory
        directory.mkdir(parents=True, exist_ok=True)
        self.uid = None
        self.card = None
        self.write_count = 0
        self.written_pages = []

    def insert(self, scenario="blank", uid=None):
        if self.uid:
            raise OpsError("REMOVE_FIRST", "Remove the current virtual card before presenting another.")
        if scenario not in ("blank", "foreign", "locked", "ntag213", "interrupted"):
            raise OpsError("INVALID_SCENARIO", "Unknown virtual-card scenario.")
        if uid is not None:
            if not isinstance(uid, str) or len(uid) != 14 or any(c not in "0123456789abcdef" for c in uid):
                raise OpsError("INVALID_UID", "Invalid virtual UID.")
            path = self.directory / (uid + ".json")
            if not path.is_file():
                raise OpsError("NOT_FOUND", "This virtual card was not created by this workspace.")
            self.card = json.loads(path.read_text())
        else:
            uid = "04" + secrets.token_hex(6)
            area = bytearray(NDEF_CAPACITY)
            area[:4] = b"\x03\x00\xfe\x00"
            if scenario == "foreign":
                payload = encode_area("https://example.net/not-owned-by-this-app")
                area[:len(payload)] = payload
            self.card = {"area": area.hex(), "version": VERSION.hex(), "cc": CC.hex(),
                         "static": "0000", "dynamic": "000000", "cfg0": "040000ff", "cfg1": "00000000",
                         "fail_after": 3 if scenario == "interrupted" else None}
            if scenario == "ntag213":
                self.card["version"] = "0004040201000f03"
            if scenario == "locked":
                self.card["static"] = "0001"
        self.uid = uid
        self.write_count = 0
        self.written_pages = []
        self._save()
        return uid

    def clear_fault(self):
        self._require()
        self.card["fail_after"] = None
        self._save()

    def remove(self):
        self.uid, self.card = None, None

    def _save(self):
        path = self.directory / (self.uid + ".json")
        temp = path.with_suffix(".tmp")
        temp.write_text(json.dumps(self.card))
        temp.replace(path)

    def _require(self):
        if not self.uid or self.card is None:
            raise OpsError("NO_CARD", "Present a card first.")

    def present_uid(self):
        return self.uid

    def inspect(self):
        self._require()
        c = self.card
        return Inspection(self.uid, c["version"], c["cc"], c["static"], c["dynamic"], c["cfg0"], c["cfg1"], self.name, True)

    def read_area(self):
        self._require()
        return bytes.fromhex(self.card["area"])

    def write_page(self, page, data):
        assert_safe_page(page, data)
        self._require()
        if self.card["fail_after"] is not None and self.write_count >= self.card["fail_after"]:
            raise OpsError("CARD_REMOVED", "Simulated loss during write. Assignment retained; recovery requires approval.")
        area = bytearray.fromhex(self.card["area"])
        offset = (page - 4)*4
        area[offset:offset+4] = data
        self.card["area"] = area.hex()
        self.write_count += 1
        self.written_pages.append(page)
        self._save()
