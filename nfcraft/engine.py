"""One deterministic writer; agents prepare jobs, an operator arms bounded runs."""
from __future__ import annotations
import json
import threading
import time
from . import __version__
from .store import Store, now
from .adapters.base import Reader
from .errors import OpsError
from .ndef import encode_area, write_plan, is_empty, recovery_matches, decode_area

class Engine:
    def __init__(self, store: Store, reader: Reader):
        if (store.mode == "demo") != reader.simulated:
            raise OpsError("MODE_MISMATCH", "Mock and physical workspaces cannot be mixed.")
        self.store, self.reader = store, reader
        self.lock = threading.RLock()
        self.stop = threading.Event()
        self.pause_requested = threading.Event()
        self.armed = None
        self.latch_uid = None
        self.phase = "idle"
        self.message = "Choose a batch, then arm a bounded run."
        self.last = None
        self.worker = None

    def snapshot(self):
        with self.lock:
            armed = None
            if self.armed:
                remaining = max(0, int(self.armed["expires"] - time.monotonic()))
                armed = {k:v for k,v in self.armed.items() if k != "expires"}
                armed["seconds_remaining"] = remaining
            return {"version":__version__,"mode":self.store.mode,"reader":self.reader.name,
                    "hardware_qualified":False,"writes_enabled": self.reader.simulated or self.reader.allow_writes,
                    "phase":self.phase,"message":self.message,"armed":armed,"last":self.last,
                    "batches":self.store.batches(),"cards":self.store.inventory(),"profiles":self.store.profiles(),
                    "events":self.store.events(),"audit":self.store.check_audit(),
                    "publication":"Not deployed by this app. Local verification is not public availability."}

    def create_batch(self, payload):
        with self.lock:
            return self.store.create_batch(payload.get("name"), payload.get("target"), payload.get("base", ""), payload.get("profile_id", "main"))

    def inspect(self):
        with self.lock:
            uid = self.reader.present_uid()
            if not uid:
                raise OpsError("NO_CARD", "Place a card on the reader first.")
            inspection = self.reader.inspect()
            safe, reason = True, None
            try:
                inspection.require_safe()
            except OpsError as exc:
                safe, reason = False, exc.as_dict()
            # Avoid high-page reads on unsupported geometries in mock/other adapters.
            url = decode_area(self.reader.read_area()) if safe else None
            return {**inspection.public(),"safe_to_provision":safe,"reason":reason,"url":url,
                    "known_assignment": self.store.by_uid(uid) is not None,
                    "authenticity":"not verified; UID and version do not prove unclonability"}

    def arm(self, payload):
        with self.lock:
            if self.armed:
                raise OpsError("ALREADY_ARMED", "Pause the current run before arming another.")
            if not self.store.check_audit()["ok"]:
                raise OpsError("AUDIT_INVALID", "Audit continuity failed. Investigate before approving more writes.")
            batch = self.store.batch(payload.get("batch_id"))
            if payload.get("confirmation") != "ARM " + batch["name"]:
                raise OpsError("CONFIRMATION_REQUIRED", "Type ARM followed by the exact batch name.")
            limit = payload.get("limit", batch["target"])
            seconds = payload.get("seconds", 600)
            if type(limit) is not int or not 1 <= limit <= 1000 or type(seconds) is not int or not 15 <= seconds <= 600:
                raise OpsError("INVALID_LEASE", "Use 1–1,000 attempts and a 15–600 second arming window.")
            if not self.reader.simulated and not self.reader.allow_writes:
                raise OpsError("HARDWARE_WRITES_DISABLED", "Read-only mode. Complete hardware qualification before enabling experimental writes.")
            recover_uid = payload.get("recover_uid")
            if recover_uid:
                row = self.store.by_uid(recover_uid)
                if not row or row["batch_id"] != batch["id"] or row["status"] != "quarantined":
                    raise OpsError("INVALID_RECOVERY", "Select a quarantined assignment from this batch.")
                limit = 1
            else:
                if self.reader.present_uid() is not None:
                    raise OpsError("REMOVE_BEFORE_ARM", "Remove the card before arming a normal run.")
                allocated = self.store.db.execute("SELECT COUNT(*) FROM cards WHERE batch_id=?", (batch["id"],)).fetchone()[0]
                if allocated >= batch["target"]:
                    raise OpsError("BATCH_FULL", "Batch identities are fully allocated; recover quarantined cards instead.")
            self.pause_requested.clear()
            self.latch_uid = None
            self.armed = {"batch_id":batch["id"],"remaining_attempts":limit,"expires":time.monotonic()+seconds,"recover_uid":recover_uid}
            self.phase = "ready"
            self.message = "Present the recovery card." if recover_uid else "Place one card on the reader."
            self.store.audit("run_armed", {"batch_id":batch["id"],"limit":limit,"seconds":seconds,"recovery":bool(recover_uid)})
            return {"armed":True,"batch_id":batch["id"]}

    def pause(self):
        # Set before acquiring the writer lock: cancellation is observed between pages.
        self.pause_requested.set()
        with self.lock:
            self.armed = None
            self.phase = "paused"
            self.message = "Paused. No further card will be written."
            self.store.audit("run_paused", {})
        return {"paused":True}

    def _check_lease(self):
        if self.pause_requested.is_set() or not self.armed or time.monotonic() >= self.armed["expires"]:
            raise OpsError("RUN_STOPPED", "Run paused or its arming window expired; uncertain writes require recovery.")

    def tick(self):
        with self.lock:
            if not self.armed:
                return
            if self.pause_requested.is_set() or time.monotonic() >= self.armed["expires"]:
                self.armed = None
                self.phase = "paused"
                self.message = "Arming window ended. Re-arm when ready."
                return
            try:
                uid = self.reader.present_uid()
                if uid is None:
                    self.latch_uid = None
                    self.phase = "ready"
                    self.message = "Place one card on the reader."
                    return
                if uid == self.latch_uid:
                    return
                self.latch_uid = uid
                self._provision(uid)
            except OpsError as exc:
                self._fail(exc)
            except Exception:
                self._fail(OpsError("INTERNAL_ERROR", "Unexpected error; run stopped. Inspect the journal before retrying."))

    def _fail(self, error):
        self.armed = None
        self.phase = "attention"
        self.message = error.message
        self.last = {"ok":False,"code":error.code,"message":error.message,"at":now()}
        self.store.audit("run_stopped", error.as_dict())

    def _provision(self, uid):
        self._check_lease()
        batch = self.store.batch(self.armed["batch_id"])
        recover_uid = self.armed["recover_uid"]
        if recover_uid and uid != recover_uid:
            raise OpsError("WRONG_RECOVERY_CARD", "The presented UID does not match the approved recovery assignment.")
        self.phase = "inspecting"
        inspection = self.reader.inspect()
        inspection.require_safe()
        if inspection.uid != uid:
            raise OpsError("TAG_CHANGED", "Tag changed during inspection.")
        original = self.reader.read_area()
        existing = self.store.by_uid(uid)
        if existing:
            if existing["status"] == "verified":
                raise OpsError("DUPLICATE_CARD", "Already verified. No new identity was allocated and no write was attempted.")
            if not recover_uid or existing["batch_id"] != batch["id"]:
                raise OpsError("RECOVERY_REQUIRED", "This UID already has a reserved identity. Use explicit recovery, not a new batch write.")
            target = bytes.fromhex(existing["target_hex"])
            if not recovery_matches(original, bytes.fromhex(existing["original_hex"]), target):
                raise OpsError("RECOVERY_MISMATCH", "Card data does not match the recorded original/partial write. No overwrite attempted.")
            card = existing
        else:
            if not is_empty(original):
                raise OpsError("FOREIGN_CONTENT", "This card contains existing or unfamiliar data. It will not be overwritten.")
            planned_length = len(encode_area(batch["base"] + "/c/" + "A" * 22))
            if original[:3] == b"\x03\x00\xfe" and any(original[3:planned_length]):
                raise OpsError("OCCUPIED_WRITE_REGION", "The NDEF message is empty, but the planned write region contains data. No overwrite attempted.")
            card = self.store.reserve(batch, inspection, original)
            target = bytes.fromhex(card["target_hex"])
        aid = None
        started = time.monotonic()
        try:
            self._check_lease()
            aid = self.store.begin_attempt(card)
            self.armed["remaining_attempts"] -= 1
            self.phase = "writing"
            for page, data in write_plan(card["url"]):
                self._check_lease()
                if self.reader.present_uid() != uid:
                    raise OpsError("TAG_CHANGED", "Tag changed or was removed before the next page write.")
                self.reader.write_page(page, data)
            self.phase = "verifying"
            self.store.db.execute("UPDATE cards SET status='verifying' WHERE id=?", (card["id"],))
            observed = self.reader.read_area()
            after = self.reader.inspect()
            expected = target + bytes.fromhex(card["original_hex"])[len(target):]
            if observed != expected:
                raise OpsError("VERIFY_FAILED", "Full user-area readback differs from the intended write and preserved tail.")
            if after != inspection or after.uid != uid:
                raise OpsError("IDENTITY_OR_CONFIG_CHANGED", "Tag identity or protected configuration changed during provisioning.")
            self._check_lease()
            self.store.verified(card, aid, target)
            elapsed = round((time.monotonic()-started)*1000)
            self.last = {"ok":True,"uid":uid,"card_id":card["id"],"ordinal":card["ordinal"],"url":card["url"],
                         "batch_name":batch["name"],"elapsed_ms":elapsed,"simulated":self.reader.simulated,"at":now()}
            self.phase = "remove"
            self.message = "Readback verified. Remove this card before the next one."
            allocated = self.store.db.execute("SELECT COUNT(*) FROM cards WHERE batch_id=?", (batch["id"],)).fetchone()[0]
            if self.armed["remaining_attempts"] <= 0 or allocated >= batch["target"]:
                self.armed = None
                self.message = "Run finished. Local verification only; publish and phone-test before distributing."
        except BaseException as exc:
            error = exc if isinstance(exc, OpsError) else OpsError("WRITE_UNCERTAIN", "Write outcome uncertain; do not reuse this assignment.")
            self.store.quarantine(card, aid, error)
            if not isinstance(exc, Exception):
                raise
            raise error

    def start_worker(self):
        def work():
            while not self.stop.wait(0.25):
                self.tick()
        self.worker = threading.Thread(target=work, name="single-nfc-writer", daemon=True)
        self.worker.start()

    def shutdown(self):
        self.pause_requested.set()
        self.stop.set()
        if self.worker:
            self.worker.join(timeout=10)
            if self.worker.is_alive():
                # Do not close the journal underneath a blocked driver thread.
                return
        self.reader.close()
        self.store.close()
