"""Loopback-only operator UI + role-limited agent API. Not an internet server."""
from __future__ import annotations
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit, parse_qs
import json
import secrets
import mimetypes
from . import __version__
from .errors import OpsError
from .exporting import inventory_csv, qr_svg

WEB = Path(__file__).parent / "web"

class LocalServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = False

    def __init__(self, engine, directory, port):
        super().__init__(("127.0.0.1", port), Handler)
        self.engine = engine
        self.directory = directory
        self.operator_token = secrets.token_urlsafe(32)
        self.agent_token = secrets.token_urlsafe(32)
        self.origin = f"http://127.0.0.1:{self.server_port}"
        self.accepted_hosts = {f"127.0.0.1:{self.server_port}", f"localhost:{self.server_port}"}
        self.accepted_origins = {self.origin, f"http://localhost:{self.server_port}"}

    @property
    def operator_url(self):
        return self.origin + "/#" + self.operator_token

class Handler(BaseHTTPRequestHandler):
    server_version = "nfcraft/" + __version__
    protocol_version = "HTTP/1.0"

    def log_message(self, *_):
        pass  # Never log authorization headers, URL fragments, or card contents.

    def _response(self, status, content, mime="application/json", filename=None):
        if isinstance(content, (dict,list)):
            content = json.dumps(content, ensure_ascii=False).encode("utf-8")
        elif isinstance(content, str):
            content = content.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", mime + ("; charset=utf-8" if mime.startswith("text/") or mime=="application/json" else ""))
        self.send_header("Content-Length", str(len(content)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'; form-action 'self'")
        if filename:
            self.send_header("Content-Disposition", f'attachment; filename="{filename}"')
        self.end_headers()
        try:
            self.wfile.write(content)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def _guard(self, api=False):
        if self.headers.get("Host") not in self.server.accepted_hosts:
            raise OpsError("BAD_HOST", "Only the loopback app host is accepted.")
        origin = self.headers.get("Origin")
        if origin and origin not in self.server.accepted_origins:
            raise OpsError("BAD_ORIGIN", "Cross-origin requests are not accepted.")
        if self.headers.get("Sec-Fetch-Site") == "cross-site":
            raise OpsError("BAD_ORIGIN", "Cross-site requests are not accepted.")
        if not api:
            return None
        auth = self.headers.get("Authorization", "")
        if secrets.compare_digest(auth, "Bearer " + self.server.operator_token):
            return "operator"
        if secrets.compare_digest(auth, "Bearer " + self.server.agent_token):
            return "agent"
        raise OpsError("UNAUTHORIZED", "Open the app using its launcher, or connect using its agent runtime file.")

    def _body(self):
        if self.headers.get("Transfer-Encoding"):
            raise OpsError("INVALID_REQUEST", "Chunked requests are not supported.")
        if self.headers.get_content_type() != "application/json":
            raise OpsError("INVALID_REQUEST", "Use application/json.")
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError as exc:
            raise OpsError("INVALID_REQUEST", "Invalid body length.") from exc
        if not 0 < length <= 65536:
            raise OpsError("INVALID_REQUEST", "Request body must be 1–65,536 bytes.")
        self.connection.settimeout(5)
        try:
            data = json.loads(self.rfile.read(length))
        except (ValueError, OSError) as exc:
            raise OpsError("INVALID_JSON", "Invalid JSON body.") from exc
        if not isinstance(data, dict):
            raise OpsError("INVALID_JSON", "Expected a JSON object.")
        return data

    def _operator(self, role):
        if role != "operator":
            raise OpsError("OPERATOR_REQUIRED", "This operation is not available through agent credentials.")

    def do_GET(self):
        try:
            path = urlsplit(self.path).path
            role = self._guard(api=path.startswith("/api/"))
            engine = self.server.engine
            if path == "/api/state":
                return self._response(200, engine.snapshot())
            if path == "/api/manifest":
                with engine.lock:
                    value = engine.store.manifest()
                return self._response(200, value, filename="routes-manifest.json")
            if path == "/api/inventory.csv":
                with engine.lock:
                    text = inventory_csv(engine.store.inventory())
                return self._response(200, text, "text/csv", "inventory.csv")
            if path == "/api/qr":
                cid = parse_qs(urlsplit(self.path).query).get("id", [""])[0]
                with engine.lock:
                    match = next((c for c in engine.store.inventory() if c["id"] == cid and c["status"]=="verified"), None)
                if not match:
                    raise OpsError("NOT_FOUND", "Select a verified card.")
                return self._response(200, qr_svg(match["url"]), "image/svg+xml", "card-qr.svg")
            if path == "/api/audit":
                with engine.lock:
                    value = engine.store.check_audit()
                return self._response(200, value)
            static = {"/":"index.html", "/app.js":"app.js", "/style.css":"style.css"}
            if path in static:
                f = WEB / static[path]
                return self._response(200, f.read_bytes(), mimetypes.guess_type(f.name)[0] or "application/octet-stream")
            return self._response(404, {"error":{"code":"NOT_FOUND","message":"Unknown path."}})
        except OpsError as exc:
            self._error(exc)
        except Exception:
            self._response(500, {"error":{"code":"INTERNAL_ERROR","message":"Operation failed. Check the local journal."}})

    def do_POST(self):
        try:
            path = urlsplit(self.path).path
            role = self._guard(api=True)
            payload = self._body()
            engine = self.server.engine
            if path == "/api/batches":
                return self._response(201, engine.create_batch(payload))
            if path == "/api/inspect":
                return self._response(200, engine.inspect())
            if path == "/api/pause":
                return self._response(200, engine.pause())
            self._operator(role)
            if path == "/api/arm":
                return self._response(200, engine.arm(payload))
            if path == "/api/profile":
                with engine.lock:
                    profile = engine.store.update_profile(payload)
                return self._response(200, profile)
            if path == "/api/route":
                with engine.lock:
                    engine.store.set_route_state(payload.get("card_id"), payload.get("state"))
                return self._response(200, {"saved":True,"public_change_pending":True})
            if path == "/api/backup":
                with engine.lock:
                    destination = self.server.directory / "journal-backup.sqlite3"
                    engine.store.backup(destination)
                return self._response(200, {"saved_to":str(destination),"contains_local_uids":True})
            if path.startswith("/api/mock/"):
                if not engine.reader.simulated:
                    raise OpsError("NOT_SIMULATION", "Mock operations do not exist in hardware mode.")
                with engine.lock:
                    if path == "/api/mock/insert":
                        uid = engine.reader.insert(payload.get("scenario","blank"), payload.get("uid"))
                        return self._response(200, {"uid":uid})
                    if path == "/api/mock/remove":
                        engine.reader.remove()
                        # Removal observed directly by the mock adapter, not inferred from time.
                        engine.latch_uid = None
                        return self._response(200, {"removed":True})
                    if path == "/api/mock/clear-fault":
                        engine.reader.clear_fault()
                        return self._response(200, {"fault_cleared":True})
            return self._response(404, {"error":{"code":"NOT_FOUND","message":"Unknown operation."}})
        except OpsError as exc:
            self._error(exc)
        except Exception:
            self._response(500, {"error":{"code":"INTERNAL_ERROR","message":"Operation failed. No additional action was attempted."}})

    def _error(self, exc):
        status = 401 if exc.code=="UNAUTHORIZED" else 403 if exc.code in ("BAD_HOST","BAD_ORIGIN","OPERATOR_REQUIRED") else 409
        self._response(status, {"error":exc.as_dict()})

    def do_OPTIONS(self):
        self._response(403, {"error":{"code":"CORS_DISABLED","message":"Cross-origin access is disabled."}})
