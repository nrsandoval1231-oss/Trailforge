"""HTTP boundary and retained-engine lifecycle checks for the optional workbench."""
from __future__ import annotations

import hashlib
import http.client
import json
import socket
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from importlib.resources import files
from pathlib import Path

import pytest

from athena_procurement_arena import local_ui, runner

BUNDLE = Path(__file__).resolve().parents[2] / "scenarios/fixtures/verified/gt-003-morgan-hill.json"


@contextmanager
def serving(root, bundles):
    app = local_ui.Workbench(root, bundles)
    server = local_ui.WorkbenchServer(app, 0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield server
    finally:
        server.shutdown()
        thread.join(timeout=5)
        server.server_close()
        app.close()


def request(server, path, data=None, *, method=None, headers=None, raw=None):
    connection = http.client.HTTPConnection("127.0.0.1", server.server_port, timeout=10)
    payload = json.dumps(data).encode() if data is not None else raw
    default = {"Host": server.authority}
    if payload is not None:
        default.update({"Content-Type": "application/json", "X-Trailforge-Token": server.workbench.token})
    default.update(headers or {})
    connection.request(method or ("POST" if payload is not None else "GET"), path, payload, default)
    response = connection.getresponse()
    body = response.read()
    result = (response.status, dict(response.getheaders()),
              json.loads(body) if response.getheader("Content-Type", "").startswith("application/json") else body)
    connection.close()
    return result


def create(server):
    status, _, body = request(server, "/api/run", {"case_id": "case-1"})
    assert status == 201, body
    assert body["integrity"] == "PASS"
    return body


def fingerprint(root):
    return {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in root.iterdir() if p.is_file()}


def test_real_lifecycle_restart_without_original_bundle(tmp_path, monkeypatch):
    bundle = tmp_path / "bundle.json"
    bundle.write_bytes(BUNDLE.read_bytes())
    root = tmp_path / "runs"
    with serving(root, [bundle]) as server:
        status, headers, session = request(server, "/api/session")
        assert status == 200 and session["token"]
        assert session["cases"][0]["fixture"]["verified_by"]
        assert headers["Cache-Control"] == "no-store"
        assert "frame-ancestors 'none'" in headers["Content-Security-Policy"]
        first = create(server)
        second = create(server)
        assert first["id"] != second["id"]
        assert first["evaluation"]["scoring"] == "UNSCORED"
        assert first["evaluation"]["status"] == "UNSEALED"
        assert len(first["decisions"]["decision_snapshots"]) == 3
        assert first["input"]["fixture_context"]["bundle_text"] == bundle.read_text(encoding="utf-8")
        saved = fingerprint(root / first["id"])
    bundle.unlink()
    with serving(root, []) as server:
        assert request(server, "/api/session")[2]["cases"] == []
        with monkeypatch.context() as patch:
            def forbidden(*_args, **_kwargs):
                raise AssertionError("inspection must not execute a world or policy")
            patch.setattr(runner.TemporalWorld, "run", forbidden)
            patch.setattr(local_ui.BaselineA, "__call__", forbidden)
            assert len(request(server, "/api/runs")[2]["runs"]) == 2
            inspected = request(server, f"/api/runs/{first['id']}")[2]
            assert inspected["integrity"] == "PASS"
            assert inspected["replay"]["status"] == "NOT_RUN"
        status, _, replayed = request(server, "/api/replay", {"run_id": first["id"]})
        assert status == 200 and replayed["replay"]["status"] == "PASS"
        assert all(replayed["replay"]["checks"].values())
        assert fingerprint(root / first["id"]) == saved


def test_corrupt_and_partial_runs_fail_visibly(tmp_path):
    with serving(tmp_path, [BUNDLE]) as server:
        run = create(server)
        run_dir = tmp_path / run["id"]
        (run_dir / "decisions.json").write_text("{}")
        partial_id = uuid.uuid4().hex
        (tmp_path / partial_id).mkdir()
        status, _, result = request(server, f"/api/runs/{run['id']}")
        assert status == 422 and result["integrity"] == "FAIL"
        assert "hash mismatch" in result["error"]
        status, _, result = request(server, "/api/replay", {"run_id": run["id"]})
        assert status == 422 and result["replay"]["status"] == "NOT_RUN"
        assert all(item["integrity"] == "FAIL" for item in request(server, "/api/runs")[2]["runs"])


@pytest.mark.parametrize("headers,status", [
    ({"Host": "localhost:8765"}, 403), ({"Host": "evil.example"}, 403),
    ({"Host": "127.0.0.1"}, 403), ({"Origin": "null"}, 403),
    ({"Origin": "http://evil.example"}, 403), ({"X-Trailforge-Token": "wrong"}, 403),
    ({"X-Trailforge-Token": ""}, 403), ({"Content-Type": "text/plain"}, 415),
    ({"Content-Type": "application/json; charset=utf-8"}, 415),
    ({"Content-Length": "99999"}, 400), ({"Transfer-Encoding": "chunked"}, 400),
    ({"Content-Length": "9" * 5000}, 400),
])
def test_request_guards(tmp_path, headers, status):
    with serving(tmp_path, [BUNDLE]) as server:
        assert request(server, "/api/run", {"case_id": "case-1"}, headers=headers)[0] == status
        assert not list(tmp_path.glob("*/manifest.json"))


@pytest.mark.parametrize("raw", [b"{", b"null", b"[]", b"42", b'"case-1"',
    b'{"case_id":3}', b'{"case_id":true}', b'{"case_id":[]}', b'{"case_id":{}}',
    b'{"case_id":"case-1","path":"x"}', b'{"case_id":"case-1","case_id":"case-1"}',
    b'{"case_id":"unknown"}', b'{"run_id":"case-1"}', b'[["case_id","case-1"]]', b'\xff'])
def test_strict_body_schema(tmp_path, raw):
    with serving(tmp_path, [BUNDLE]) as server:
        assert request(server, "/api/run", raw=raw)[0] == 400
        assert not list(tmp_path.glob("*/manifest.json"))


@pytest.mark.parametrize("run_id", ["..", "../secret", "%2e%2e%2fsecret", "%252e%252e", "C:/Windows", "abc", "a" * 33])
def test_path_and_id_rejection(tmp_path, run_id):
    with serving(tmp_path, []) as server:
        assert request(server, f"/api/runs/{run_id}")[0] == 400
        assert request(server, "/api/replay", {"run_id": run_id})[0] == 400
        assert request(server, f"/{run_id}")[0] == 404


def test_static_resources_no_get_mutation_and_no_cors(tmp_path):
    with serving(tmp_path, [BUNDLE]) as server:
        for path, (name, kind) in local_ui.ASSETS.items():
            status, headers, body = request(server, path)
            assert status == 200 and headers["Content-Type"] == kind
            expected = files("athena_procurement_arena").joinpath("ui_assets", name).read_bytes()
            assert body == (json.loads(expected) if kind.startswith("application/json") else expected)
            assert "Access-Control-Allow-Origin" not in headers
            assert headers["Referrer-Policy"] == "no-referrer"
        for path in ("/api/run", "/api/replay", "/../pyproject.toml", "/%2e%2e/pyproject.toml", "/app.js?x=1"):
            assert request(server, path)[0] == 404
        assert request(server, "/api/session", headers={"Origin": "null"})[0] == 403
        assert request(server, "/api/session", headers={"Origin": server.origin})[0] == 200
        assert request(server, "/api/run", {}, method="PUT")[0] == 501
        js = files("athena_procurement_arena").joinpath("ui_assets", "app.js").read_text()
        assert "innerHTML" not in js and "insertAdjacentHTML" not in js


def test_no_overwrite_and_root_lock(tmp_path, monkeypatch):
    with serving(tmp_path, [BUNDLE]) as server:
        run = create(server)
        before = fingerprint(tmp_path / run["id"])
        monkeypatch.setattr(local_ui.uuid, "uuid4", lambda: uuid.UUID(hex=run["id"]))
        assert request(server, "/api/run", {"case_id": "case-1"})[0] == 422
        assert fingerprint(tmp_path / run["id"]) == before
        with pytest.raises(ValueError, match="already served"):
            local_ui.Workbench(tmp_path, [])


def test_create_failure_retains_partial_run(tmp_path, monkeypatch):
    def fail(_scenario, _source, path, *_args, **_kwargs):
        path.mkdir()
        raise ValueError("engine failed")
    monkeypatch.setattr(local_ui, "create_experiment", fail)
    with serving(tmp_path, [BUNDLE]) as server:
        status, _, run = request(server, "/api/run", {"case_id": "case-1"})
        assert status == 422 and "engine failed" in run["error"]
        assert request(server, "/api/runs")[2]["runs"][0]["integrity"] == "FAIL"


def test_symlink_run_rejected(tmp_path):
    outside = tmp_path / "outside"
    outside.mkdir()
    root = tmp_path / "runs"
    root.mkdir()
    run_id = uuid.uuid4().hex
    try:
        (root / run_id).symlink_to(outside, target_is_directory=True)
    except OSError:
        pytest.skip("Windows symlink privilege unavailable")
    with serving(root, []) as server:
        assert request(server, "/api/runs")[2]["runs"][0]["integrity"] == "FAIL"
        assert request(server, f"/api/runs/{run_id}")[0] == 400


def test_only_accepted_mechanics_case_is_runnable(tmp_path):
    raw = json.loads(BUNDLE.read_text())
    raw["fixtures"][0]["fixture_id"] = "SouthValley"
    bundle = tmp_path / "other.json"
    bundle.write_text(json.dumps(raw))
    with serving(tmp_path / "runs", [bundle]) as server:
        assert request(server, "/api/session")[2]["cases"] == []
        assert request(server, "/api/run", {"case_id": "SouthValley"})[0] == 400


def test_missing_explicit_bundle_has_clear_startup_error(tmp_path, capsys):
    with pytest.raises(SystemExit) as exc:
        local_ui.main(["--bundle", str(tmp_path / "missing.json"), "--experiments-dir", str(tmp_path / "runs")])
    assert exc.value.code == 2
    assert "missing.json" in capsys.readouterr().err


def test_mutations_serialized_and_distinct(tmp_path):
    with serving(tmp_path, [BUNDLE]) as server, ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(create, server) for _ in range(2)]
        runs = [future.result() for future in futures]
        assert len({run["id"] for run in runs}) == 2
        assert all(run["integrity"] == "PASS" for run in runs)


@pytest.mark.parametrize("extra,status", [
    ([("Host", "evil.example")], 403),
    ([("Origin", "null")], 403),
    ([("X-Trailforge-Token", "wrong")], 403),
    ([("Content-Length", "2")], 400),
])
def test_duplicate_security_headers_rejected(tmp_path, extra, status):
    with serving(tmp_path, []) as server:
        connection = http.client.HTTPConnection("127.0.0.1", server.server_port, timeout=10)
        connection.putrequest("POST", "/api/run", skip_host=True)
        for name, value in [("Host", server.authority), ("Origin", server.origin),
                            ("X-Trailforge-Token", server.workbench.token),
                            ("Content-Type", "application/json"), ("Content-Length", "2"), *extra]:
            connection.putheader(name, value)
        connection.endheaders(b"{}")
        response = connection.getresponse()
        assert response.status == status
        response.read()
        connection.close()


def test_missing_token_rejected(tmp_path):
    with serving(tmp_path, []) as server:
        assert request(server, "/api/run", method="POST")[0] == 403


def test_windows_reparse_point_rejected_without_symlink_privilege(tmp_path, monkeypatch):
    original = Path.lstat

    class Reparse:
        st_mode = 0
        st_file_attributes = 0x400

    def lstat(path, *args, **kwargs):
        return Reparse() if path == tmp_path else original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "lstat", lstat)
    with pytest.raises(ValueError, match="reparse"):
        local_ui.safe_path(tmp_path / "child")


def test_artifact_link_rejected(tmp_path, monkeypatch):
    with serving(tmp_path, [BUNDLE]) as server:
        run = create(server)
        original = local_ui.safe_path

        def reject(path):
            if path.name == "input.json":
                raise ValueError("symlink or reparse-point path is not allowed")
            return original(path)

        monkeypatch.setattr(local_ui, "safe_path", reject)
        assert request(server, "/api/runs")[2]["runs"][0]["integrity"] == "FAIL"
        assert request(server, "/api/replay", {"run_id": run["id"]})[0] == 400


def test_replay_failure_distinct_from_integrity(tmp_path, monkeypatch):
    with serving(tmp_path, [BUNDLE]) as server:
        run = create(server)
        monkeypatch.setattr(local_ui, "replay_experiment", lambda *_: {
            "status": "FAIL", "checks": {"source_content": False},
            "manifest_hash": run["manifest"]["manifest_hash"]})
        status, _, result = request(server, "/api/replay", {"run_id": run["id"]})
        assert status == 422 and result["integrity"] == "PASS"
        assert result["replay"]["status"] == "FAIL"
        assert request(server, f"/api/runs/{run['id']}")[2]["replay"]["status"] == "FAIL"


@pytest.mark.parametrize("framing,body,status", [
    ({"Transfer-Encoding": "chunked"}, b'13\r\n{"case_id":"case-1"}\r\n0\r\n\r\n', 400),
    ({"Transfer-Encoding": "chunked"}, b'{"case_id":"case-1"}', 400),
    ({"Transfer-Encoding": "chunked", "Content-Length": "19"}, b'{"case_id":"case-1"}', 400),
    ({"Content-Type": "text/plain", "Content-Length": "19"}, b'{"case_id":"case-1"}', 415),
])
def test_rejection_delayed_body_transport(tmp_path, monkeypatch, framing, body, status):
    """Force headers to be rejected before a complete small body reaches the socket."""
    replied = threading.Event()
    original = local_ui.Handler.reply

    def signal_reply(self, *args, **kwargs):
        original(self, *args, **kwargs)
        replied.set()

    monkeypatch.setattr(local_ui.Handler, "reply", signal_reply)
    with serving(tmp_path, []) as server:
        for _ in range(10):
            replied.clear()
            connection = http.client.HTTPConnection("127.0.0.1", server.server_port, timeout=5)
            connection.putrequest("POST", "/api/run")
            headers = {"Content-Type": "application/json", "X-Trailforge-Token": server.workbench.token}
            headers.update(framing)
            for key, value in headers.items():
                connection.putheader(key, value)
            connection.endheaders()
            assert replied.wait(5)
            # Deliberate scheduling gap, not a retry: old Windows close aborts
            # the connection when the second client send arrives after FIN.
            time.sleep(0.02)
            try:
                connection.send(body)
                response = connection.getresponse()
                assert response.status == status
                assert json.loads(response.read())["error"]
            finally:
                connection.close()
        assert not list(tmp_path.glob("*/manifest.json"))


@pytest.mark.parametrize("mode", ["bytes", "deadline", "timeout", "eof"])
def test_transport_drain_is_bounded_and_always_closes(monkeypatch, mode):
    class Transport:
        received = 0
        calls = 0
        closed = False
        now = 0.0

        def shutdown(self, how):
            assert how == socket.SHUT_WR

        def settimeout(self, timeout):
            assert 0 < timeout <= local_ui.CLOSE_DRAIN_SECONDS

        def recv(self, size):
            self.calls += 1
            assert 0 < size <= 1024
            if mode == "timeout":
                raise TimeoutError("peer does not finish")
            if mode == "eof":
                return b""
            if mode == "deadline":
                self.now += 0.1
                size = 1
            self.received += size
            return b"x" * size

        def close(self):
            self.closed = True

    transport = Transport()
    monkeypatch.setattr(local_ui.time, "monotonic", lambda: transport.now)
    server = object.__new__(local_ui.WorkbenchServer)
    server.shutdown_request(transport)
    assert transport.closed
    if mode == "bytes":
        assert transport.received == local_ui.CLOSE_DRAIN_BYTES
    elif mode == "deadline":
        assert transport.calls == 3
    else:
        assert transport.calls == 1

