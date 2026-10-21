"""Local, persistent project and customer operator desk."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import secrets
import sqlite3
import stat
import threading
from datetime import UTC, datetime, timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from importlib.resources import files
from pathlib import Path
from urllib.parse import urlsplit

from .discovery import Discovery

# Updates resend the whole append-only dossier, so the bound must fit a grown project file
# (evidence excerpts alone may be 12,000 characters each). Still bounded; loopback + token only.
MAX_BODY = 8 * 1024 * 1024
ID = re.compile(r"[0-9a-f]{32}\Z")
CLAIMS = {"project", "scope", "required_mw", "supply_status", "timing", "duration", "site_constraints", "fuel", "buyer"}
ROLES = {"OWNER", "DEVELOPER", "EPC", "BUYER", "UTILITY", "ENGINEER", "OTHER"}
ASSETS = {
    "/": ("index.html", "text/html; charset=utf-8"),
    "/app.js": ("app.js", "text/javascript; charset=utf-8"),
    "/style.css": ("style.css", "text/css; charset=utf-8"),
}


def safe_store_path(path: Path) -> Path:
    path = path.absolute()
    for item in (*reversed(path.parents), path):
        try:
            info = item.lstat()
        except FileNotFoundError:
            continue
        if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
            raise ValueError("operator storage path cannot include links or reparse points")
    return path


def now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def aware_timestamp(value: str) -> bool:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed.tzinfo is not None and parsed.utcoffset() is not None
    except (ValueError, TypeError):
        return False


FUTURE_SKEW = timedelta(minutes=5)


def not_future(value: str) -> bool:
    """Evidence and interactions cannot be dated after the moment they are recorded."""
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return parsed <= datetime.now(UTC) + FUTURE_SKEW


def traceable_source_url(value: str) -> bool:
    if not isinstance(value, str) or value != value.strip() or any(ch.isspace() for ch in value):
        return False
    try:
        parsed = urlsplit(value)
        port = parsed.port
        return (
            parsed.scheme in {"http", "https"}
            and bool(parsed.hostname)
            and not parsed.username
            and not parsed.password
            and (port is None or 0 <= port <= 65535)
        )
    except ValueError:
        return False


def _json(raw: str):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError(f"duplicate JSON key: {key}")
            result[key] = value
        return result

    return json.loads(raw, object_pairs_hook=pairs)


def validate_doc(doc: object) -> dict:
    if not isinstance(doc, dict) or set(doc) != {
        "id",
        "version",
        "name",
        "location",
        "phase",
        "summary",
        "evidence",
        "organizations",
        "people",
        "brief",
        "interactions",
        "fuel",
    }:
        raise ValueError("project document has an invalid schema")
    if not isinstance(doc["id"], str) or not ID.fullmatch(doc["id"]):
        raise ValueError("invalid project ID")
    if not isinstance(doc["version"], int) or doc["version"] < 1:
        raise ValueError("invalid project version")
    for key in ("name", "location", "phase", "summary", "brief"):
        if not isinstance(doc[key], str) or len(doc[key]) > 4000:
            raise ValueError(f"{key} must be text up to 4000 characters")
    for key in ("evidence", "organizations", "people", "interactions"):
        if not isinstance(doc[key], list) or len(doc[key]) > 500:
            raise ValueError(f"{key} must be a bounded list")
    if (
        not isinstance(doc["fuel"], dict)
        or set(doc["fuel"]) != {"status", "notes"}
        or doc["fuel"]["status"] not in {"NOT_STARTED", "PLANNING", "COORDINATING"}
        or not isinstance(doc["fuel"]["notes"], str)
    ):
        raise ValueError("fuel record has an invalid schema")
    seen_evidence = {}
    for evidence in doc["evidence"]:
        if not isinstance(evidence, dict) or set(evidence) != {
            "id",
            "claim",
            "value",
            "source_url",
            "excerpt",
            "source_date",
            "observed_at",
            "reviewer",
            "review_status",
            "sha256",
            "supersedes",
        }:
            raise ValueError("evidence record has an invalid schema")
        if not isinstance(evidence["id"], str) or not ID.fullmatch(evidence["id"]):
            raise ValueError("invalid evidence ID")
        if not isinstance(evidence["supersedes"], list) or any(not isinstance(x, str) for x in evidence["supersedes"]):
            raise ValueError("corrections require superseded evidence IDs")
        if evidence["id"] in seen_evidence or any(
            x not in seen_evidence or seen_evidence[x]["claim"] != evidence["claim"] for x in evidence["supersedes"]
        ):
            raise ValueError("correction must reference earlier evidence for the same claim")
        if any(
            not isinstance(evidence[k], str)
            for k in (
                "claim",
                "value",
                "source_url",
                "excerpt",
                "source_date",
                "observed_at",
                "reviewer",
                "review_status",
                "sha256",
            )
        ):
            raise ValueError("evidence fields must be text")
        if evidence["claim"] not in CLAIMS or evidence["review_status"] not in {"UNKNOWN", "REVIEWED", "CONTRADICTED"}:
            raise ValueError("evidence claim or review status is invalid")
        if (
            not isinstance(evidence["value"], str)
            or len(evidence["value"]) > 4000
            or not isinstance(evidence["excerpt"], str)
            or len(evidence["excerpt"]) > 12000
        ):
            raise ValueError("evidence value or excerpt is too long")
        expected = hashlib.sha256(evidence["excerpt"].encode()).hexdigest()
        if evidence["sha256"] != expected:
            raise ValueError("evidence excerpt hash mismatch")
        if not aware_timestamp(evidence["observed_at"]):
            raise ValueError("evidence observed time must be an ISO timestamp with timezone")
        if not not_future(evidence["observed_at"]):
            raise ValueError("evidence observed time cannot be in the future")
        if evidence["review_status"] == "REVIEWED" and (
            not evidence["reviewer"].strip() or not evidence["excerpt"].strip()
        ):
            raise ValueError("reviewed evidence requires an excerpt and named reviewer")
        if evidence["review_status"] == "REVIEWED" and evidence["claim"] in {"scope", "buyer"} and not traceable_source_url(evidence["source_url"]):
            raise ValueError("reviewed scope and buyer evidence require a traceable HTTP or HTTPS source URL")
        if evidence["source_url"] and not traceable_source_url(evidence["source_url"]):
            raise ValueError("source URL must use HTTP or HTTPS")
        seen_evidence[evidence["id"]] = evidence
    for person in doc["people"]:
        if (
            not isinstance(person, dict)
            or set(person) != {"name", "organization", "role", "source_evidence", "contact_route"}
            or person["role"] not in ROLES
        ):
            raise ValueError("person record has an invalid schema")
        if any(not isinstance(person[k], str) for k in person):
            raise ValueError("person fields must be text")
    for organization in doc["organizations"]:
        if (
            not isinstance(organization, dict)
            or set(organization) != {"name", "role", "source_evidence"}
            or organization["role"] not in ROLES
        ):
            raise ValueError("organization record has an invalid schema")
        if any(not isinstance(organization[k], str) for k in organization):
            raise ValueError("organization fields must be text")
    for interaction in doc["interactions"]:
        if (
            not isinstance(interaction, dict)
            or set(interaction)
            != {
                "occurred_at",
                "person",
                "notes",
                "needs_understood",
                "learned_mw",
                "timing",
                "duration",
                "site_constraints",
            }
            or not isinstance(interaction["needs_understood"], bool)
        ):
            raise ValueError("interaction record has an invalid schema")
        if any(
            not isinstance(interaction[k], str)
            for k in ("occurred_at", "person", "notes", "learned_mw", "timing", "duration", "site_constraints")
        ):
            raise ValueError("interaction fields must be text")
        if not aware_timestamp(interaction["occurred_at"]):
            raise ValueError("conversation time must be an ISO timestamp with timezone")
        occurred_at = datetime.fromisoformat(interaction["occurred_at"].replace("Z", "+00:00"))
        if occurred_at.astimezone(UTC) > datetime.now(UTC):
            raise ValueError("conversation time cannot be in the future")
        if interaction["needs_understood"]:
            try:
                mw = float(interaction["learned_mw"])
            except ValueError as exc:
                raise ValueError("understood need requires a positive numeric MW value") from exc
            if (
                not math.isfinite(mw)
                or mw <= 0
                or any(
                    interaction[k].strip().casefold() in {"", "unknown", "n/a", "none"}
                    for k in ("timing", "duration", "site_constraints")
                )
            ):
                raise ValueError("understood need requires MW, timing, duration, and site constraints")
    evidence_ids = {e["id"] for e in doc["evidence"]}
    for relation in [*doc["people"], *doc["organizations"]]:
        if relation["source_evidence"] and relation["source_evidence"] not in evidence_ids:
            raise ValueError("relationship evidence reference does not exist")
    return doc


def gate(doc: dict) -> dict:
    claims = {}
    superseded = {evidence_id for item in doc["evidence"] for evidence_id in item["supersedes"]}
    for item in doc["evidence"]:
        if item["id"] in superseded:
            continue
        if item["review_status"] == "CONTRADICTED":
            claims[item["claim"]] = "CONTRADICTED"
        elif item["review_status"] == "REVIEWED":
            if item["claim"] in {"scope", "buyer"} and not traceable_source_url(item["source_url"]):
                continue
            if item["claim"] != "scope" and item["value"].strip().casefold() in {
                "",
                "unknown",
                "n/a",
                "none",
                "not known",
            }:
                continue
            prior = claims.get(item["claim"])
            if prior == "CONTRADICTED":
                continue
            if prior is None:
                claims[item["claim"]] = {item["value"].strip().casefold()}
            elif isinstance(prior, set):
                prior.add(item["value"].strip().casefold())

    def value(key):
        found = claims.get(key)
        return next(iter(found)) if isinstance(found, set) and len(found) == 1 else None

    scope = value("scope")
    supported_scopes = {
        "temporary power",
        "temporary",
        "bridge power",
        "bridge",
        "commissioning power",
        "commissioning",
    }
    scope_state = claims.get("scope")
    active_scope = [e for e in doc["evidence"] if e["claim"] == "scope" and e["id"] not in superseded]
    scope_sources_valid = all(
        e["review_status"] != "REVIEWED" or traceable_source_url(e["source_url"]) for e in active_scope
    )
    need_verified = bool(scope_sources_valid and scope and scope in supported_scopes and scope_state != "CONTRADICTED")
    active_buyer = [e for e in doc["evidence"] if e["claim"] == "buyer" and e["id"] not in superseded]
    buyer_values = {e["value"].strip().casefold() for e in active_buyer if e["review_status"] == "REVIEWED"}
    buyer_reviewed = (
        bool(active_buyer)
        and all(e["review_status"] == "REVIEWED" for e in active_buyer)
        and all(traceable_source_url(e["source_url"]) for e in active_buyer)
        and len(buyer_values) == 1
        and next(iter(buyer_values)) not in {"", "unknown", "n/a", "none", "not known"}
    )
    evidence_ids = {e["id"] for e in active_buyer} if buyer_reviewed else set()
    buyer_known = any(p["role"] == "BUYER" and p["source_evidence"] in evidence_ids for p in doc["people"])
    contact_names = {
        p["name"].strip().casefold()
        for p in doc["people"]
        if p["role"] == "BUYER" and p["name"].strip() and p["source_evidence"] in evidence_ids
    }
    understood = any(
        i["needs_understood"]
        and aware_timestamp(i["occurred_at"])
        and i["person"].strip().casefold() in contact_names
        and i["learned_mw"].strip().casefold() not in {"", "unknown", "n/a", "none"}
        and math.isfinite(float(i["learned_mw"]))
        and float(i["learned_mw"]) > 0
        and all(
            i[k].strip().casefold() not in {"", "unknown", "n/a", "none"}
            for k in ("learned_mw", "timing", "duration", "site_constraints")
        )
        for i in doc["interactions"]
    )
    claim_states = {
        k: (
            "CONTRADICTED"
            if v == "CONTRADICTED" or isinstance(v, set) and len(v) > 1
            else "VERIFIED"
            if isinstance(v, set) and len(v) == 1
            else "UNKNOWN"
        )
        for k, v in claims.items()
    }
    for item in doc["evidence"]:
        claim_states.setdefault(item["claim"], "UNKNOWN")
    return {
        "need": "VERIFIED" if need_verified else "UNKNOWN",
        "buyer": "KNOWN" if buyer_known else "UNKNOWN",
        "conversation": "RECORDED" if doc["interactions"] else "NONE",
        "fuel_unlocked": bool(need_verified and understood),
        "claims": claim_states,
    }


class Store:
    def __init__(self, path: Path):
        self.path = safe_store_path(path.expanduser())
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.lock = threading.RLock()
        self.db = sqlite3.connect(self.path, check_same_thread=False, isolation_level=None)
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.execute("PRAGMA foreign_keys=ON")
        with self.db:
            self.db.execute("CREATE TABLE IF NOT EXISTS metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
            self.db.execute(
                "CREATE TABLE IF NOT EXISTS projects (id TEXT PRIMARY KEY, version INTEGER NOT NULL, payload TEXT NOT NULL)"
            )
            row = self.db.execute("SELECT value FROM metadata WHERE key='schema_version'").fetchone()
            if row is None:
                self.db.execute("INSERT INTO metadata VALUES ('schema_version','1')")
            elif row[0] not in {"1", "2"}:
                raise ValueError(f"unsupported operator database schema version: {row[0]}")
            self.db.execute(
                "CREATE TABLE IF NOT EXISTS discovery_candidates (candidate_id TEXT PRIMARY KEY, source_id TEXT NOT NULL, title TEXT NOT NULL, url TEXT NOT NULL UNIQUE, source_date TEXT NOT NULL, first_seen TEXT NOT NULL, snapshot_hash TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'PENDING_REVIEW', project_id TEXT, FOREIGN KEY(project_id) REFERENCES projects(id))"
            )
            self.db.execute(
                "CREATE TABLE IF NOT EXISTS discovery_checks (source_id TEXT PRIMARY KEY, checked_at TEXT NOT NULL, last_success TEXT NOT NULL, error TEXT NOT NULL, fetched_count INTEGER NOT NULL, eligible_count INTEGER NOT NULL, excluded_count INTEGER NOT NULL)"
            )
            self.db.execute("UPDATE metadata SET value='2' WHERE key='schema_version'")
        self.discovery = Discovery(self)

    def listing(self):
        with self.lock:
            result = []
            for project_id, version, payload in self.db.execute("SELECT id,version,payload FROM projects ORDER BY id"):
                try:
                    doc = validate_doc(_json(payload))
                    result.append(
                        {
                            "id": project_id,
                            "version": version,
                            "name": doc["name"],
                            "location": doc["location"],
                            "phase": doc["phase"],
                            "gate": gate(doc),
                            "integrity": "PASS",
                        }
                    )
                except (ValueError, TypeError, KeyError, json.JSONDecodeError) as exc:
                    result.append(
                        {
                            "id": project_id,
                            "version": version,
                            "name": "Unreadable project",
                            "integrity": "FAIL",
                            "error": str(exc),
                        }
                    )
            return result

    def get(self, project_id: str):
        if not ID.fullmatch(project_id):
            raise ValueError("invalid project ID")
        with self.lock:
            row = self.db.execute("SELECT payload FROM projects WHERE id=?", (project_id,)).fetchone()
            if row is None:
                raise KeyError("project not found")
            doc = validate_doc(_json(row[0]))
            return {
                **doc,
                "gate": gate(doc),
                "_history_lengths": {k: len(doc[k]) for k in ("evidence", "organizations", "people", "interactions")},
            }

    def save(self, doc: dict):
        doc = dict(doc)
        doc.pop("gate", None)
        doc.pop("_history_lengths", None)
        for item in doc.get("evidence", []):
            item["sha256"] = hashlib.sha256(item["excerpt"].encode()).hexdigest()
        validate_doc(doc)
        with self.lock:
            self.db.execute("BEGIN IMMEDIATE")
            try:
                row = self.db.execute("SELECT version,payload FROM projects WHERE id=?", (doc["id"],)).fetchone()
                expected = doc["version"] - 1
                if (row[0] if row else 0) != expected:
                    raise ValueError("STALE_VERSION: reload this project before saving")
                if row:
                    previous = validate_doc(_json(row[1]))
                    current_gate = gate(doc)
                    if doc["fuel"]["status"] != "NOT_STARTED" and not current_gate["fuel_unlocked"]:
                        raise ValueError(
                            "fuel coordination is locked until the reviewed need and understood conversation are complete"
                        )
                    if (
                        not current_gate["fuel_unlocked"]
                        and doc["fuel"]["notes"]
                        and (
                            doc["fuel"]["notes"] != previous["fuel"]["notes"]
                            or not previous["fuel"]["notes"]
                        )
                    ):
                        raise ValueError("new or changed fuel notes are locked until the gate is unlocked")
                    for key in ("evidence", "organizations", "people", "interactions"):
                        if doc[key][: len(previous[key])] != previous[key]:
                            raise ValueError(f"{key} history is append-only; add a correction record")
                elif doc["fuel"]["status"] != "NOT_STARTED" and not gate(doc)["fuel_unlocked"]:
                    raise ValueError(
                        "fuel coordination is locked until the reviewed need and understood conversation are complete"
                    )
                elif doc["fuel"]["notes"] and not gate(doc)["fuel_unlocked"]:
                    raise ValueError("new or changed fuel notes are locked until the gate is unlocked")
                payload = json.dumps(doc, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
                self.db.execute(
                    "INSERT INTO projects VALUES (?,?,?) ON CONFLICT(id) DO UPDATE SET version=excluded.version,payload=excluded.payload",
                    (doc["id"], doc["version"], payload),
                )
                self.db.execute("COMMIT")
            except Exception:
                self.db.execute("ROLLBACK")
                raise
        return self.get(doc["id"])

    def close(self):
        self.db.close()


def blank(name: str, location: str, phase: str):
    return {
        "id": secrets.token_hex(16),
        "version": 1,
        "name": name,
        "location": location,
        "phase": phase,
        "summary": "",
        "evidence": [],
        "organizations": [],
        "people": [],
        "brief": "",
        "interactions": [],
        "fuel": {"status": "NOT_STARTED", "notes": ""},
    }


class Server(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, store: Store, port: int):
        self.store, self.token = store, secrets.token_urlsafe(32)
        super().__init__(("127.0.0.1", port), Handler)
        self.authority = f"127.0.0.1:{self.server_port}"
        self.origin = f"http://{self.authority}"


class Handler(BaseHTTPRequestHandler):
    server: Server

    def setup(self):
        super().setup()
        self.connection.settimeout(5)

    def log_message(self, *_args):
        pass

    def reply(self, status, value, kind="application/json; charset=utf-8"):
        body = value if isinstance(value, bytes) else json.dumps(value, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", kind)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header(
            "Content-Security-Policy",
            "default-src 'none'; script-src 'self'; style-src 'self'; connect-src 'self'; base-uri 'none'; frame-ancestors 'none'; form-action 'none'",
        )
        self.end_headers()
        self.wfile.write(body)

    def valid_host(self):
        origins = self.headers.get_all("Origin", [])
        return self.headers.get_all("Host", []) == [self.server.authority] and (
            not origins or origins == [self.server.origin]
        )

    def do_GET(self):
        if not self.valid_host():
            return self.reply(403, {"error": "Host or Origin rejected"})
        if self.path in ASSETS:
            name, kind = ASSETS[self.path]
            return self.reply(
                200, files("athena_procurement_arena").joinpath("operator_assets", name).read_bytes(), kind
            )
        if self.path == "/api/session":
            return self.reply(200, {"token": self.server.token})
        if self.path == "/api/projects":
            return self.reply(200, {"projects": self.server.store.listing()})
        if self.path.startswith("/api/discovery"):
            from urllib.parse import parse_qs

            query = parse_qs(urlsplit(self.path).query)
            search = query.get("search", [""])[0][:250]
            return self.reply(200, self.server.store.discovery.listing(search))
        if self.path.startswith("/api/projects/"):
            try:
                suffix = self.path.removeprefix("/api/projects/")
                if suffix.endswith("/export"):
                    project = self.server.store.get(suffix.removesuffix("/export"))
                    project.pop("gate", None)
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json; charset=utf-8")
                    self.send_header(
                        "Content-Disposition", f"attachment; filename=trailforge-project-{project['id']}.json"
                    )
                    body = json.dumps(project, ensure_ascii=False, indent=2).encode()
                    self.send_header("Content-Length", str(len(body)))
                    self.send_header("Cache-Control", "no-store")
                    self.end_headers()
                    self.wfile.write(body)
                    return
                return self.reply(200, self.server.store.get(suffix))
            except (ValueError, KeyError, TypeError) as exc:
                return self.reply(404, {"error": str(exc)})
        return self.reply(404, {"error": "Unknown resource"})

    def do_POST(self):
        if not self.valid_host():
            return self.reply(403, {"error": "Host or Origin rejected"})
        if self.headers.get_all("X-Operator-Token", []) != [self.server.token]:
            return self.reply(403, {"error": "Mutation token rejected; reload the desk"})
        lengths = self.headers.get_all("Content-Length", [])
        if (
            self.headers.get("Transfer-Encoding")
            or self.headers.get_all("Content-Type", []) != ["application/json"]
            or len(lengths) != 1
            or not lengths[0].isdigit()
            or not 1 <= int(lengths[0]) <= MAX_BODY
        ):
            return self.reply(400, {"error": "A bounded JSON body is required"})
        try:
            doc = _json(self.rfile.read(int(lengths[0])).decode("utf-8"))
            if self.path == "/api/discovery/check":
                if doc != {}:
                    raise ValueError("discovery check accepts only an empty object")
                return self.reply(200, self.server.store.discovery.check())
            elif self.path.startswith("/api/discovery/") and self.path.endswith("/admit"):
                if not isinstance(doc, dict) or set(doc) != {"name", "location", "phase"} or not all(isinstance(doc[k], str) for k in doc):
                    raise ValueError("admission needs name, location, and phase")
                candidate_id = self.path.removeprefix("/api/discovery/").removesuffix("/admit")
                result, repeated = self.server.store.discovery.admit(candidate_id, doc["name"], doc["location"], doc["phase"])
                return self.reply(200 if repeated else 201, result)
            elif self.path.startswith("/api/discovery/"):
                if not isinstance(doc, dict) or set(doc) != {"status"}:
                    raise ValueError("candidate update needs status")
                candidate_id = self.path.removeprefix("/api/discovery/")
                self.server.store.discovery.set_status(candidate_id, doc["status"])
                return self.reply(200, {"ok": True})
            elif self.path == "/api/projects":
                if not isinstance(doc, dict) or set(doc) != {"name", "location", "phase"}:
                    raise ValueError("new project needs name, location, and phase")
                key = (doc["name"].strip().casefold(), doc["location"].strip().casefold())
                for item in self.server.store.listing():
                    if (
                        item["integrity"] == "PASS"
                        and (item["name"].strip().casefold(), item["location"].strip().casefold()) == key
                    ):
                        raise ValueError(f"possible duplicate project: {item['id']}")
                result = self.server.store.save(blank(doc["name"], doc["location"], doc["phase"]))
            elif self.path.startswith("/api/projects/"):
                if not isinstance(doc, dict):
                    raise ValueError("project document must be an object")
                project_id = self.path.removeprefix("/api/projects/")
                if doc.get("id") != project_id:
                    raise ValueError("project URL and document ID do not match")
                old = self.server.store.get(project_id)
                old.pop("gate", None)
                for key in ("evidence", "organizations", "people", "interactions"):
                    history = old[key]
                    if doc.get(key, [])[: len(history)] != history:
                        raise ValueError(f"{key} history is append-only; add a correction record")
                result = self.server.store.save(doc)
            else:
                return self.reply(404, {"error": "Unknown resource"})
            return self.reply(201, result)
        except (ValueError, TypeError, KeyError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            status = 409 if str(exc).startswith("STALE_VERSION") else 400
            return self.reply(status, {"error": str(exc)})

    def do_OPTIONS(self):
        self.reply(405, {"error": "Method not allowed"})


def main(argv=None):
    parser = argparse.ArgumentParser(description="Trailforge local project and customer operator desk")
    parser.add_argument("--data", type=Path, default=Path(".trailforge-operator.sqlite3"))
    parser.add_argument("--port", type=int, default=8766)
    args = parser.parse_args(argv)
    if not 0 <= args.port <= 65535:
        parser.error("port must be between 0 and 65535")
    store = Store(args.data)
    try:
        with Server(store, args.port) as server:
            print(f"Trailforge project desk: {server.origin}/ (Ctrl+C to stop)", flush=True)
            server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        store.close()


if __name__ == "__main__":
    raise SystemExit(main())
