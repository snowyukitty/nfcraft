"""EXPERIMENTAL ACS ACR1552U adapter. No physical qualification claimed.

Requires pyscard and an exact reader name. Uses PC/SC transparent sessions in
ISO14443-A layer 3 for native NTAG commands; no PN532/ACR122U command reuse.
Responses must contain valid C0 status and 97 response objects. Unsupported
firmware/response shapes fail closed, before provisioning. See hardware.md.
"""
from __future__ import annotations
from .base import Reader, Inspection
from ..errors import OpsError
from ..ndef import assert_safe_page


def parse_objects(data: bytes) -> dict[int, bytes]:
    result, i = {}, 0
    while i < len(data):
        if i + 2 > len(data):
            raise OpsError("BAD_READER_RESPONSE", "Truncated response TLV.")
        tag, length = data[i], data[i+1]
        i += 2
        if length & 0x80:  # Small supported native commands never need BER long lengths.
            raise OpsError("BAD_READER_RESPONSE", "Unexpected long response object.")
        if i + length > len(data) or tag in result:
            raise OpsError("BAD_READER_RESPONSE", "Truncated or duplicate response object.")
        result[tag] = data[i:i+length]
        i += length
    if result.get(0xC0) != b"\x00\x90\x00":
        raise OpsError("READER_STATUS", "Reader reported a transparent-session error.")
    return result


def list_readers() -> list[str]:
    try:
        from smartcard.System import readers
        return [str(r) for r in readers()]
    except ImportError as exc:
        raise OpsError("DEPENDENCY_MISSING", "Install the [hardware] extra to use pyscard.") from exc
    except Exception as exc:
        raise OpsError("PCSC_UNAVAILABLE", "PC/SC is unavailable. Check the driver and Smart Card service.") from exc


class Acs1552Reader(Reader):
    simulated = False

    def __init__(self, reader_name: str, allow_writes=False):
        if "ACR1552" not in reader_name.upper() or "SAM" in reader_name.upper():
            raise OpsError("READER_NOT_ALLOWED", "Select the ACR1552U PICC reader, not a SAM or other model.")
        self.name = reader_name
        self.allow_writes = allow_writes
        self.connection = None
        self.transparent = False
        self.uid = None

    def _send(self, command: bytes) -> bytes:
        if self.connection is None:
            raise OpsError("NO_CARD", "No card is connected.")
        try:
            data, sw1, sw2 = self.connection.transmit(list(command))
        except Exception as exc:
            # PC/SC distinguishes an absent/removed card from reader, sharing and RF faults.
            # An absence during a write is still an uncertain outcome, never a rollback.
            hr = getattr(exc, "hresult", None)
            if isinstance(hr, int) and (hr & 0xffffffff) in (0x8010000C, 0x80100069):
                raise OpsError("CARD_REMOVED", "PC/SC reported card removal; re-inspect any interrupted write.") from exc
            raise OpsError("CARD_IO", "PC/SC communication failed. Do not assume the write did not happen.") from exc
        if (sw1, sw2) != (0x90, 0):
            raise OpsError("APDU_STATUS", f"Reader returned {sw1:02X}{sw2:02X}; no fallback write attempted.")
        return bytes(data)

    def _session(self):
        if self.transparent:
            return
        parse_objects(self._send(bytes.fromhex("FF C2 00 00 02 81 00")))
        self.transparent = True
        parse_objects(self._send(bytes.fromhex("FF C2 00 02 04 8F 02 00 03")))

    def _raw(self, native: bytes, expected: int) -> bytes:
        self._session()
        if native[0] not in (0x60, 0x30, 0xA2):
            raise OpsError("FORBIDDEN_COMMAND", "Native command is not allowed.")
        packet = bytes((0xFF, 0xC2, 0, 1, len(native)+2, 0x95, len(native))) + native + b"\x00"
        objects = parse_objects(self._send(packet))
        if 0x96 in objects and any(objects[0x96]):
            raise OpsError("RF_STATUS", "Reader reported an RF reception error.")
        data = objects.get(0x97)
        if data is None or len(data) != expected:
            raise OpsError("BAD_READER_RESPONSE", "Unexpected native response length; driver needs qualification.")
        return data

    def _head(self):
        data = self._raw(b"\x30\x00", 16)
        uid = data[:3] + data[4:8]
        if data[3] != (0x88 ^ uid[0] ^ uid[1] ^ uid[2]) or data[8] != (uid[3] ^ uid[4] ^ uid[5] ^ uid[6]):
            raise OpsError("UID_CHECK_FAILED", "UID/BCC mismatch; stop and inspect the tag.")
        return uid.hex(), data

    def present_uid(self):
        try:
            if self.connection is None:
                from smartcard.System import readers
                from smartcard.CardConnection import CardConnection
                from smartcard.scard import SCARD_SHARE_EXCLUSIVE
                matches = [r for r in readers() if str(r) == self.name]
                if len(matches) != 1:
                    raise OpsError("READER_MISSING", "The exact selected PICC reader is unavailable.")
                self.connection = matches[0].createConnection()
                try:
                    self.connection.connect(protocol=CardConnection.T1_protocol, mode=SCARD_SHARE_EXCLUSIVE)
                except Exception as exc:
                    self.close()
                    from smartcard.Exceptions import NoCardException
                    hr = getattr(exc, "hresult", None)
                    if isinstance(exc, NoCardException) or (isinstance(hr, int) and (hr & 0xffffffff) in (0x8010000C, 0x80100069)):
                        return None
                    raise OpsError("CONNECT_FAILED", "Could not acquire the selected reader exclusively. Close other NFC apps and check the driver.") from exc
                raw_uid = self._send(bytes.fromhex("FF CA 00 00 00"))
                if len(raw_uid) != 7:
                    raise OpsError("UNSUPPORTED_UID", "Only 7-byte NTAG215 UIDs are accepted.")
                self.uid = raw_uid.hex()
            uid, _ = self._head()
            if uid != self.uid:
                raise OpsError("TAG_CHANGED", "Card changed without a clean removal event.")
            return uid
        except OpsError as exc:
            self.close()
            if exc.code == "CARD_REMOVED":
                return None
            raise
        except ImportError as exc:
            raise OpsError("DEPENDENCY_MISSING", "Install the [hardware] extra.") from exc

    def inspect(self):
        if self.connection is None:
            if self.present_uid() is None:
                raise OpsError("NO_CARD", "Place one NTAG215 on the reader.")
        version = self._raw(b"\x60", 8)
        uid, head = self._head()
        # Only inspect NTAG215 high pages after exact version evidence.
        from ..ndef import VERSION
        if version != VERSION:
            raise OpsError("UNSUPPORTED_TAG", "GET_VERSION does not match NTAG215; no high-page access attempted.")
        tail = self._raw(bytes((0x30, 0x82)), 16)
        return Inspection(uid, version.hex(), head[12:16].hex(), head[10:12].hex(), tail[:3].hex(),
                          tail[4:8].hex(), tail[8:12].hex(), self.name, False)

    def read_area(self):
        return b"".join(self._raw(bytes((0x30, page)), 16) for page in range(4, 128, 4))

    def write_page(self, page, data):
        assert_safe_page(page, data)
        if not self.allow_writes:
            raise OpsError("HARDWARE_WRITES_DISABLED", "Restart with the explicit experimental hardware-write flag after read-only qualification.")
        ack = self._raw(bytes((0xA2, page)) + data, 1)
        if ack != b"\x0a":
            raise OpsError("TAG_NAK", "Tag did not acknowledge the four-byte write.")

    def close(self):
        if self.connection:
            if self.transparent:
                try:
                    self._send(bytes.fromhex("FF C2 00 00 02 82 00"))
                except Exception:
                    pass
            try:
                self.connection.disconnect()
                self.connection.release()
            except Exception:
                pass
        self.connection, self.uid, self.transparent = None, None, False
