from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict
from ..ndef import VERSION, CC
from ..errors import OpsError

@dataclass(frozen=True)
class Inspection:
    uid: str
    version: str
    cc: str
    static_locks: str
    dynamic_locks: str
    config0: str
    config1: str
    reader: str
    simulated: bool

    def public(self):
        return asdict(self)

    def require_safe(self):
        if self.version != VERSION.hex():
            raise OpsError("UNSUPPORTED_TAG", "Exact NTAG215 GET_VERSION response is required; no geometry guessing.")
        if self.cc != CC.hex():
            raise OpsError("UNSUPPORTED_CC", "Expected writable factory NTAG215 CC E1103E00.")
        if any(bytes.fromhex(self.static_locks)) or any(bytes.fromhex(self.dynamic_locks)):
            raise OpsError("LOCKED_TAG", "Lock bits are set. This app never clears or changes locks.")
        cfg0, cfg1 = bytes.fromhex(self.config0), bytes.fromhex(self.config1)
        if len(cfg0) != 4 or len(cfg1) != 4 or cfg0[3] != 255:
            raise OpsError("PROTECTED_TAG", "Password-protected / unusual tags are not provisioned.")
        if cfg0[0] & 0xC0 or cfg1[0] != 0:
            raise OpsError("NONDEFAULT_CONFIG", "Mirroring, counters, access limits or config locking are not supported.")
        if len(self.uid) != 14 or not self.uid.startswith("04"):
            raise OpsError("UNSUPPORTED_UID", "Expected an NXP-style 7-byte UID; this is not an authenticity check.")

class Reader(ABC):
    simulated = False
    name = "Reader"

    @abstractmethod
    def present_uid(self) -> str | None: ...
    @abstractmethod
    def inspect(self) -> Inspection: ...
    @abstractmethod
    def read_area(self) -> bytes: ...
    @abstractmethod
    def write_page(self, page: int, data: bytes) -> None: ...
    def close(self): pass
