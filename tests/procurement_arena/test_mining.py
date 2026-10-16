"""Acceptance and real HTTP workflow checks using only synthetic evidence."""
from __future__ import annotations

import copy
import http.client
import json
import threading
from dataclasses import replace
from pathlib import Path

import pytest

from athena_procurement_arena.local_ui import Workbench, WorkbenchServer
from athena_procurement_arena.mining import (
    REFERENCE_SUPPLIER,
    import_project,
    load_project,
    main,
    match_supplier,
    qualify,
    render_report,
)

FIXTURE = Path(__file__).resolve().parents[2] / 'scenarios/fixtures/mining/project.json'


def raw():
    return json.loads(FIXTURE.read_text())


def imported(manifest=None):
    return import_project(manifest or raw(), FIXTURE.parent)


def test_multiple_requirements_and_unknown_load_remain_researchable():
    p = imported()
    assert len({r['requirement_id'] for r in p['requirements']}) == 3
    assert [r['demand']['normal_kw']['value'] for r in p['requirements']] == [250, 2000, None]
    assert all(qualify(r)['researchable'] for r in p['requirements'])
    assert qualify(p['requirements'][2])['procurement'] == 'UNAVAILABLE'
    assert p['discovery_credit'] is False


def test_neutral_discovery_then_explicit_fuel_and_package_exclusions():
    p = imported()
    diesel, propane, awarded = p['requirements']
    assert qualify(diesel)['researchable']
    assert match_supplier(diesel)['dimensions']['fuel']['verdict'] == 'INCOMPATIBLE'
    assert match_supplier(propane)['dimensions']['fuel']['verdict'] == 'POTENTIAL'
    assert match_supplier(awarded)['verdict'] == 'DO_NOT_PURSUE'
    other = replace(REFERENCE_SUPPLIER, supplier='Synthetic diesel supplier', fuels=('diesel',))
    assert match_supplier(diesel, other)['dimensions']['fuel']['verdict'] == 'POTENTIAL'
    assert match_supplier(propane, other)['dimensions']['fuel']['verdict'] == 'INCOMPATIBLE'


def test_nameplate_never_proves_site_or_redundancy_compliance():
    req = imported()['requirements'][1]
    supplier = replace(REFERENCE_SUPPLIER, nominal_kw=100000)
    result = match_supplier(req, supplier)
    assert result['engineering_compliance'] == 'NOT_ESTABLISHED'
    assert result['dimensions']['capacity_redundancy']['verdict'] == 'UNKNOWN'
    assert result['verdict'] == 'RESEARCH_REQUIRED'


@pytest.mark.parametrize('mutation', ['missing', 'quote', 'future', 'backdated', 'private', 'rights'])
def test_evidence_and_permission_boundaries(mutation):
    m = raw()
    if mutation == 'missing':
        m['project']['name']['evidence'] = []
    elif mutation == 'quote':
        m['project']['name']['evidence'][0]['quote'] = 'invented unsupported source quote'
    elif mutation == 'future':
        m['cutoff'] = '2025-12-31T00:00:00+00:00'
    elif mutation == 'backdated':
        m['sources']['notice']['available_at'] = '2025-12-31T00:00:00+00:00'
    elif mutation == 'private':
        m['sources']['notice']['access'] = 'CUSTOMER_PRIVATE'
        m['sources']['notice']['capture_file'] = 'must-not-be-read.json'
    else:
        m['sources']['notice']['share_allowed'] = False
    with pytest.raises(ValueError):
        imported(m)


def test_all_verified_values_have_traceable_retained_captures():
    p = imported()
    def walk(node):
        if isinstance(node, dict):
            if node.get('basis') == 'VERIFIED':
                assert node['evidence']
                for evidence in node['evidence']:
                    source = next(s for s in p['sources'].values() if s['capture_hash'] == evidence['capture_hash'])
                    assert evidence['quote'] in source['content']
                    assert evidence['content_sha256'] == source['content_sha256']
            for child in node.values():
                walk(child)
        elif isinstance(node, (list, tuple)):
            for child in node:
                walk(child)
    walk(p)


def test_conflicts_preserved_not_resolved_by_import_or_matching():
    m = raw()
    a = m['requirements'][0]['demand']['normal_kw']
    b = m['requirements'][1]['demand']['normal_kw']
    m['requirements'][0]['demand']['normal_kw'] = [a, b]
    p = imported(m)
    c = p['requirements'][0]['demand']['normal_kw']
    assert c['value'] is None and c['basis'] == 'CONFLICT'
    assert [a['value'] for a in c['alternatives']] == [250, 2000]
    assert 'demand.normal_kw' in qualify(p['requirements'][0])['unknowns']
    assert 'Conflicting source value' in render_report(p)


def test_estimates_require_method_range_and_cannot_be_verified():
    m = raw()
    r = m['requirements'][0]
    c = r['demand']['normal_kw']
    c['basis'] = 'ESTIMATE'
    with pytest.raises(ValueError, match='method'):
        imported(m)
    c.update(method='Synthetic engineering estimate from stated load', range=[200, 300])
    assert imported(m)['requirements'][0]['demand']['normal_kw']['basis'] == 'ESTIMATE'
    r['status'] = 'VERIFIED'
    with pytest.raises(ValueError, match='verified requirement'):
        imported(m)


def test_dependency_hypotheses_are_specific_and_falsifiable():
    r = imported()['requirements'][1]
    q = qualify(r)
    assert len(q['hypotheses']) == 3
    assert all(h['status'] == 'HYPOTHESIS' and h['falsifier'] and h['evidence'] for h in q['hypotheses'])
    assert '2026-06-01' in q['hypotheses'][-1]['statement']
    assert r['requirement_id'] in q['hypotheses'][0]['statement']


def test_private_import_produces_no_artifact(tmp_path):
    m = raw()
    m['sources']['notice'].update(access='CUSTOMER_PRIVATE', capture_file='private.json')
    path = tmp_path / 'input.json'
    path.write_text(json.dumps(m))
    output = tmp_path / 'output'
    with pytest.raises(ValueError, match='private'):
        main(['--input', str(path), '--output', str(output)])
    assert not output.exists()
    # Committed demonstration is explicitly synthetic, not a redacted real RFQ.
    p = imported()
    assert {s['access'] for s in p['sources'].values()} == {'SYNTHETIC'}
    assert all('SYNTHETIC DEMONSTRATION' in s['content'] for s in p['sources'].values())


def test_real_import_report_and_workbench_http_end_to_end(tmp_path):
    output = tmp_path / 'output'
    assert main(['--input', str(FIXTURE), '--output', str(output)]) == 0
    report = next(output.glob('*/report.html'))
    assert 'Example Mine Operations' in report.read_text()
    assert 'DO_NOT_PURSUE' in report.read_text()
    with pytest.raises(FileExistsError):
        main(['--input', str(FIXTURE), '--output', str(output)])
    app = Workbench(tmp_path / 'workbench', [], [FIXTURE])
    server = WorkbenchServer(app, 0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        for path, expected in [('/', 'Mining intelligence reports'), ('/mining', 'synthetic-copper'),
                               ('/mining/0', 'Infrastructure dependencies &amp; falsifiable hypotheses')]:
            connection = http.client.HTTPConnection('127.0.0.1', server.server_port)
            connection.request('GET', path)
            response = connection.getresponse()
            page = response.read().decode()
            assert response.status == 200
            assert expected.replace('&amp;', '&') in page
            assert 'default-src' in response.getheader('Content-Security-Policy')
            connection.close()
    finally:
        server.shutdown()
        thread.join()
        server.server_close()
        app.close()


def test_html_escaping_and_invalid_numeric_input():
    p = copy.deepcopy(load_project(FIXTURE))
    p['project']['name']['value'] = '<script>alert(1)</script>'
    assert '<script>' not in render_report(p)
    m = raw()
    m['requirements'][0]['demand']['normal_kw']['value'] = float('nan')
    with pytest.raises(ValueError, match='numeric'):
        imported(m)


@pytest.mark.parametrize('field', ['published_at', 'first_observed_at', 'available_at'])
def test_each_evidence_clock_rejects_future(field):
    m = raw()
    m['sources']['notice'][field] = '2027-01-01T00:00:00+00:00'
    with pytest.raises(ValueError, match='future evidence'):
        imported(m)


def test_automatic_dependency_and_planned_milestone_are_not_observed_events():
    m = raw()
    r = m['requirements'][0]
    r['dependencies'] = []
    # A reviewed interpretation must still reference an exact source span.
    r['delivery']['grid_available'] = {'value': 'NO', 'evidence': r['delivery']['grid_ready_by']['evidence']}
    project = imported(m)
    hypotheses = qualify(project['requirements'][0])['hypotheses']
    assert any('Off-grid' in h['statement'] for h in hypotheses)
    assert all(h['status'] == 'HYPOTHESIS' for h in hypotheses)
    assert project['requirements'][0]['delivery']['needed_by']['value'] > project['cutoff']


def test_custom_supplier_export_and_delivery_mismatch(tmp_path):
    supplier = tmp_path / 'supplier.json'
    supplier.write_text(json.dumps({'supplier': 'Synthetic Diesel Supplier', 'offering': 'Rental',
                                    'fuels': ['diesel'], 'technologies': ['diesel generation'],
                                    'available_by': '2028-01-01T00:00:00+00:00'}))
    output = tmp_path / 'output'
    assert main(['--input', str(FIXTURE), '--output', str(output), '--supplier', str(supplier)]) == 0
    report = next(output.glob('*/report.html')).read_text()
    assert 'Synthetic Diesel Supplier' in report and 'delivery: INCOMPATIBLE' in report
    assert next(output.glob('*/supplier.json')).is_file()
    assert next(output.glob('*/style.css')).is_file()


def test_duplicate_requirements_and_unrecognized_fields_are_rejected():
    m = raw()
    m['requirements'].append(copy.deepcopy(m['requirements'][0]))
    with pytest.raises(ValueError, match='unique'):
        imported(m)
    m = raw()
    m['requirements'][0]['demand']['peak_mw'] = None
    with pytest.raises(ValueError, match='unrecognized fields'):
        imported(m)


def test_conflicting_package_is_never_open():
    m = raw()
    r = m['requirements'][0]
    r['procurement']['package_status'] = [m['requirements'][1]['procurement']['package_status'],
                                          m['requirements'][2]['procurement']['package_status']]
    req = imported(m)['requirements'][0]
    assert qualify(req)['procurement'] == 'UNCONFIRMED'
    assert match_supplier(req)['dimensions']['procurement']['verdict'] == 'UNCONFIRMED'
