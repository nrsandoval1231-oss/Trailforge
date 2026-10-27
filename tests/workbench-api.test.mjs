import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtemp, readFile, writeFile, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { startServer } from '../workbench/server.mjs';

async function call(app, method, path, body) {
  const response = await fetch(app.url + path, { method, headers: body === undefined ? {} : { 'Content-Type': 'application/json; charset=utf-8' }, body: body === undefined ? undefined : JSON.stringify(body) });
  return { status: response.status, headers: response.headers, body: await response.json() };
}
function proof(id, day, extra = {}) {
  const time = `${day}T00:00:00Z`;
  return { id, signalType: 'PERMIT_APPROVED', title: `Test-only ${id}`, sourceUrl: 'https://example.org/test', excerpt: `Test-only source for ${id}.`, quote: `source for ${id}`, eventAt: time, documentAt: time, availableAt: time, availabilityStatus: 'ATTESTED', reviewer: 'Test reviewer', proofUrl: 'https://example.org/proof', availabilityNote: 'Synthetic acceptance-test evidence only.', claims: {}, ...extra };
}

test('HTTP project/evidence/report lifecycle preserves frozen results across edits, archives, and restart', async () => {
  const directory = await mkdtemp(join(tmpdir(), 'trailforge-api-'));
  let app;
  try {
    app = await startServer({ port: 0, dataDir: directory });
    assert.match(app.url, /^http:\/\/127\.0\.0\.1:\d+$/);
    assert.deepEqual((await call(app, 'GET', '/api/projects')).body.projects, []);
    assert.deepEqual((await call(app, 'GET', '/api/reports')).body.reports, []);
    let response = await call(app, 'POST', '/api/projects', { id: 'api-project', name: 'Test mine chronology', location: 'Test region', notes: 'Initial review' });
    assert.equal(response.status, 201);
    assert.match(response.headers.get('cache-control'), /no-store/);
    let project = response.body.project;
    assert.equal(project.revision, 1);
    response = await call(app, 'PATCH', '/api/projects/api-project', { revision: 1, notes: 'Inspect the primary source' });
    assert.equal(response.status, 200);
    project = response.body.project;
    assert.equal(project.revision, 2);
    assert.equal((await call(app, 'PATCH', '/api/projects/api-project', { revision: 1, notes: 'Stale' })).status, 409);
    assert.equal((await call(app, 'GET', '/api/projects?q=PRIMARY')).body.projects.length, 1);
    assert.deepEqual((await call(app, 'GET', '/api/projects?q=no-such-project')).body.projects, []);
    response = await call(app, 'POST', '/api/projects/api-project/evidence', { revision: 2, ...proof('early', '2025-01-01', { claims: { project_specific: true, generation_need_supported: true, need_reason: 'Test construction continuity', buyer_organization: 'Test owner' } }) });
    assert.equal(response.status, 201);
    assert.equal(response.body.project.revision, 3);
    response = await call(app, 'POST', '/api/projects/api-project/evidence', { revision: 3, ...proof('target', '2025-02-01', { signalType: 'PROCUREMENT_SIGNAL' }) });
    assert.equal(response.status, 201);
    assert.equal(response.body.project.evidence.length, 2);
    response = await call(app, 'POST', '/api/reports', { id: 'api-report', name: 'Test cohort', projectIds: ['api-project'] });
    assert.equal(response.status, 201);
    const frozen = response.body.report;
    assert.equal(frozen.cases[0].leadDays, 31);
    assert.equal(frozen.summary.projectCount, 1);
    assert.equal((await call(app, 'POST', '/api/reports/api-report/replay', {})).body.replay, 'PASS');
    response = await call(app, 'GET', '/api/reports/api-report/export');
    assert.equal(response.status, 200);
    assert.match(response.headers.get('content-disposition'), /attachment/);
    assert.deepEqual(response.body, frozen);
    response = await call(app, 'PATCH', '/api/projects/api-project', { revision: 4, name: 'Renamed test mine' });
    assert.equal(response.status, 200);
    assert.equal((await call(app, 'DELETE', '/api/projects/api-project', { revision: 5 })).status, 200);
    assert.deepEqual((await call(app, 'GET', '/api/projects')).body.projects, []);
    assert.equal((await call(app, 'GET', '/api/projects?includeArchived=true')).body.projects[0].archived, true);
    assert.deepEqual((await call(app, 'GET', '/api/reports/api-report')).body.report, frozen);
    assert.equal((await call(app, 'POST', '/api/reports', { name: 'Archived selection', projectIds: ['api-project'] })).status, 400);
    await app.close();
    app = await startServer({ port: 0, dataDir: directory });
    const retained = await call(app, 'GET', '/api/reports/api-report');
    assert.equal(retained.status, 200);
    assert.deepEqual(retained.body.report, frozen);
    assert.equal(retained.body.verification.integrity, 'PASS');
    assert.equal((await call(app, 'POST', '/api/reports/api-report/replay', {})).body.replay, 'PASS');
    const archived = (await call(app, 'GET', '/api/projects/api-project')).body.project;
    assert.equal(archived.evidence.length, 2);
    assert.equal(archived.name, 'Renamed test mine');
    assert.equal(archived.archived, true);
    assert.equal((await call(app, 'PATCH', '/api/projects/api-project', { revision: archived.revision, archived: false })).status, 200);
    assert.equal((await call(app, 'GET', '/api/projects')).body.projects.length, 1);
  } finally {
    if (app) await app.close();
    await rm(directory, { recursive: true, force: true });
  }
});

test('HTTP validation and imports do not promote unknowns or commit failed writes', async () => {
  const directory = await mkdtemp(join(tmpdir(), 'trailforge-errors-'));
  let app;
  try {
    app = await startServer({ port: 0, dataDir: directory });
    assert.equal((await call(app, 'POST', '/api/projects', { name: '   ' })).status, 400);
    assert.equal((await call(app, 'POST', '/api/projects', { id: '../bad', name: 'Bad path' })).status, 400);
    const created = await call(app, 'POST', '/api/projects', { id: 'unknown', name: 'Unreviewed test project' });
    assert.equal(created.status, 201);
    assert.equal((await call(app, 'POST', '/api/projects', { id: 'unknown', name: 'Duplicate' })).status, 409);
    const invalid = await call(app, 'POST', '/api/projects/unknown/evidence', { revision: 1, ...proof('bad-quote', '2025-01-01', { quote: 'invented absent words' }) });
    assert.equal(invalid.status, 400);
    assert.ok(invalid.body.error);
    assert.equal((await call(app, 'GET', '/api/projects/unknown')).body.project.revision, 1);
    const accepted = await call(app, 'POST', '/api/projects/unknown/evidence', { revision: 1, id: 'unreviewed', signalType: 'PROJECT_ANNOUNCED', title: 'Unreviewed test reference', sourceUrl: 'https://example.org/reference', excerpt: 'Literal unreviewed reference.', quote: 'unreviewed reference' });
    assert.equal(accepted.status, 201);
    const report = await call(app, 'POST', '/api/reports', { id: 'unknown-report', name: 'Unknown availability', projectIds: ['unknown'] });
    assert.equal(report.status, 201);
    assert.equal(report.body.report.cases[0].leadDays, null);
    assert.equal(report.body.report.cases[0].status, 'UNKNOWN_AVAILABILITY');
    assert.equal((await call(app, 'POST', '/api/reports', { name: 'Empty', projectIds: [] })).status, 400);
    assert.equal((await call(app, 'POST', '/api/reports', { name: 'Duplicates', projectIds: ['unknown', 'unknown'] })).status, 400);
    for (const path of ['/api/projects/missing', '/api/reports/missing', '/api/not-a-route']) {
      const missing = await call(app, 'GET', path);
      assert.equal(missing.status, 404);
      assert.ok(missing.body.error);
    }
    const raw = await fetch(app.url + '/api/projects', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: '{bad' });
    assert.equal(raw.status, 400);
    const oversized = await fetch(app.url + '/api/projects', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ name: 'Oversized', notes: 'x'.repeat(270000) }) });
    assert.equal(oversized.status, 413);
    const crossOrigin = await fetch(app.url + '/api/projects', { method: 'POST', headers: { 'Content-Type': 'application/json', Origin: 'https://example.org' }, body: JSON.stringify({ name: 'Cross origin' }) });
    assert.equal(crossOrigin.status, 403);
    const trace = { schema_version: 'trailforge-project-trace-v1', project_id: 'test-legacy', trace_hash: 'a'.repeat(64), signals: [{ signal_id: 'legacy-1', project_id: 'test-legacy', observed_at: '2025-01-01T00:00:00Z', signal_type: 'PERMIT_FILED', title: 'Test legacy reference', evidence_class: 'PUBLIC', source_sha256: 'b'.repeat(64), source_url: 'https://example.org/legacy', source_quote: 'Retained legacy quote', claims: {} }] };
    const imported = await call(app, 'POST', '/api/imports/traces', { id: 'legacy', name: 'Legacy reference', trace });
    assert.equal(imported.status, 201);
    assert.deepEqual(imported.body.project.evidence, []);
    assert.equal(imported.body.project.importContext.verification, 'NOT_AUTHENTICATED');
    assert.deepEqual(imported.body.project.importContext.original, trace);
    assert.equal((await call(app, 'GET', '/api/projects')).body.projects.length, 2);
  } finally {
    if (app) await app.close();
    await rm(directory, { recursive: true, force: true });
  }
});

test('tampered reports remain visible as failed and cannot be exported as healthy', async () => {
  const directory = await mkdtemp(join(tmpdir(), 'trailforge-integrity-'));
  let app;
  try {
    app = await startServer({ port: 0, dataDir: directory });
    await call(app, 'POST', '/api/projects', { id: 'integrity-project', name: 'Integrity test' });
    assert.equal((await call(app, 'POST', '/api/reports', { id: 'integrity-report', name: 'Retained test', projectIds: ['integrity-project'] })).status, 201);
    await app.close();
    app = null;
    const path = join(directory, 'workbench.json');
    const state = JSON.parse(await readFile(path, 'utf8'));
    state.reports[0].summary.projectCount = 999;
    await writeFile(path, JSON.stringify(state));
    app = await startServer({ port: 0, dataDir: directory });
    const listing = await call(app, 'GET', '/api/reports');
    assert.equal(listing.body.reports[0].integrity, 'FAIL');
    assert.equal((await call(app, 'GET', '/api/reports/integrity-report')).status, 422);
    assert.equal((await call(app, 'GET', '/api/reports/integrity-report/export')).status, 422);
    assert.equal((await call(app, 'POST', '/api/reports/integrity-report/replay', {})).status, 422);
  } finally {
    if (app) await app.close();
    await rm(directory, { recursive: true, force: true });
  }
});
