"""Product API retains the mining engine's distinctions and loopback boundary."""
import http.client
import json
import threading
from pathlib import Path

from athena_procurement_arena.local_ui import Workbench, WorkbenchServer
from athena_procurement_arena.mining import match_supplier, qualify

FIXTURE = Path(__file__).resolve().parents[2] / 'scenarios/fixtures/mining/project.json'


def test_product_api_uses_real_engine_without_aggregating_phases(tmp_path):
    app = Workbench(tmp_path, [], [FIXTURE])
    server = WorkbenchServer(app, 0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        conn = http.client.HTTPConnection('127.0.0.1', server.server_port)
        conn.request('GET', '/api/mining')
        response = conn.getresponse()
        assert response.status == 200
        data = json.loads(response.read())
        p = data['projects'][0]
        assert p['project'] == json.loads(json.dumps(app.mining[0]))
        assert len(p['evaluations']) == 3
        for req, result in zip(app.mining[0]['requirements'], p['evaluations'], strict=True):
            assert result['qualification'] == json.loads(json.dumps(qualify(req)))
            assert result['match'] == json.loads(json.dumps(match_supplier(
                req, app.mining_supplier, location=app.mining[0]['project']['location']['value'])))
        assert 'total_mw' not in data
        assert next(iter(p['project']['sources'].values()))['access'] == 'SYNTHETIC'
        conn.close()
        conn = http.client.HTTPConnection('127.0.0.1', server.server_port)
        conn.request('GET', '/api/mining', headers={'Origin': 'https://example.com'})
        assert conn.getresponse().status == 403
        conn.close()
    finally:
        server.shutdown()
        server.server_close()
        app.close()
        thread.join()


def test_snapshot_retains_real_engine_results_and_discloses_provenance(tmp_path):
    import runpy

    import pytest

    script = Path(__file__).resolve().parents[2] / 'scripts/build_mining_preview.py'
    build = runpy.run_path(str(script))['build']
    output = tmp_path / 'snapshot'
    build(output, [FIXTURE])
    data = json.loads((output / 'api/mining').read_text())
    assert len(data['projects'][0]['evaluations']) == 3
    assert data['projects'][0]['evaluations'][0]['match']['verdict'] == 'DO_NOT_PURSUE'
    assert data['projects'][0]['evaluations'][1]['qualification']['procurement'] == 'OPEN'
    assert data['projects'][0]['evaluations'][2]['qualification']['procurement'] == 'UNAVAILABLE'
    assert 'Interactive snapshot' in (output / 'index.html').read_text()
    assert (output / 'mining/0/index.html').is_file()
    assert 'Synthetic' in (output / 'mining/0/index.html').read_text()
    assert (output / 'mountain.webp').stat().st_size > 0
    research = json.loads((output / 'assessments.json').read_text())
    assert research['basis'] == 'SECONDARY_RESEARCH'
    assert {a['name'] for a in research['assessments']} == {
        'Stibnite', 'Hermosa', 'Rhyolite Ridge', 'Thacker Pass', 'Eskay Creek'}
    assert all('requirements' not in a for a in research['assessments'])
    with pytest.raises(FileExistsError):
        build(output, [FIXTURE])


def test_snapshot_rejects_private_evidence_before_writing(tmp_path):
    import runpy

    import pytest

    script = Path(__file__).resolve().parents[2] / 'scripts/build_mining_preview.py'
    raw = json.loads(FIXTURE.read_text())
    next(iter(raw['sources'].values()))['access'] = 'PRIVATE'
    manifest = tmp_path / 'private.json'
    manifest.write_text(json.dumps(raw))
    output = tmp_path / 'snapshot'
    with pytest.raises(ValueError, match='private'):
        runpy.run_path(str(script))['build'](output, [manifest])
    assert not output.exists()
