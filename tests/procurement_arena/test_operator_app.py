"""Operator app (docs/UI_VISION.md Phase 1): mining API, packaged assets, Stibnite import."""
from __future__ import annotations

import http.client
import json
import threading
from contextlib import contextmanager
from pathlib import Path

import pytest

from athena_procurement_arena import local_ui
from athena_procurement_arena.mining import load_project, match_supplier, qualify

ROOT = Path(__file__).resolve().parents[2]
MINING = [ROOT / "scenarios/fixtures/mining/project.json", ROOT / "scenarios/fixtures/mining/stibnite/project.json"]


@contextmanager
def serving(root):
    app = local_ui.Workbench(root, [], MINING)
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


def get(server, path):
    connection = http.client.HTTPConnection("127.0.0.1", server.server_port, timeout=10)
    connection.request("GET", path, headers={"Host": server.authority})
    response = connection.getresponse()
    body = response.read()
    connection.close()
    return response.status, dict(response.getheaders()), body


def test_mining_api_returns_engine_verdicts_per_requirement(tmp_path):
    with serving(tmp_path) as server:
        status, headers, body = get(server, "/api/mining")
    assert status == 200 and headers["Content-Type"].startswith("application/json")
    data = json.loads(body)
    assert [p["project_id"] for p in data["projects"]] == ["stibnite"]
    assert data["withheld_synthetic"] == 1  # owner rule: synthetic data is never shown
    for project in data["projects"]:
        for req in project["requirements"]:
            assert req["qualification"] == qualify({k: v for k, v in req.items() if k not in {"qualification", "match"}})
            assert req["match"]["engineering_compliance"] == "NOT_ESTABLISHED"
    assert data["supplier"]["supplier"] == "2G Energy Rental"


@pytest.mark.parametrize("path,kind", [
    ("/app", "text/html"), ("/app/", "text/html"), ("/app/app.js", "text/javascript"),
    ("/app/app.css", "text/css"), ("/app/wordmark-white.svg", "image/svg+xml"), ("/app/Manrope.ttf", "font/ttf"),
])
def test_app_assets_are_packaged_and_csp_allows_only_self(tmp_path, path, kind):
    with serving(tmp_path) as server:
        status, headers, body = get(server, path)
    assert status == 200 and headers["Content-Type"].startswith(kind) and body
    assert "font-src 'self'" in headers["Content-Security-Policy"]
    assert "script-src 'self'" in headers["Content-Security-Policy"]


def test_explicit_inputs_add_to_defaults_and_opt_out_removes_them(tmp_path, monkeypatch):
    seen = {}

    class Stop(Exception):
        pass

    def fake_workbench(root, bundles, inputs, supplier):
        seen["inputs"] = [Path(p).resolve() for p in inputs]
        raise Stop

    monkeypatch.setattr(local_ui, "Workbench", fake_workbench)
    extra = ROOT / "scenarios/fixtures/mining/project.json"
    for argv, expected in [
        (["--saved-only", "--mining-input", str(extra)], [MINING[1].resolve(), extra.resolve()]),
        (["--saved-only", "--mining-input", str(MINING[1])], [MINING[1].resolve()]),
        (["--saved-only", "--no-fixture-mining", "--mining-input", str(extra)], [extra.resolve()]),
    ]:
        with pytest.raises(Stop):
            local_ui.main(argv)
        assert seen["inputs"] == expected


def test_default_inputs_fall_back_to_working_directory(tmp_path, monkeypatch):
    monkeypatch.setattr(local_ui, "__file__", str(tmp_path / "site-packages/pkg/local_ui.py"))
    monkeypatch.chdir(ROOT)
    assert local_ui.default_mining_inputs() == [ROOT / "scenarios/fixtures/mining/stibnite/project.json"]
    monkeypatch.chdir(tmp_path)
    assert local_ui.default_mining_inputs() == []


def test_synthetic_projects_never_reach_any_operator_page(tmp_path):
    with serving(tmp_path) as server:
        _, _, listing = get(server, "/mining")
        _, _, api = get(server, "/api/mining")
    assert b"synthetic" not in listing.lower() and b"Synthetic" not in api


def test_app_has_no_send_path_or_inline_script(tmp_path):
    with serving(tmp_path) as server:
        _, _, html = get(server, "/app")
        _, _, js = get(server, "/app/app.js")
    assert b"<script>" not in html and b"onclick=" not in html
    assert b"innerHTML" not in js and b"method: \"POST\"" not in js


def test_stibnite_import_keeps_unknowns_and_awarded_scope_separate():
    project = load_project(MINING[1])
    reqs = {r["requirement_id"]: r for r in project["requirements"]}
    camp = reqs["stibnite:construction:camp"]
    assert camp["status"] == "HYPOTHESIS"
    assert camp["demand"]["normal_kw"]["basis"] == "UNKNOWN"  # no invented MW
    assert match_supplier(camp)["verdict"] == "RESEARCH_REQUIRED"
    powerline = reqs["stibnite:construction:powerline-materials"]
    assert qualify(powerline)["procurement"] == "UNAVAILABLE"
    assert match_supplier(powerline)["verdict"] == "DO_NOT_PURSUE"
    assert "pending" in project["reviewed_by"]
    assert {s["access"] for s in project["sources"].values()} == {"PUBLIC"}
