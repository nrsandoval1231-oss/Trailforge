"""Optional loopback workbench; the existing runner owns experiment semantics."""
from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import os
import re
import secrets
import socket
import stat
import sys
import threading
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from importlib.resources import files
from pathlib import Path

from .fixtures import load_bundle_mapping
from .mining import REFERENCE_SUPPLIER, load_project, load_supplier, match_supplier, qualify, render_report
from .policies import BaselineA
from .runner import create_experiment, replay_experiment, verify_experiment

RUN_ID = re.compile(r"[0-9a-f]{32}\Z")
MAX_BODY = 4096
CLOSE_DRAIN_BYTES = MAX_BODY + 1024
CLOSE_DRAIN_SECONDS = 0.25
ERRORS = (OSError, ValueError, TypeError, KeyError, AttributeError)
ASSETS = {"/": ("index.html", "text/html; charset=utf-8"),
          "/app.js": ("app.js", "text/javascript; charset=utf-8"),
          "/style.css": ("style.css", "text/css; charset=utf-8")}
# Operator app (docs/UI_VISION.md). Client-side routes all serve index.html.
APP_ASSETS = {"/app/app.js": ("app.js", "text/javascript; charset=utf-8"),
              "/app/app.css": ("app.css", "text/css; charset=utf-8"),
              "/app/wordmark-white.svg": ("wordmark-white.svg", "image/svg+xml"),
              "/app/icon-jade.svg": ("icon-jade.svg", "image/svg+xml"),
              "/app/Manrope.ttf": ("Manrope.ttf", "font/ttf"),
              "/app/IBMPlexMono-Regular.ttf": ("IBMPlexMono-Regular.ttf", "font/ttf")}


def default_mining_inputs() -> list[Path]:
    """Real checkout imports (never synthetic), from the source tree or the current directory."""
    for root in (Path(__file__).resolve().parents[2], Path.cwd()):
        found = [path for path in (root / "scenarios/fixtures/mining/stibnite/project.json",) if path.is_file()]
        if found:
            return found
    return []


def mining_payload(projects: list[dict], supplier) -> dict:
    """Engine verdicts for the operator app; the browser renders, never decides.

    Owner rule: the operator app never shows synthetic data. Any project with a
    SYNTHETIC source is withheld and only counted.
    """
    from dataclasses import asdict
    out, withheld = [], 0
    for project in projects:
        if any(source["access"] == "SYNTHETIC" for source in project["sources"].values()):
            withheld += 1
            continue
        location = project["project"]["location"]["value"]
        requirements = [{**req, "qualification": qualify(req), "match": match_supplier(req, supplier, location=location)}
                        for req in project["requirements"]]
        out.append({**project, "requirements": requirements})
    return {"supplier": asdict(supplier), "reference_supplier": supplier == REFERENCE_SUPPLIER, "projects": out,
            "withheld_synthetic": withheld}


def safe_path(path: Path) -> Path:
    """Reject symlinks and Windows reparse points, including ancestor junctions."""
    path = path.absolute()
    for part in (*reversed(path.parents), path):
        try:
            info = part.lstat()
        except FileNotFoundError:
            continue
        if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
            raise ValueError("symlink or reparse-point path is not allowed")
    return path.resolve()


class Workbench:
    def __init__(self, root: Path, bundles: list[Path], mining_inputs: list[Path] = (), mining_supplier: Path | None = None):
        self.mining_supplier = load_supplier(safe_path(mining_supplier)) if mining_supplier else load_supplier()
        # Owner rule: no synthetic data on any operator page (app or legacy /mining reports).
        loaded = {}
        for path in mining_inputs:  # later inputs replace earlier ones with the same project_id
            project = load_project(safe_path(path))
            loaded.pop(project["project_id"], None)
            loaded[project["project_id"]] = project
        loaded = list(loaded.values())
        self.mining = [p for p in loaded if not any(s["access"] == "SYNTHETIC" for s in p["sources"].values())]
        self.withheld_synthetic = len(loaded) - len(self.mining)
        self.root = safe_path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.lock = threading.RLock()
        self.token = secrets.token_urlsafe(32)
        self.cases = {}
        self.replays = {}
        for source in bundles:
            source = safe_path(source)
            text = source.read_text(encoding="utf-8")
            raw = json.loads(text)
            if not isinstance(raw, dict):
                raise ValueError("fixture bundle must be an object")
            bundle = load_bundle_mapping(raw)
            if not bundle.fixtures:
                raise ValueError("fixture bundle must contain fixtures")
            for fixture in bundle.fixtures:
                # This extension admits the accepted mechanics case only.
                if fixture.fixture_id != "GT-003":
                    continue
                alias = f"case-{len(self.cases) + 1}"
                self.cases[alias] = {
                    "input_kind": "fixture_bundle", "fixture_id": fixture.fixture_id,
                    "bundle_id": bundle.bundle_id, "bundle_version": bundle.version,
                    "bundle_source_path": str(source), "bundle_text": text,
                    "bundle_sha256": hashlib.sha256(text.encode()).hexdigest(),
                    "fixture": fixture.as_dict(),
                }
        # Hold an OS lock for the server lifetime. Closing releases it, even on crash.
        lock_path = safe_path(self.root / ".local-ui.lock")
        self.root_lock = lock_path.open("a+b")
        try:
            if os.name == "nt":
                import msvcrt
                self.root_lock.seek(0)
                if not self.root_lock.read(1):
                    self.root_lock.write(b"0")
                    self.root_lock.flush()
                self.root_lock.seek(0)
                msvcrt.locking(self.root_lock.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(self.root_lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            self.root_lock.close()
            raise ValueError("experiments directory is already served by another workbench") from exc

    def close(self):
        self.root_lock.close()

    def run_path(self, run_id: str) -> Path:
        if not RUN_ID.fullmatch(run_id):
            raise ValueError("invalid run ID")
        if safe_path(self.root) != self.root:
            raise ValueError("experiments root changed")
        target = safe_path(self.root / run_id)
        if target.parent != self.root:
            raise ValueError("run path escapes experiments root")
        # Reject all links before the runner reads any retained artifact.
        if target.is_dir():
            for child in target.iterdir():
                safe_path(child)
        return target

    def inspect(self, run_id: str) -> dict:
        try:
            manifest, artifacts = verify_experiment(self.run_path(run_id))
            replay = self.replays.get(run_id, {"status": "NOT_RUN"})
            if replay.get("manifest_hash") not in (None, manifest["manifest_hash"]):
                replay = {"status": "NOT_RUN"}
            return {"id": run_id, "integrity": "PASS", "replay": replay,
                    "manifest": manifest, **{name.removesuffix(".json"): value
                                             for name, value in artifacts.items()}}
        except ERRORS as exc:
            return {"id": run_id, "integrity": "FAIL", "replay": {"status": "NOT_RUN"},
                    "error": f"Saved run cannot be verified: {exc}"}

    def listing(self):
        safe_path(self.root)
        result = []
        for item in sorted(self.root.iterdir(), key=lambda p: p.name):
            if RUN_ID.fullmatch(item.name):
                run = self.inspect(item.name)
                result.append({"id": item.name, "integrity": run["integrity"],
                               "scenario": run.get("config", {}).get("scenario_id", "Unreadable run"),
                               "error": run.get("error"), "replay": run["replay"]})
        return result

    def create(self, alias):
        if alias not in self.cases:
            raise ValueError("unknown configured case")
        context = self.cases[alias]
        run_id = uuid.uuid4().hex
        target = self.run_path(run_id)
        scenario = json.dumps(context["fixture"]["scenario"], sort_keys=True, indent=2) + "\n"
        try:
            create_experiment(scenario, context["bundle_source_path"], target,
                              BaselineA(), fixture_context=context)
        except ERRORS as exc:
            return {"id": run_id, "integrity": "FAIL", "replay": {"status": "NOT_RUN"},
                    "error": f"Run was not completed: {exc}. Refresh saved runs to inspect retained partial data."}
        return self.inspect(run_id)


class WorkbenchServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, workbench: Workbench, port: int):
        self.workbench = workbench
        super().__init__(("127.0.0.1", port), Handler)
        self.authority = f"127.0.0.1:{self.server_port}"
        self.origin = f"http://{self.authority}"

    def shutdown_request(self, request):
        # http.client sends headers and body separately. Immediate close after
        # header rejection can turn a late body into Windows error 10053 before
        # the client reads our response. Half-close output, then discard a small
        # bounded tail. Never interpret rejected framing or dispatch more work.
        try:
            request.shutdown(socket.SHUT_WR)
            deadline = time.monotonic() + CLOSE_DRAIN_SECONDS
            remaining = CLOSE_DRAIN_BYTES
            while remaining > 0:
                timeout = deadline - time.monotonic()
                if timeout <= 0:
                    break
                request.settimeout(timeout)
                chunk = request.recv(min(1024, remaining))
                if not chunk:
                    break
                remaining -= len(chunk)
        except OSError:
            # Peer disconnect/timeout ends transport cleanup, never validation.
            pass
        finally:
            self.close_request(request)


class Handler(BaseHTTPRequestHandler):
    server: WorkbenchServer

    def setup(self):
        super().setup()
        self.connection.settimeout(5)

    def log_message(self, *_args):
        pass

    def reply(self, status, value, content_type="application/json; charset=utf-8"):
        data = value if isinstance(value, bytes) else json.dumps(value, ensure_ascii=True).encode()
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Security-Policy", "default-src 'none'; script-src 'self'; style-src 'self'; "
                         "connect-src 'self'; img-src 'self'; font-src 'self'; base-uri 'none'; frame-ancestors 'none'; form-action 'none'")
        self.send_header("Connection", "close")
        self.end_headers()
        self.wfile.write(data)
        self.close_connection = True

    def guard(self):
        hosts = self.headers.get_all("Host", [])
        origins = self.headers.get_all("Origin", [])
        if hosts != [self.server.authority] or (origins and origins != [self.server.origin]):
            self.reply(403, {"error": "Host or Origin rejected; open the printed loopback URL."})
            return False
        return True

    def do_GET(self):
        if not self.guard():
            return
        try:
            with self.server.workbench.lock:
                app = self.server.workbench
                path = self.path.split("?", 1)[0]
                if path in APP_ASSETS:
                    name, kind = APP_ASSETS[path]
                    self.reply(200, files("athena_procurement_arena").joinpath("app_assets", name).read_bytes(), kind)
                    return
                if path == "/app" or path == "/app/":
                    self.reply(200, files("athena_procurement_arena").joinpath("app_assets", "index.html").read_bytes(),
                               "text/html; charset=utf-8")
                    return
                if path == "/api/mining":
                    payload = mining_payload(app.mining, app.mining_supplier)
                    payload["withheld_synthetic"] += app.withheld_synthetic
                    self.reply(200, payload)
                    return
                if self.path == "/mining/style.css":
                    self.path = "/style.css"
                if self.path in ASSETS:
                    name, kind = ASSETS[self.path]
                    asset = files("athena_procurement_arena").joinpath("ui_assets", name)
                    if isinstance(asset, Path):
                        safe_path(asset)
                    self.reply(200, asset.read_bytes(), kind)
                elif self.path == "/mining":
                    import html
                    links = "".join(f'<li><a href="/mining/{i}">{html.escape(p["project_id"])}</a></li>'
                                    for i, p in enumerate(app.mining))
                    page = ('<html lang="en"><meta charset="utf-8"><title>Mining intelligence</title>'
                            '<link rel="stylesheet" href="/style.css"><main><a href="/">Workbench</a>'
                            '<h1>Mining intelligence</h1><p>Reviewed, source-bound opportunity reports.</p><ul>'
                            + links + '</ul><p>Import a reviewed source manifest with --mining-input PATH at startup.</p></main></html>')
                    self.reply(200, page.encode(), "text/html; charset=utf-8")
                elif self.path.startswith("/mining/"):
                    index = self.path.removeprefix("/mining/")
                    if not index.isdigit() or int(index) >= len(app.mining):
                        self.reply(404, {"error": "Unknown mining report"})
                    else:
                        self.reply(200, render_report(app.mining[int(index)], app.mining_supplier).encode(), "text/html; charset=utf-8")
                elif self.path == "/api/session":
                    self.reply(200, {"token": app.token, "cases": [
                        {"id": alias, "fixture": context["fixture"], "bundle_id": context["bundle_id"]}
                        for alias, context in app.cases.items()]})
                elif self.path == "/api/runs":
                    self.reply(200, {"runs": app.listing()})
                elif self.path.startswith("/api/runs/"):
                    run_id = self.path.removeprefix("/api/runs/")
                    app.run_path(run_id)
                    result = app.inspect(run_id)
                    self.reply(200 if result["integrity"] == "PASS" else 422, result)
                else:
                    self.reply(404, {"error": "Unknown resource"})
        except ERRORS as exc:
            self.reply(400, {"error": str(exc)})

    def do_POST(self):
        if not self.guard():
            return
        app = self.server.workbench
        tokens = self.headers.get_all("X-Trailforge-Token", [])
        if len(tokens) != 1 or not hmac.compare_digest(tokens[0].encode(), app.token.encode()):
            self.reply(403, {"error": "Mutation token rejected; reload this workbench."})
            return
        if self.headers.get_all("Content-Type", []) != ["application/json"]:
            self.reply(415, {"error": "Content-Type must be application/json"})
            return
        lengths = self.headers.get_all("Content-Length", [])
        if (self.headers.get("Transfer-Encoding") is not None or len(lengths) != 1
                or len(lengths[0]) > 4 or not lengths[0].isdigit() or not 0 < int(lengths[0]) <= MAX_BODY):
            self.reply(400, {"error": "A bounded Content-Length is required (1–4096 bytes)."})
            return
        try:
            raw = self.rfile.read(int(lengths[0]))
            if len(raw) != int(lengths[0]):
                raise ValueError("incomplete body")
            pairs = json.loads(raw, object_pairs_hook=list)
            field = {"/api/run": "case_id", "/api/replay": "run_id"}.get(self.path)
            if (field is None or not isinstance(pairs, list) or len(pairs) != 1
                    or not isinstance(pairs[0], tuple) or pairs[0][0] != field
                    or not isinstance(pairs[0][1], str)):
                raise ValueError("request must contain exactly the expected string field")
            value = pairs[0][1]
            with app.lock:
                if field == "case_id":
                    result = app.create(value)
                    self.reply(201 if result["integrity"] == "PASS" else 422, result)
                else:
                    target = app.run_path(value)
                    result = app.inspect(value)
                    if result["integrity"] == "PASS":
                        try:
                            result["replay"] = replay_experiment(target, BaselineA())
                        except ERRORS as exc:
                            result["replay"] = {"status": "FAIL", "error": str(exc)}
                        app.replays[value] = result["replay"]
                    self.reply(200 if result["integrity"] == "PASS"
                               and result["replay"]["status"] == "PASS" else 422, result)
        except ERRORS as exc:
            self.reply(400, {"error": str(exc)})


def main(argv=None):
    parser = argparse.ArgumentParser(description="Trailforge local research workbench (loopback only)")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--bundle", type=Path, action="append", help="trusted startup bundle; repeatable")
    mode.add_argument("--saved-only", action="store_true", help="inspect/replay saved runs without a bundle")
    parser.add_argument("--experiments-dir", type=Path, default=Path(".trailforge-experiments"))
    parser.add_argument("--mining-supplier", type=Path, help="optional supplier offering profile JSON")
    parser.add_argument("--mining-input", type=Path, action="append", default=[], help="reviewed mining import; repeatable")
    parser.add_argument("--no-fixture-mining", action="store_true",
                        help="do not load the checkout's real Stibnite mining import by default")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args(argv)
    if not 0 <= args.port <= 65535:
        parser.error("port must be between 0 and 65535")
    bundles = args.bundle or []
    if not bundles and not args.saved_only:
        default = Path(__file__).resolve().parents[2] / "scenarios/fixtures/verified/gt-003-morgan-hill.json"
        if not default.is_file():
            parser.error("No checkout GT-003 bundle found. Supply --bundle PATH or --saved-only.")
        bundles = [default]
    mining_inputs = default_mining_inputs() if not args.no_fixture_mining else []
    if not args.no_fixture_mining and not mining_inputs:
        print("No checkout mining imports found (run from the repository root); add projects with --mining-input PATH.",
              file=sys.stderr, flush=True)
    for path in args.mining_input:  # explicit inputs add to the defaults, never replace them
        if path.resolve() not in {p.resolve() for p in mining_inputs}:
            mining_inputs.append(path)
    app = None
    try:
        app = Workbench(args.experiments_dir, bundles, mining_inputs, args.mining_supplier)
        with WorkbenchServer(app, args.port) as server:
            print(f"Trailforge: {server.origin}/app  (research workbench: {server.origin}/)  Ctrl+C to stop", flush=True)
            server.serve_forever()
    except KeyboardInterrupt:
        pass
    except ERRORS as exc:
        parser.error(str(exc))
    finally:
        if app is not None:
            app.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
