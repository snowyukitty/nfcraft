"""SQLite journal: durable UID reservation precedes every card write."""
from __future__ import annotations
from contextlib import contextmanager, closing
from pathlib import Path
import hashlib
import json
import secrets
import sqlite3
from datetime import datetime, timezone
from .errors import OpsError
from .ndef import validate_base, encode_area


def now():
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)

SCHEMA = """
PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS meta(key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS profiles(id TEXT PRIMARY KEY, name TEXT NOT NULL, headline TEXT NOT NULL,
  bio TEXT NOT NULL, email TEXT NOT NULL, website TEXT NOT NULL, revision INTEGER NOT NULL DEFAULT 1);
CREATE TABLE IF NOT EXISTS batches(id TEXT PRIMARY KEY, name TEXT NOT NULL, target INTEGER NOT NULL,
  base TEXT NOT NULL, profile_id TEXT NOT NULL REFERENCES profiles(id), created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS cards(id TEXT PRIMARY KEY, uid TEXT NOT NULL UNIQUE, slug TEXT NOT NULL UNIQUE,
  batch_id TEXT NOT NULL REFERENCES batches(id), ordinal INTEGER NOT NULL, url TEXT NOT NULL,
  status TEXT NOT NULL CHECK(status IN ('reserved','writing','verifying','verified','quarantined')),
  route_state TEXT NOT NULL DEFAULT 'enabled' CHECK(route_state IN ('enabled','suspended')),
  original_hex TEXT NOT NULL, target_hex TEXT NOT NULL, inspection_json TEXT NOT NULL,
  last_error TEXT, verified_at TEXT, payload_sha256 TEXT, revision INTEGER NOT NULL DEFAULT 1,
  UNIQUE(batch_id,ordinal));
CREATE TABLE IF NOT EXISTS attempts(id TEXT PRIMARY KEY, card_id TEXT NOT NULL REFERENCES cards(id),
  started_at TEXT NOT NULL, finished_at TEXT, outcome TEXT, error TEXT);
CREATE TABLE IF NOT EXISTS audit(seq INTEGER PRIMARY KEY AUTOINCREMENT, at TEXT NOT NULL, kind TEXT NOT NULL,
  data TEXT NOT NULL, prev_hash TEXT NOT NULL, hash TEXT NOT NULL);
"""

class Store:
    def __init__(self, path: Path, mode="demo"):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.path = path
        self.db = sqlite3.connect(path, isolation_level=None, check_same_thread=False)
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.execute("PRAGMA synchronous=FULL")
        self.db.executescript(SCHEMA)
        stored_mode = self.db.execute("SELECT value FROM meta WHERE key='mode'").fetchone()
        if stored_mode and stored_mode[0] != mode:
            self.db.close()
            raise OpsError("MODE_MISMATCH", "Simulation and physical workspaces must remain separate.")
        self.db.execute("INSERT OR IGNORE INTO meta VALUES('mode',?)", (mode,))
        self.db.execute("INSERT OR IGNORE INTO meta VALUES('schema','1')")
        self.db.execute("INSERT OR IGNORE INTO profiles VALUES('main','Your name','A small card. A lasting connection.','Replace these placeholders before publishing.','','',1)")
        self.mode = mode
        with self.transaction():
            interrupted = self.db.execute("SELECT id FROM cards WHERE status IN ('reserved','writing','verifying')").fetchall()
            for row in interrupted:
                self.db.execute("UPDATE cards SET status='quarantined',last_error='PROCESS_INTERRUPTED' WHERE id=?", (row[0],))
                self.audit("recovery_required", {"card_id": row[0], "reason": "PROCESS_INTERRUPTED"})
            self.db.execute("UPDATE attempts SET finished_at=?,outcome='interrupted',error='PROCESS_INTERRUPTED' WHERE finished_at IS NULL", (now(),))

    @contextmanager
    def transaction(self):
        self.db.execute("BEGIN IMMEDIATE")
        try:
            yield
            self.db.execute("COMMIT")
        except BaseException:
            self.db.execute("ROLLBACK")
            raise

    def audit(self, kind, data):
        previous = self.db.execute("SELECT hash FROM audit ORDER BY seq DESC LIMIT 1").fetchone()
        prev = previous[0] if previous else "0"*64
        at, text = now(), canonical(data)
        digest = hashlib.sha256((prev + at + kind + text).encode()).hexdigest()
        self.db.execute("INSERT INTO audit(at,kind,data,prev_hash,hash) VALUES(?,?,?,?,?)", (at,kind,text,prev,digest))

    def check_audit(self):
        prev = "0"*64
        rows = self.db.execute("SELECT * FROM audit ORDER BY seq").fetchall()
        for row in rows:
            digest = hashlib.sha256((prev + row["at"] + row["kind"] + row["data"]).encode()).hexdigest()
            if row["prev_hash"] != prev or row["hash"] != digest:
                return {"ok": False, "bad_seq": row["seq"], "count": len(rows)}
            prev = row["hash"]
        return {"ok": True, "count": len(rows), "head": prev,
                "note": "Hash chaining detects ordinary edits, not privileged rewriting or suffix truncation."}

    def create_batch(self, name, target, base, profile_id="main"):
        if not isinstance(name, str) or not name.strip() or len(name) > 80 or any(ord(c)<32 for c in name):
            raise OpsError("INVALID_NAME", "Batch name must contain 1–80 printable characters.")
        if type(target) is not int or not 1 <= target <= 1000:
            raise OpsError("INVALID_TARGET", "Batch size must be an integer from 1 to 1,000.")
        base = validate_base(base, production=self.mode=="hardware")
        if not self.db.execute("SELECT 1 FROM profiles WHERE id=?", (profile_id,)).fetchone():
            raise OpsError("PROFILE_NOT_FOUND", "Unknown public profile.")
        bid = "b_" + secrets.token_hex(5)
        with self.transaction():
            self.db.execute("INSERT INTO batches VALUES(?,?,?,?,?,?)", (bid,name.strip(),target,base,profile_id,now()))
            self.audit("batch_created", {"batch_id":bid,"name":name.strip(),"target":target,"base":base})
        return self.batch(bid)

    def batch(self, bid):
        row = self.db.execute("SELECT * FROM batches WHERE id=?", (bid,)).fetchone()
        if not row:
            raise OpsError("NOT_FOUND", "Batch not found.")
        return dict(row)

    def by_uid(self, uid):
        row = self.db.execute("SELECT * FROM cards WHERE uid=?", (uid,)).fetchone()
        return dict(row) if row else None

    def reserve(self, batch, inspection, original):
        with self.transaction():
            existing = self.by_uid(inspection.uid)
            if existing:
                return existing
            count = self.db.execute("SELECT COUNT(*) FROM cards WHERE batch_id=?", (batch["id"],)).fetchone()[0]
            if count >= batch["target"]:
                raise OpsError("BATCH_FULL", "All card identities are reserved; recover quarantined cards or create another batch.")
            slug = secrets.token_urlsafe(16)
            url = batch["base"] + "/c/" + slug
            cid = "card_" + secrets.token_hex(6)
            target = encode_area(url)
            self.db.execute("""INSERT INTO cards(id,uid,slug,batch_id,ordinal,url,status,original_hex,target_hex,inspection_json)
                               VALUES(?,?,?,?,?,?,'reserved',?,?,?)""",
                            (cid,inspection.uid,slug,batch["id"],count+1,url,original.hex(),target.hex(),canonical(inspection.public())))
            self.audit("identity_reserved", {"card_id":cid,"batch_id":batch["id"],"ordinal":count+1,"url":url})
        return self.by_uid(inspection.uid)

    def begin_attempt(self, card):
        aid = "a_" + secrets.token_hex(6)
        with self.transaction():
            self.db.execute("INSERT INTO attempts(id,card_id,started_at) VALUES(?,?,?)", (aid,card["id"],now()))
            self.db.execute("UPDATE cards SET status='writing',last_error=NULL WHERE id=?", (card["id"],))
            self.audit("write_started", {"card_id":card["id"],"attempt_id":aid})
        return aid

    def verified(self, card, aid, target):
        with self.transaction():
            stamp = now()
            digest = hashlib.sha256(target).hexdigest()
            self.db.execute("UPDATE cards SET status='verified',verified_at=?,payload_sha256=?,last_error=NULL WHERE id=?", (stamp,digest,card["id"]))
            self.db.execute("UPDATE attempts SET finished_at=?,outcome='verified' WHERE id=?", (stamp,aid))
            self.audit("readback_verified", {"card_id":card["id"],"sha256":digest,"publicly_live":False})

    def quarantine(self, card, aid, error):
        with self.transaction():
            self.db.execute("UPDATE cards SET status='quarantined',last_error=? WHERE id=?", (error.code,card["id"]))
            if aid:
                self.db.execute("UPDATE attempts SET finished_at=?,outcome='quarantined',error=? WHERE id=?", (now(),error.code,aid))
            self.audit("quarantined", {"card_id":card["id"],"error":error.as_dict()})

    def inventory(self):
        return [dict(r) for r in self.db.execute("""SELECT c.id,c.uid,c.slug,c.batch_id,c.ordinal,c.url,c.status,c.route_state,
                   c.last_error,c.verified_at,c.payload_sha256,c.revision,b.name AS batch_name
                   FROM cards c JOIN batches b ON b.id=c.batch_id ORDER BY c.rowid DESC""")]

    def batches(self):
        return [dict(r) for r in self.db.execute("""SELECT b.*,
            COUNT(c.id) AS allocated,
            COALESCE(SUM(c.status='verified'),0) AS verified,
            COALESCE(SUM(c.status='quarantined'),0) AS quarantined
            FROM batches b LEFT JOIN cards c ON c.batch_id=b.id GROUP BY b.id ORDER BY b.created_at DESC""")]

    def profiles(self):
        return [dict(r) for r in self.db.execute("SELECT * FROM profiles ORDER BY id")]

    def update_profile(self, payload):
        allowed = ("name", "headline", "bio", "email", "website")
        values = {}
        for key in allowed:
            value = payload.get(key, "")
            if not isinstance(value, str) or len(value) > (1200 if key=="bio" else 160) or any(ord(c)<32 and c!='\n' for c in value):
                raise OpsError("INVALID_PROFILE", "Invalid profile field: " + key)
            values[key] = value.strip()
        if not values["name"]:
            raise OpsError("INVALID_PROFILE", "A display name is required.")
        if any(c in values["email"] for c in "\r\n") or (values["email"] and ("@" not in values["email"] or " " in values["email"])):
            raise OpsError("INVALID_PROFILE", "Use a simple email address.")
        if values["website"]:
            from .ndef import validate_https
            validate_https(values["website"])
        with self.transaction():
            self.db.execute("UPDATE profiles SET name=?,headline=?,bio=?,email=?,website=?,revision=revision+1 WHERE id='main'", tuple(values[k] for k in allowed))
            self.audit("profile_updated", {"profile_id":"main"})
        return self.profiles()[0]

    def set_route_state(self, cid, state):
        if state not in ("enabled", "suspended"):
            raise OpsError("INVALID_STATE", "Route state must be enabled or suspended.")
        with self.transaction():
            row = self.db.execute("SELECT status FROM cards WHERE id=?", (cid,)).fetchone()
            if not row or row[0] != "verified":
                raise OpsError("NOT_VERIFIED", "Only verified assignments have exportable routes.")
            self.db.execute("UPDATE cards SET route_state=?,revision=revision+1 WHERE id=?", (state,cid))
            self.audit("route_state_changed", {"card_id":cid,"state":state,"requires_redeployment":True})

    def manifest(self, cards=None):
        # No UID or inspection dumps leave the local database.
        routes = [dict(r) for r in self.db.execute("""SELECT c.slug,c.url,c.route_state AS state,c.revision,b.profile_id
                    FROM cards c JOIN batches b ON b.id=c.batch_id WHERE c.status='verified' ORDER BY c.slug""")]
        profiles = self.profiles()
        if cards is not None:
            slugs = {c["slug"] for c in cards}
            routes = [r for r in routes if r["slug"] in slugs]
            if routes:
                used = {r["profile_id"] for r in routes}
                profiles = [p for p in profiles if p["id"] in used]
        body = {"schema":1,"simulated":self.mode=="demo","profiles":profiles,"routes":routes}
        return {**body,"sha256":hashlib.sha256(canonical(body).encode()).hexdigest(),"generated_at":now()}

    def events(self):
        return [dict(r) for r in self.db.execute("SELECT seq,at,kind,data,hash FROM audit ORDER BY seq DESC LIMIT 150")]

    def backup(self, destination):
        with closing(sqlite3.connect(destination)) as copy:
            self.db.backup(copy)

    def close(self):
        self.db.close()
