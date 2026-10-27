import { createHash } from 'node:crypto';
import { isIP } from 'node:net';

const POLICY_ID = 'PRE_RFP_BASELINE_V1';
const POLICY_VERSION = '1.0';
const SLUG = /^[a-z0-9][a-z0-9-]{0,63}$/;
const HEX_HASH = /^[a-f0-9]{64}$/i;
const SIGNAL_TYPES = new Set([
  'PROJECT_ANNOUNCED',
  'PERMIT_FILED',
  'PERMIT_APPROVED',
  'GRID_CONNECTION_REQUESTED',
  'GRID_CONNECTION_DELAYED',
  'CONSTRUCTION_STARTED',
  'PROCUREMENT_SIGNAL',
  'POWER_NEED_IDENTIFIED',
  'BUYER_IDENTIFIED',
  'FUNDING_SECURED',
  'EPC_SELECTED',
]);
const BOOLEAN_CLAIMS = new Set([
  'project_specific', 'generation_need_supported',
  'generation_not_in_scope', 'awarded', 'supply_resolved',
]);
const TEXT_CLAIMS = new Set(['need_reason', 'buyer_organization']);
const SUPPRESSORS = ['generation_not_in_scope', 'awarded', 'supply_resolved'];
const EVIDENCE_FIELDS = [
  'revision', 'id', 'signalType', 'title', 'sourceUrl', 'excerpt', 'quote',
  'eventAt', 'documentAt', 'availableAt', 'availabilityStatus',
  'reviewer', 'proofUrl', 'availabilityNote', 'claims',
];
const PROJECT_FIELDS = [
  'id', 'name', 'location', 'notes', 'revision', 'archived',
  'createdAt', 'updatedAt', 'evidence', 'importContext',
];

function fail(message, status = 400, code = 'VALIDATION_ERROR') {
  throw Object.assign(new Error(message), { status, code });
}

function object(value, label) {
  if (value === null || typeof value !== 'object' || Array.isArray(value)) {
    fail(`${label} must be an object`);
  }
  const prototype = Object.getPrototypeOf(value);
  if (prototype !== Object.prototype && prototype !== null) {
    fail(`${label} must be a plain JSON object`);
  }
  return value;
}

function fields(value, allowed, label) {
  object(value, label);
  if (Object.getOwnPropertySymbols(value).length) fail(`${label} has unsupported fields`);
  for (const key of Object.keys(value)) {
    if (!allowed.includes(key)) fail(`${label} has unsupported field: ${key}`);
  }
}

function text(value, label, minimum, maximum, trim = false) {
  if (typeof value !== 'string') fail(`${label} must be text`);
  const result = trim ? value.trim() : value;
  if (result.length < minimum || result.length > maximum) {
    fail(`${label} must contain ${minimum}..${maximum} characters`);
  }
  return result;
}

function slug(value, label = 'id') {
  if (typeof value !== 'string' || !SLUG.test(value)) fail(`${label} must be a lowercase ASCII slug`);
  return value;
}

function compare(a, b) {
  return a < b ? -1 : a > b ? 1 : 0;
}

// Serialize directly: constructing an object and calling JSON.stringify would
// reorder integer-looking object keys instead of retaining lexical key order.
function canonicalJSON(value) {
  const ancestors = new Set();
  function encode(item) {
    if (item === null) return 'null';
    if (typeof item === 'string' || typeof item === 'boolean') return JSON.stringify(item);
    if (typeof item === 'number') {
      if (!Number.isFinite(item)) fail('JSON numbers must be finite');
      return JSON.stringify(item);
    }
    if (typeof item !== 'object') fail('Unsupported JSON value');
    if (ancestors.has(item)) fail('Circular JSON value');
    if (Object.getOwnPropertySymbols(item).length) fail('Symbol properties are unsupported');
    ancestors.add(item);
    let result;
    if (Array.isArray(item)) {
      const keys = Object.keys(item);
      if (keys.length !== item.length || keys.some((key, index) => key !== String(index))) {
        fail('Sparse arrays and extra array properties are unsupported');
      }
      const values = [];
      for (let index = 0; index < item.length; index += 1) {
        const descriptor = Object.getOwnPropertyDescriptor(item, String(index));
        if (!descriptor || !Object.hasOwn(descriptor, 'value')) fail('JSON accessors are unsupported');
        values.push(encode(descriptor.value));
      }
      result = `[${values.join(',')}]`;
    } else {
      object(item, 'JSON value');
      const pairs = Object.keys(item).sort(compare).map(key => {
        const descriptor = Object.getOwnPropertyDescriptor(item, key);
        if (!Object.hasOwn(descriptor, 'value')) fail('JSON accessors are unsupported');
        return `${JSON.stringify(key)}:${encode(descriptor.value)}`;
      });
      result = `{${pairs.join(',')}}`;
    }
    ancestors.delete(item);
    return result;
  }
  return encode(value);
}

function detached(value) {
  return JSON.parse(canonicalJSON(value));
}

export function canonicalHash(value) {
  return createHash('sha256').update(canonicalJSON(value), 'utf8').digest('hex');
}

function excerptHash(value) {
  return createHash('sha256').update(value, 'utf8').digest('hex');
}

function instant(value, label, upperBound = Infinity) {
  if (typeof value !== 'string') fail(`${label} must be a timezone-aware ISO instant`);
  const match = /^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})(?:\.\d+)?(Z|[+-]\d{2}:\d{2})$/.exec(value);
  if (!match) fail(`${label} must be a timezone-aware ISO instant`);
  const [, yearText, monthText, dayText, hourText, minuteText, secondText, zone] = match;
  const year = Number(yearText);
  const month = Number(monthText);
  const day = Number(dayText);
  const leap = year % 4 === 0 && (year % 100 !== 0 || year % 400 === 0);
  const monthDays = [31, leap ? 29 : 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];
  if (month < 1 || month > 12 || day < 1 || day > monthDays[month - 1]
      || Number(hourText) > 23 || Number(minuteText) > 59 || Number(secondText) > 59
      || (zone !== 'Z' && (Number(zone.slice(1, 3)) > 23 || Number(zone.slice(4)) > 59))) {
    fail(`${label} is not a valid ISO instant`);
  }
  const milliseconds = Date.parse(value);
  if (!Number.isFinite(milliseconds)) fail(`${label} is not a valid ISO instant`);
  if (milliseconds > upperBound) fail(`${label} must not be later than now`);
  return milliseconds;
}

function optionalInstant(value, label, now) {
  if (value === undefined || value === null) return null;
  instant(value, label, now);
  return value;
}

function publicIPv4(address) {
  const [a, b, c] = address.split('.').map(Number);
  if (a === 0 || a === 10 || a === 127 || a >= 224) return false;
  if (a === 100 && b >= 64 && b <= 127) return false;
  if (a === 169 && b === 254) return false;
  if (a === 172 && b >= 16 && b <= 31) return false;
  if (a === 192 && (b === 168 || b === 0 || (b === 88 && c === 99))) return false;
  if (a === 198 && (b === 18 || b === 19 || (b === 51 && c === 100))) return false;
  if (a === 203 && b === 0 && c === 113) return false;
  return true;
}

function publicIPv6(address) {
  // Public unicast space. This also rejects mapped private IPv4 literals,
  // loopback, unspecified, link-local, multicast, and unique-local addresses.
  const normalized = new URL(`http://[${address}]/`).hostname.slice(1, -1).toLowerCase();
  const first = parseInt(normalized.split(':')[0], 16);
  if (first < 0x2000 || first > 0x3fff) return false;
  if (/^2001:(?:db8|0|2|10|20)(?=:)/.test(normalized)) return false;
  if (normalized.startsWith('2002:')) return false;
  return true;
}

function referenceURL(value, label) {
  text(value, label, 1, Infinity);
  let parsed;
  try {
    parsed = new URL(value);
  } catch {
    fail(`${label} must be an HTTP(S) URL`);
  }
  if (!['http:', 'https:'].includes(parsed.protocol) || parsed.username || parsed.password) {
    fail(`${label} must be an HTTP(S) URL without credentials`);
  }
  const host = parsed.hostname.toLowerCase().replace(/\.$/, '');
  if (!host || host === 'localhost' || host.endsWith('.localhost')
      || host === 'local' || host.endsWith('.local')) {
    fail(`${label} must reference a public host`);
  }
  const literal = host.startsWith('[') ? host.slice(1, -1) : host;
  const version = isIP(literal);
  if ((version === 4 && !publicIPv4(literal)) || (version === 6 && !publicIPv6(literal))) {
    fail(`${label} must not reference a non-public IP literal`);
  }
  return value;
}

function revision(project, supplied) {
  if (!Number.isSafeInteger(supplied) || supplied !== project.revision) {
    fail('Project revision is stale; reload the current project', 409, 'STALE_REVISION');
  }
  if (project.revision >= Number.MAX_SAFE_INTEGER) fail('Project revision limit reached');
}

export function createProject(input, { now } = {}) {
  fields(input, ['id', 'name', 'location', 'notes'], 'Project');
  instant(now, 'now');
  return {
    id: slug(input.id),
    name: text(input.name, 'name', 1, 160, true),
    location: text(input.location === undefined ? '' : input.location, 'location', 0, 160),
    notes: text(input.notes === undefined ? '' : input.notes, 'notes', 0, 6000),
    revision: 1,
    archived: false,
    createdAt: now,
    updatedAt: now,
    evidence: [],
  };
}

export function updateProject(project, patch, { now } = {}) {
  fields(patch, ['revision', 'name', 'location', 'notes', 'archived'], 'Project patch');
  instant(now, 'now');
  object(project, 'Project');
  revision(project, patch.revision);
  const result = detached(project);
  if (Object.hasOwn(patch, 'name')) result.name = text(patch.name, 'name', 1, 160, true);
  if (Object.hasOwn(patch, 'location')) result.location = text(patch.location, 'location', 0, 160);
  if (Object.hasOwn(patch, 'notes')) result.notes = text(patch.notes, 'notes', 0, 6000);
  if (Object.hasOwn(patch, 'archived')) {
    if (typeof patch.archived !== 'boolean') fail('archived must be boolean');
    result.archived = patch.archived;
  }
  result.revision += 1;
  result.updatedAt = now;
  return result;
}

function validateClaims(value = {}) {
  object(value, 'claims');
  const result = {};
  for (const key of Object.keys(value)) {
    if (BOOLEAN_CLAIMS.has(key)) {
      if (typeof value[key] !== 'boolean') fail(`claims.${key} must be boolean`);
    } else if (TEXT_CLAIMS.has(key)) {
      text(value[key], `claims.${key}`, 0, 1000);
    } else {
      fail(`Unsupported claim: ${key}`);
    }
    result[key] = value[key];
  }
  if (Object.getOwnPropertySymbols(value).length) fail('Unsupported claim');
  return result;
}

function normalizeEvidence(input, now) {
  const ceiling = instant(now, 'now');
  slug(input.id, 'Evidence id');
  if (!SIGNAL_TYPES.has(input.signalType)) fail('Unsupported signalType');
  const title = text(input.title, 'title', 1, 200, true);
  const sourceUrl = referenceURL(input.sourceUrl, 'sourceUrl');
  const excerpt = text(input.excerpt, 'excerpt', 1, 20000);
  const quote = text(input.quote, 'quote', 1, 20000);
  if (!excerpt.includes(quote)) fail('quote must be an exact contiguous substring of excerpt');
  const eventAt = optionalInstant(input.eventAt, 'eventAt', ceiling);
  const documentAt = optionalInstant(input.documentAt, 'documentAt', ceiling);
  const availableAt = optionalInstant(input.availableAt, 'availableAt', ceiling);
  const availabilityStatus = input.availabilityStatus === undefined ? 'UNREVIEWED' : input.availabilityStatus;
  if (!['UNREVIEWED', 'ATTESTED'].includes(availabilityStatus)) fail('Unsupported availabilityStatus');
  const reviewer = text(input.reviewer === undefined ? '' : input.reviewer, 'reviewer', 0, 120, true);
  const availabilityNote = text(input.availabilityNote === undefined ? '' : input.availabilityNote, 'availabilityNote', 0, 2000, true);
  const proofUrl = input.proofUrl === undefined ? '' : input.proofUrl;
  if (proofUrl !== '') referenceURL(proofUrl, 'proofUrl');
  if (availabilityStatus === 'UNREVIEWED') {
    if (availableAt !== null) fail('UNREVIEWED evidence must have availableAt=null');
  } else {
    if (eventAt === null || documentAt === null || availableAt === null) {
      fail('ATTESTED evidence requires eventAt, documentAt, and availableAt');
    }
    if (Date.parse(eventAt) > Date.parse(availableAt) || Date.parse(documentAt) > Date.parse(availableAt)) {
      fail('Event and document timestamps must not follow availability');
    }
    if (!reviewer || !proofUrl || !availabilityNote) {
      fail('ATTESTED evidence requires a reviewer, proofUrl, and availabilityNote');
    }
  }
  return {
    id: input.id,
    signalType: input.signalType,
    title,
    sourceUrl,
    excerpt,
    quote,
    sourceSha256: excerptHash(excerpt),
    eventAt,
    documentAt,
    availableAt,
    availabilityStatus,
    reviewer,
    proofUrl,
    availabilityNote,
    claims: validateClaims(input.claims),
    recordedAt: now,
  };
}

export function appendEvidence(project, input, { now } = {}) {
  fields(input, EVIDENCE_FIELDS, 'Evidence');
  object(project, 'Project');
  revision(project, input.revision);
  const evidence = normalizeEvidence(input, now);
  if (!Array.isArray(project.evidence)) fail('Project evidence must be an array');
  if (project.evidence.some(item => item.id === evidence.id)) {
    fail('Evidence id already exists', 409, 'DUPLICATE_ID');
  }
  const result = detached(project);
  result.evidence.push(evidence);
  result.revision += 1;
  result.updatedAt = now;
  return result;
}

function validateTrace(trace) {
  // References intentionally retain the original schema's additional fields.
  // Validating their shape does not authenticate any supplied hashes or claims.
  canonicalJSON(trace);
  object(trace, 'trace');
  if (trace.schema_version !== 'trailforge-project-trace-v1') fail('Unsupported trace schema');
  text(trace.project_id, 'trace.project_id', 1, Infinity, true);
  if (typeof trace.trace_hash !== 'string' || !HEX_HASH.test(trace.trace_hash)) fail('Invalid trace_hash');
  if (!Array.isArray(trace.signals) || trace.signals.length < 1 || trace.signals.length > 500) {
    fail('Trace must contain 1..500 signals');
  }
  const ids = new Set();
  for (const signal of trace.signals) {
    object(signal, 'Trace signal');
    text(signal.signal_id, 'signal_id', 1, Infinity, true);
    if (ids.has(signal.signal_id)) fail('Duplicate trace signal_id');
    ids.add(signal.signal_id);
    if (signal.project_id !== trace.project_id) fail('Trace signal project_id does not match');
    if (!SIGNAL_TYPES.has(signal.signal_type)) fail('Unsupported trace signal_type');
    instant(signal.observed_at, 'observed_at');
    text(signal.title, 'signal title', 1, Infinity, true);
    if (typeof signal.source_sha256 !== 'string' || !HEX_HASH.test(signal.source_sha256)) {
      fail('Invalid source_sha256');
    }
    if (signal.evidence_class !== 'PUBLIC') fail('Only PUBLIC trace references are accepted');
    referenceURL(signal.source_url, 'source_url');
    if (Object.hasOwn(signal, 'source_quote') && signal.source_quote !== null) {
      text(signal.source_quote, 'source_quote', 0, Infinity);
    }
  }
}

export function importTrace(input, { now } = {}) {
  fields(input, ['id', 'name', 'trace'], 'Trace import');
  const project = createProject({ id: input.id, name: input.name }, { now });
  validateTrace(input.trace);
  project.importContext = {
    verification: 'NOT_AUTHENTICATED',
    traceHash: input.trace.trace_hash,
    original: detached(input.trace),
  };
  return project;
}

function validateSnapshot(project, now) {
  fields(project, PROJECT_FIELDS, 'Project snapshot');
  const ceiling = instant(now, 'now');
  createProject({ id: project.id, name: project.name, location: project.location, notes: project.notes }, { now });
  if (!Number.isSafeInteger(project.revision) || project.revision < 1) fail('Invalid project revision');
  if (typeof project.archived !== 'boolean') fail('Invalid archived state');
  instant(project.createdAt, 'createdAt', ceiling);
  instant(project.updatedAt, 'updatedAt', ceiling);
  if (!Array.isArray(project.evidence)) fail('Project evidence must be an array');
  const ids = new Set();
  for (const evidence of project.evidence) {
    fields(evidence, [...EVIDENCE_FIELDS.filter(key => key !== 'revision'), 'sourceSha256', 'recordedAt'], 'Retained evidence');
    if (ids.has(evidence.id)) fail('Duplicate retained evidence id');
    ids.add(evidence.id);
    instant(evidence.recordedAt, 'recordedAt', ceiling);
    const normalized = normalizeEvidence(evidence, evidence.recordedAt);
    if (evidence.sourceSha256 !== normalized.sourceSha256) fail('Retained excerpt hash does not match');
  }
  if (Object.hasOwn(project, 'importContext')) {
    fields(project.importContext, ['verification', 'traceHash', 'original'], 'importContext');
    const context = project.importContext;
    if (context.verification !== 'NOT_AUTHENTICATED') fail('Unsupported import verification');
    validateTrace(context.original);
    if (context.traceHash !== context.original.trace_hash) fail('Import trace hash reference does not match');
  }
}

function known(value) {
  return typeof value === 'string' && value.trim() !== '' && value.trim().toUpperCase() !== 'UNKNOWN';
}

function qualifies(evidence) {
  const claims = evidence.claims || {};
  return claims.project_specific === true && claims.generation_need_supported === true
    && known(claims.need_reason) && known(claims.buyer_organization);
}

function suppresses(evidence) {
  return SUPPRESSORS.some(key => evidence.claims?.[key] === true);
}

function round(value, digits) {
  const rounded = Number(value.toFixed(digits));
  return Object.is(rounded, -0) ? 0 : rounded;
}

function chronological(a, b) {
  return Date.parse(a) - Date.parse(b) || compare(a, b);
}

function computeCase(project) {
  const attested = project.evidence.filter(item => item.availabilityStatus === 'ATTESTED');
  const policyEvidence = attested.filter(item => item.signalType !== 'PROCUREMENT_SIGNAL');
  const times = [...new Set(policyEvidence.map(item => item.availableAt))].sort(chronological);
  const decisions = times.map(at => {
    const visibleEvidence = policyEvidence
      .filter(item => Date.parse(item.availableAt) <= Date.parse(at))
      .sort((a, b) => compare(a.id, b.id));
    const suppressing = visibleEvidence.filter(suppresses);
    const qualifying = visibleEvidence.filter(qualifies);
    const decision = suppressing.length ? 'SUPPRESS' : qualifying.length ? 'INVESTIGATE' : 'WATCH';
    const basis = decision === 'SUPPRESS' ? suppressing : decision === 'INVESTIGATE' ? qualifying : [];
    const buyerOrganizations = [...new Set(visibleEvidence
      .map(item => item.claims?.buyer_organization)
      .filter(known)
      .map(value => value.trim()))].sort(compare);
    return {
      at,
      decision,
      basisEvidenceIds: basis.map(item => item.id),
      visibleEvidenceIds: visibleEvidence.map(item => item.id),
      visibleEvidence: detached(visibleEvidence),
      buyerOrganizations,
    };
  });
  const firstSurfaceAt = decisions.find(item => item.decision === 'INVESTIGATE')?.at ?? null;
  const comparisonAt = attested.filter(item => item.signalType === 'PROCUREMENT_SIGNAL')
    .map(item => item.availableAt).sort(chronological)[0] ?? null;
  const leadDays = firstSurfaceAt !== null && comparisonAt !== null
    ? round((Date.parse(comparisonAt) - Date.parse(firstSurfaceAt)) / 86400000, 3)
    : null;
  const unknownAvailabilityCount = project.evidence.filter(item => item.availabilityStatus === 'UNREVIEWED').length;
  let status;
  if (leadDays !== null) status = leadDays > 0 ? 'EARLY' : 'NO_EARLY_ADVANTAGE';
  else if (unknownAvailabilityCount > 0) status = 'UNKNOWN_AVAILABILITY';
  else if (firstSurfaceAt === null) status = 'NO_SURFACE';
  else status = 'MISSING_MILESTONE';
  return {
    projectId: project.id,
    projectName: project.name,
    firstSurfaceAt,
    comparisonAt,
    leadDays,
    status,
    unknownAvailabilityCount,
    decisions,
  };
}

function computeResults(inputs) {
  const cases = inputs.map(computeCase).sort((a, b) => compare(a.projectId, b.projectId));
  const measured = cases.filter(item => item.leadDays !== null).map(item => item.leadDays).sort((a, b) => a - b);
  const targetCount = cases.filter(item => item.comparisonAt !== null).length;
  const summary = {
    projectCount: cases.length,
    surfacedCount: cases.filter(item => item.firstSurfaceAt !== null).length,
    targetCount,
    matchedCount: measured.length,
    unresolvedCount: cases.length - measured.length,
    medianLeadDays: measured.length ? measured[Math.floor((measured.length - 1) / 2)] : null,
    coverage: targetCount ? round(measured.length / targetCount, 6) : null,
    decisionCount: cases.reduce((count, item) => count + item.decisions.length, 0),
  };
  return { cases, summary };
}

export function buildReport(projects, options = {}) {
  fields(options, ['id', 'name', 'now'], 'Report options');
  const { id, now } = options;
  slug(id, 'Report id');
  const name = text(options.name, 'Report name', 1, 200, true);
  instant(now, 'now');
  if (!Array.isArray(projects) || projects.length < 1 || projects.length > 50) {
    fail('A report requires 1..50 distinct projects');
  }
  const inputs = detached(projects).sort((a, b) => compare(a?.id, b?.id));
  const ids = new Set();
  for (const project of inputs) {
    validateSnapshot(project, now);
    if (ids.has(project.id)) fail('A report requires distinct projects');
    ids.add(project.id);
  }
  const { cases, summary } = computeResults(inputs);
  return {
    schemaVersion: 1,
    id,
    name,
    createdAt: now,
    policyId: POLICY_ID,
    policyVersion: POLICY_VERSION,
    inputs,
    cases,
    summary,
    inputHash: canonicalHash(inputs),
    resultHash: canonicalHash({ policyId: POLICY_ID, policyVersion: POLICY_VERSION, cases, summary }),
  };
}

export function verifyReport(report) {
  const checks = { inputHash: false, resultHash: false, recomputedResult: false };
  // Each check runs independently so one malformed component does not conceal
  // useful results from the other checks. Verification never changes its input.
  try {
    checks.inputHash = canonicalHash(report.inputs) === report.inputHash;
  } catch {}
  try {
    checks.resultHash = canonicalHash({
      policyId: report.policyId,
      policyVersion: report.policyVersion,
      cases: report.cases,
      summary: report.summary,
    }) === report.resultHash;
  } catch {}
  try {
    if (report.schemaVersion === 1 && report.policyId === POLICY_ID && report.policyVersion === POLICY_VERSION) {
      const replayed = buildReport(report.inputs, {
        id: report.id,
        name: report.name,
        now: report.createdAt,
      });
      checks.recomputedResult = canonicalHash({ cases: replayed.cases, summary: replayed.summary })
        === canonicalHash({ cases: report.cases, summary: report.summary });
    }
  } catch {}
  const integrity = checks.inputHash && checks.resultHash ? 'PASS' : 'FAIL';
  return {
    integrity,
    replay: integrity === 'PASS' && checks.recomputedResult ? 'PASS' : 'FAIL',
    checks,
  };
}
