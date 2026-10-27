import test from 'node:test';
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { canonicalHash, createProject, updateProject, appendEvidence, importTrace, buildReport, verifyReport } from '../workbench/domain.mjs';

const now = '2026-10-27T12:00:00Z';
const stamp = day => `${day}T00:00:00Z`;
function evidence(id, day, extra = {}) {
  return { id, signalType: 'PERMIT_APPROVED', title: `Test-only ${id}`, sourceUrl: 'https://example.org/test-source', excerpt: `Test-only retained excerpt for ${id}.`, quote: `retained excerpt for ${id}`, eventAt: stamp(day), documentAt: stamp(day), availableAt: stamp(day), availabilityStatus: 'ATTESTED', reviewer: 'Test reviewer', proofUrl: 'https://example.org/test-proof', availabilityNote: 'Synthetic test chronology; not real historical evidence.', claims: {}, ...extra };
}
function add(project, item) { return appendEvidence(project, { revision: project.revision, ...item }, { now }); }
const qualifying = { project_specific: true, generation_need_supported: true, need_reason: 'Test construction continuity', buyer_organization: 'Test City' };

test('project edits detach inputs and enforce revisions; evidence keeps exact source bytes', () => {
  const project = createProject({ id: 'test-project', name: ' Test project ', notes: 'Initial' }, { now });
  assert.equal(project.name, 'Test project');
  assert.equal(project.revision, 1);
  assert.deepEqual(project.evidence, []);
  const changed = updateProject(project, { revision: 1, notes: 'Edited' }, { now });
  assert.equal(changed.revision, 2);
  assert.equal(project.notes, 'Initial');
  assert.throws(() => updateProject(changed, { revision: 1, notes: 'Stale' }, { now }), error => error.status === 409);
  const item = evidence('source-1', '2025-01-01', { excerpt: '  Source\nexact quote  ', quote: 'exact quote' });
  const saved = add(changed, item);
  assert.equal(saved.evidence[0].excerpt, item.excerpt);
  assert.equal(saved.evidence[0].sourceSha256, createHash('sha256').update(item.excerpt).digest('hex'));
  assert.equal(saved.evidence[0].recordedAt, now);
  assert.equal(changed.evidence.length, 0);
  assert.throws(() => add(saved, item));
  assert.throws(() => add(changed, { ...item, quote: 'Exact quote' }));
  assert.throws(() => add(changed, { ...item, availableAt: '2025-01-01T00:00:00' }));
  assert.throws(() => add(changed, { ...item, availableAt: '2099-01-01T00:00:00Z' }));
  assert.throws(() => add(changed, { ...item, reviewer: '' }));
  assert.throws(() => add(changed, { ...item, proofUrl: '' }));
  assert.throws(() => add(changed, { ...item, sourceUrl: 'http://127.0.0.1/private' }));
  assert.throws(() => add(changed, { ...item, sourceUrl: 'https://user:secret@example.org/source' }));
  assert.throws(() => add(changed, { ...item, claims: { required_mw: 300 } }));
});

test('temporal replay excludes milestones and later evidence; reports preserve signed lead', () => {
  let project = createProject({ id: 'early-project', name: 'Test early project' }, { now });
  project = add(project, evidence('early', '2025-01-01', { claims: qualifying }));
  project = add(project, evidence('target', '2025-02-01', { signalType: 'PROCUREMENT_SIGNAL', claims: qualifying }));
  project = add(project, evidence('later-suppression', '2025-03-01', { claims: { awarded: true } }));
  const before = JSON.stringify(project);
  const report = buildReport([project], { id: 'report-one', name: 'Test cohort', now });
  assert.equal(JSON.stringify(project), before);
  assert.equal(report.policyId, 'PRE_RFP_BASELINE_V1');
  const row = report.cases[0];
  assert.equal(row.firstSurfaceAt, stamp('2025-01-01'));
  assert.equal(row.comparisonAt, stamp('2025-02-01'));
  assert.equal(row.leadDays, 31);
  assert.equal(row.status, 'EARLY');
  assert.deepEqual(row.decisions[0].visibleEvidenceIds, ['early']);
  assert.deepEqual(row.decisions[0].basisEvidenceIds, ['early']);
  assert.deepEqual(row.decisions[0].buyerOrganizations, ['Test City']);
  assert.equal(row.decisions[0].decision, 'INVESTIGATE');
  assert.ok(!JSON.stringify(row.decisions[0]).includes('later-suppression'));
  assert.ok(row.decisions.every(decision => !decision.visibleEvidenceIds.includes('target')));
  assert.equal(row.decisions.at(-1).decision, 'SUPPRESS');
  assert.deepEqual(row.decisions.at(-1).basisEvidenceIds, ['later-suppression']);
  assert.equal(report.summary.matchedCount, 1);
  assert.equal(report.summary.medianLeadDays, 31);
  assert.equal(report.summary.coverage, 1);
  assert.equal(verifyReport(report).replay, 'PASS');
  const repeated = buildReport([project], { id: 'report-two', name: 'Other label', now: '2026-10-27T13:00:00Z' });
  assert.equal(repeated.inputHash, report.inputHash);
  assert.equal(repeated.resultHash, report.resultHash);
  let late = createProject({ id: 'late-project', name: 'Test late project' }, { now });
  late = add(late, evidence('late', '2025-03-01', { claims: qualifying }));
  late = add(late, evidence('target', '2025-02-01', { signalType: 'PROCUREMENT_SIGNAL' }));
  const lateReport = buildReport([late], { id: 'late-report', name: 'Late', now });
  assert.equal(lateReport.cases[0].leadDays, -28);
  assert.equal(lateReport.cases[0].status, 'NO_EARLY_ADVANTAGE');
  const ordered = buildReport([late, project], { id: 'ordered', name: 'Ordered', now });
  const reversed = buildReport([project, late], { id: 'reversed', name: 'Reversed', now });
  assert.equal(ordered.inputHash, reversed.inputHash);
  assert.equal(ordered.resultHash, reversed.resultHash);
  assert.equal(ordered.summary.medianLeadDays, -28);
  const damaged = structuredClone(report);
  damaged.inputs[0].notes = 'Changed after freezing';
  assert.equal(verifyReport(damaged).integrity, 'FAIL');
  assert.equal(verifyReport(damaged).checks.inputHash, false);
  const alteredResult = structuredClone(report);
  alteredResult.cases[0].leadDays = 999;
  assert.equal(verifyReport(alteredResult).replay, 'FAIL');
  alteredResult.resultHash = canonicalHash({ policyId: alteredResult.policyId, policyVersion: alteredResult.policyVersion, cases: alteredResult.cases, summary: alteredResult.summary });
  assert.equal(verifyReport(alteredResult).checks.recomputedResult, false);
});

test('unknown availability and unknown buyer do not receive investigation or numeric lead', () => {
  let unknown = createProject({ id: 'unknown-project', name: 'Unknown' }, { now });
  unknown = add(unknown, { id: 'unreviewed', signalType: 'PROJECT_ANNOUNCED', title: 'Unreviewed test note', sourceUrl: 'https://example.org/reference', excerpt: 'Test-only unreviewed source.', quote: 'unreviewed source', claims: qualifying });
  const report = buildReport([unknown], { id: 'unknown-report', name: 'Unknown', now });
  assert.equal(report.cases[0].status, 'UNKNOWN_AVAILABILITY');
  assert.equal(report.cases[0].leadDays, null);
  assert.equal(report.cases[0].firstSurfaceAt, null);
  assert.equal(report.cases[0].unknownAvailabilityCount, 1);
  assert.deepEqual(report.cases[0].decisions, []);
  assert.equal(report.summary.coverage, null);
  assert.equal(report.summary.medianLeadDays, null);
  for (const buyer of ['UNKNOWN', '  unknown  ', '']) {
    let project = createProject({ id: 'unknown-buyer', name: 'Unknown buyer' }, { now });
    project = add(project, evidence('early', '2025-01-01', { claims: { ...qualifying, buyer_organization: buyer } }));
    const result = buildReport([project], { id: 'buyer-report', name: 'Buyer', now });
    assert.equal(result.cases[0].decisions[0].decision, 'WATCH');
    assert.equal(result.cases[0].firstSurfaceAt, null);
  }
  assert.throws(() => buildReport([], { id: 'empty', name: 'Empty', now }));
  assert.throws(() => buildReport([unknown, unknown], { id: 'duplicate', name: 'Duplicate', now }));
});

test('legacy trace intake preserves references without asserting source or availability verification', () => {
  const trace = { schema_version: 'trailforge-project-trace-v1', project_id: 'legacy-project', trace_hash: 'a'.repeat(64), signals: [{ schema_version: 'trailforge-project-signal-v1', signal_id: 'legacy-signal', project_id: 'legacy-project', observed_at: '2025-01-01T00:00:00+00:00', signal_type: 'PERMIT_APPROVED', title: 'Test legacy reference', evidence_class: 'PUBLIC', source_sha256: 'b'.repeat(64), verified_by: 'Retained assertion', claims: { buyer_path: ['Test EPC'] }, source_url: 'https://example.org/legacy', source_quote: 'Retained quote', signal_hash: 'c'.repeat(64) }] };
  const project = importTrace({ id: 'imported-project', name: 'Imported reference', trace }, { now });
  assert.equal(project.importContext.verification, 'NOT_AUTHENTICATED');
  assert.equal(project.importContext.traceHash, trace.trace_hash);
  assert.deepEqual(project.importContext.original, trace);
  assert.deepEqual(project.evidence, []);
  trace.signals[0].title = 'Mutated caller object';
  assert.equal(project.importContext.original.signals[0].title, 'Test legacy reference');
  const result = buildReport([project], { id: 'reference-report', name: 'Reference', now });
  assert.equal(result.cases[0].firstSurfaceAt, null);
  assert.equal(result.cases[0].leadDays, null);
  assert.throws(() => importTrace({ id: 'bad-import', name: 'Bad', trace: { ...trace, schema_version: 'other' } }, { now }));
});
