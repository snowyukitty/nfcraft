"""Agent CLI. All machine commands reuse the running daemon; no second writer."""
from __future__ import annotations
import argparse
import json
import sys
import urllib.request
import urllib.error
from urllib.parse import urlsplit
from . import __version__
from .runtime import workspace
from .errors import OpsError

class _NoRedirects(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise OpsError("REDIRECT_BLOCKED", "The loopback agent client does not follow redirects.")


class Client:
    def __init__(self, mode="demo", root=None):
        path = workspace(mode,root) / "agent-runtime.json"
        try:
            runtime = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise OpsError("DAEMON_NOT_RUNNING", "Start the app in the same mode/workspace first.") from exc
        origin = runtime.get("origin", "")
        p = urlsplit(origin)
        if p.scheme != "http" or p.hostname != "127.0.0.1" or p.path or p.query or p.fragment or p.username or p.password:
            raise OpsError("INVALID_RUNTIME", "Agent runtime must point to the loopback daemon.")
        self.origin, self.token = origin, runtime["token"]
        # Never send local capability tokens through an environment-configured proxy.
        self.opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), _NoRedirects())

    def call(self, path, payload=None):
        data = json.dumps(payload).encode() if payload is not None else None
        request = urllib.request.Request(self.origin+path, data=data,
            headers={"Authorization":"Bearer "+self.token,"Content-Type":"application/json"})
        try:
            with self.opener.open(request, timeout=30) as response:
                return json.load(response)
        except urllib.error.HTTPError as exc:
            try:
                body = json.load(exc)
                error = body.get("error", {}) if isinstance(body, dict) else {}
                if not isinstance(error, dict):
                    error = {}
            except (ValueError, OSError):
                error = {}
            raise OpsError(error.get("code","HTTP_ERROR"),error.get("message","Request failed.")) from exc
        except (OSError, ValueError) as exc:
            raise OpsError("DAEMON_UNREACHABLE", "Could not reach the app. Verify its workspace and mode.") from exc


def main(argv=None):
    parser = argparse.ArgumentParser(description="nfcraft agent-safe CLI; outputs JSON")
    parser.add_argument("--version", action="version", version="nfcraftctl " + __version__)
    parser.add_argument("--mode", choices=("demo","hardware"), default="demo")
    parser.add_argument("--data-dir")
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("status","inspect","pause","manifest","audit","doctor","mcp"):
        sub.add_parser(name)
    batch = sub.add_parser("batch-create")
    batch.add_argument("--name",required=True)
    batch.add_argument("--count",type=int,required=True)
    batch.add_argument("--base",required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "doctor":
            from .adapters.pcsc import list_readers
            try:
                devices = {"readers":list_readers()}
            except OpsError as exc:
                devices = {"reader_diagnostic":exc.as_dict()}
            result = {"python":sys.version.split()[0],"workspace":str(workspace(args.mode,args.data_dir)),
                      "mode":args.mode,"hardware_qualified":False,**devices}
        elif args.command == "mcp":
            from .mcp import serve
            return serve(Client(args.mode,args.data_dir))
        else:
            client = Client(args.mode,args.data_dir)
            routes = {"status":("/api/state",None),"inspect":("/api/inspect",{}),"pause":("/api/pause",{}),
                      "manifest":("/api/manifest",None),"audit":("/api/audit",None)}
            if args.command == "batch-create":
                result = client.call("/api/batches", {"name":args.name,"target":args.count,"base":args.base})
            else:
                result = client.call(*routes[args.command])
        print(json.dumps(result,ensure_ascii=False,indent=2))
        return 0
    except OpsError as exc:
        print(json.dumps({"error":exc.as_dict()},ensure_ascii=False),file=sys.stderr)
        return 2
