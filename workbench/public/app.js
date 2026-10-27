const $ = (selector) => document.querySelector(selector);
const main = $('#main');
const state = { query: '', archived: false, selected: new Set(), cohortName: '', project: null, editor: null, evidenceProject: null, archiveProject: null, routeVersion: 0 };
const openers = new WeakMap();

function node(tag, attributes = {}, ...children) {
  const element = document.createElement(tag);
  for (const [key, value] of Object.entries(attributes)) {
    if (value === null || value === undefined || value === false) continue;
    if (key === 'className') element.className = value;
    else if (key === 'checked' || key === 'disabled' || key === 'hidden') element[key] = Boolean(value);
    else element.setAttribute(key, String(value));
  }
  for (const child of children.flat(Infinity)) {
    if (child !== null && child !== undefined) element.append(child instanceof Node ? child : document.createTextNode(String(child)));
  }
  return element;
}
function button(text, action, attributes = {}) {
  const result = node('button', { type: 'button', ...attributes }, text);
  result.addEventListener('click', action);
  return result;
}
function badge(text, kind = '') { return node('span', { className: `badge ${kind}` }, text); }
function empty(title, text) { return node('div', { className: 'empty' }, node('h3', {}, title), node('p', {}, text)); }
function field(label, value, className = '') { return node('div', {}, node('dt', {}, label), node('dd', { className }, value ?? 'Unresolved')); }
function date(value) { return value ? String(value) : 'Unknown'; }
function detail(label, content) { return node('details', {}, node('summary', {}, label), content); }
function sourceLink(value, label) {
  try {
    const url = new URL(value);
    if (!['http:', 'https:'].includes(url.protocol) || url.username || url.password) throw new Error();
    return node('a', { href: url.href, target: '_blank', rel: 'noopener noreferrer', className: 'inline-link' }, label || value);
  } catch { return node('span', { className: 'subtle' }, value || 'No source URL'); }
}
function notice(message) { $('#notice').textContent = message; $('#notice').hidden = !message; }
async function api(path, options = {}) {
  let response;
  try {
    response = await fetch(path, { ...options, cache: 'no-store', headers: { ...(options.body !== undefined ? { 'Content-Type': 'application/json' } : {}), ...options.headers }, body: options.body !== undefined ? JSON.stringify(options.body) : undefined });
  } catch { throw new Error('The local server could not be reached. Check that it is running, then retry.'); }
  let body;
  try { body = await response.json(); } catch { throw new Error('The local server returned an unreadable response. Retry when it is available.'); }
  if (!response.ok) {
    const error = new Error(body.error || `Request failed (${response.status}).`);
    error.status = response.status;
    error.code = body.code;
    error.body = body;
    throw error;
  }
  return body;
}
async function busy(control, task) {
  control.disabled = true;
  control.setAttribute('aria-busy', 'true');
  try { return await task(); } finally { control.disabled = false; control.removeAttribute('aria-busy'); }
}
function showDialog(id, opener = document.activeElement) {
  const dialog = document.getElementById(id);
  openers.set(dialog, opener);
  dialog.showModal();
}
for (const dialog of document.querySelectorAll('dialog')) {
  dialog.addEventListener('close', () => {
    const opener = openers.get(dialog);
    if (opener?.isConnected) opener.focus();
    else main.focus();
  });
}
for (const control of document.querySelectorAll('[data-close]')) {
  control.addEventListener('click', () => document.getElementById(control.dataset.close).close());
}
function validation(form, error, prefix = '') {
  if (form.checkValidity()) return true;
  error.textContent = `${prefix}Complete the required fields and check their formats.`;
  form.reportValidity();
  return false;
}
function projectPath(id) { return `/api/projects/${encodeURIComponent(id)}`; }
function goProject(project) { location.hash = `/projects/${encodeURIComponent(project.id)}`; }
function goReport(report) { location.hash = `/reports/${encodeURIComponent(report.id)}`; }

function openProjectEditor(project, opener) {
  state.editor = project ? { id: project.id, revision: project.revision } : null;
  $('#project-dialog-title').textContent = project ? 'Edit project' : 'New project';
  $('#project-name-input').value = project?.name || '';
  $('#project-location-input').value = project?.location || '';
  $('#project-notes-input').value = project?.notes || '';
  $('#project-form-error').textContent = '';
  $('#revision-message').textContent = '';
  $('#refresh-project-revision').hidden = true;
  showDialog('project-dialog', opener);
}
$('#project-form').addEventListener('submit', async (event) => {
  event.preventDefault();
  const error = $('#project-form-error');
  error.textContent = '';
  if (!validation(event.currentTarget, error, 'Could not save project. ')) return;
  const payload = { name: $('#project-name-input').value, location: $('#project-location-input').value, notes: $('#project-notes-input').value };
  const editor = state.editor ? { ...state.editor } : null;
  if (editor) payload.revision = editor.revision;
  await busy($('#save-project'), async () => {
    try {
      const { project } = await api(editor ? projectPath(editor.id) : '/api/projects', { method: editor ? 'PATCH' : 'POST', body: payload });
      $('#project-dialog').close();
      if (location.hash === `#/projects/${encodeURIComponent(project.id)}`) await route();
      else goProject(project);
    } catch (failure) {
      error.textContent = `Could not save project. ${failure.message}`;
      if (failure.status === 409 && editor) {
        error.textContent += ' Your values are retained. Load the current revision, review your values, and retry explicitly.';
        $('#refresh-project-revision').hidden = false;
      }
    }
  });
});
$('#refresh-project-revision').addEventListener('click', async (event) => {
  if (!state.editor) return;
  await busy(event.currentTarget, async () => {
    try {
      const { project } = await api(projectPath(state.editor.id));
      state.editor.revision = project.revision;
      $('#revision-message').textContent = `Current revision ${project.revision} loaded. Stored name: ${project.name}. Stored location: ${project.location || '(empty)'}. Stored notes: ${project.notes || '(empty)'}. Your editor values are unchanged. Review before saving.`;
      $('#project-form-error').textContent = '';
      $('#refresh-project-revision').hidden = true;
    } catch (failure) { $('#project-form-error').textContent = `Could not save project. ${failure.message}`; }
  });
});

function openArchive(project, opener) {
  state.archiveProject = { id: project.id, revision: project.revision };
  $('#archive-title').textContent = `Archive ${project.name}?`;
  $('#archive-error').textContent = '';
  showDialog('archive-dialog', opener);
  $('#cancel-archive').focus();
}
$('#archive-form').addEventListener('submit', async (event) => {
  event.preventDefault();
  const project = state.archiveProject;
  if (!project) return;
  await busy($('#confirm-archive'), async () => {
    try {
      await api(projectPath(project.id), { method: 'DELETE', body: { revision: project.revision } });
      $('#archive-dialog').close();
      notice('Project archived. Evidence and report references are retained.');
      location.hash = '/';
    } catch (failure) { $('#archive-error').textContent = `${failure.message} No archive was confirmed by this request. Close and reload the project before retrying a revision conflict.`; }
  });
});

function syncAttestation() {
  const attested = $('#evidence-availability').value === 'ATTESTED';
  $('#attestation-fields').hidden = !attested;
  $('#unreviewed-help').hidden = attested;
  for (const control of $('#attestation-fields').querySelectorAll('input,textarea')) { control.disabled = !attested; control.required = attested; }
  $('#evidence-event-at').required = attested;
  $('#evidence-document-at').required = attested;
}
$('#evidence-availability').addEventListener('change', syncAttestation);
function openEvidence(project, opener) {
  state.evidenceProject = { id: project.id, revision: project.revision };
  $('#evidence-form').reset();
  $('#evidence-quote').setCustomValidity('');
  $('#evidence-error').textContent = '';
  const types = new Set(['PROCUREMENT_SIGNAL']);
  for (const evidence of project.evidence || []) types.add(evidence.signalType);
  for (const signal of project.importContext?.original?.signals || []) types.add(signal.signal_type);
  $('#signal-types').replaceChildren(...[...types].filter(Boolean).sort().map(type => node('option', { value: type })));
  syncAttestation();
  showDialog('evidence-dialog', opener);
}
for (const id of ['evidence-quote', 'evidence-excerpt']) document.getElementById(id).addEventListener('input', () => $('#evidence-quote').setCustomValidity(''));
$('#evidence-form').addEventListener('submit', async (event) => {
  event.preventDefault();
  const error = $('#evidence-error');
  error.textContent = '';
  const form = event.currentTarget;
  const values = new FormData(form);
  const excerpt = String(values.get('excerpt') || '');
  const quote = String(values.get('quote') || '');
  $('#evidence-quote').setCustomValidity(quote && excerpt.includes(quote) ? '' : 'The quote must be a nonempty exact contiguous part of the excerpt.');
  if (!validation(form, error)) return;
  const project = state.evidenceProject;
  const payload = { revision: project.revision, title: values.get('title'), signalType: values.get('signalType'), sourceUrl: values.get('sourceUrl'), excerpt, quote, availabilityStatus: values.get('availabilityStatus'), claims: {} };
  for (const clock of ['eventAt', 'documentAt']) payload[clock] = String(values.get(clock) || '').trim() || null;
  if (payload.availabilityStatus === 'ATTESTED') {
    for (const key of ['availableAt', 'reviewer', 'proofUrl', 'availabilityNote']) payload[key] = values.get(key);
  } else payload.availableAt = null;
  for (const key of ['project_specific', 'generation_need_supported', 'generation_not_in_scope', 'awarded', 'supply_resolved']) {
    const value = values.get(key);
    if (value === 'true' || value === 'false') payload.claims[key] = value === 'true';
  }
  for (const key of ['need_reason', 'buyer_organization']) {
    const value = String(values.get(key) || '');
    if (value.length) payload.claims[key] = value;
  }
  await busy($('#save-evidence'), async () => {
    try {
      await api(`${projectPath(project.id)}/evidence`, { method: 'POST', body: payload });
      $('#evidence-dialog').close();
      await route();
    } catch (failure) {
      error.textContent = `Could not append evidence. ${failure.message}`;
      if (failure.status === 409) {
        error.textContent += ' Your evidence values are retained. Refresh the revision below, then retry explicitly.';
        if (!$('#refresh-evidence-revision')) {
          const refresh = button('Load current revision for retry', async (click) => {
            await busy(click.currentTarget, async () => {
              try {
                const result = await api(projectPath(project.id));
                state.evidenceProject.revision = result.project.revision;
                error.textContent = `Revision ${result.project.revision} loaded. Your evidence values are unchanged. Review and retry.`;
                click.currentTarget.remove();
              } catch (refreshFailure) { error.textContent = refreshFailure.message; }
            });
          }, { id: 'refresh-evidence-revision', className: 'secondary' });
          error.after(refresh);
        }
      }
    }
  });
});
$('#evidence-dialog').addEventListener('close', () => $('#refresh-evidence-revision')?.remove());

$('#import-form').addEventListener('submit', async (event) => {
  event.preventDefault();
  const error = $('#import-error');
  error.textContent = '';
  if (!validation(event.currentTarget, error)) return;
  let trace;
  try { trace = JSON.parse($('#import-json').value); } catch { error.textContent = 'Could not import references. Enter a valid JSON object. Your input is retained.'; return; }
  const payload = { name: $('#import-name').value, trace };
  if ($('#import-id').value) payload.id = $('#import-id').value;
  await busy($('#save-import'), async () => {
    try {
      const { project } = await api('/api/imports/traces', { method: 'POST', body: payload });
      $('#import-dialog').close();
      $('#import-form').reset();
      goProject(project);
    } catch (failure) { error.textContent = `Could not import references. ${failure.message} Your input is retained.`; }
  });
});

function home(projects, reports) {
  const active = projects.filter(project => !project.archived);
  for (const id of state.selected) if (!active.some(project => project.id === id)) state.selected.delete(id);
  const unknown = projects.reduce((count, project) => count + (project.evidence || []).filter(item => item.availabilityStatus === 'UNREVIEWED').length + (project.importContext?.original?.signals?.length || 0), 0);
  const heading = node('div', { className: 'heading-row' }, node('div', {}, node('p', { className: 'eyebrow' }, 'EVIDENCE BEFORE OUTCOMES'), node('h1', {}, 'Historical signal workbench'), node('p', { className: 'intro' }, 'Assemble project evidence, inspect what was available at each decision time, and retain reproducible Pre-RFP reviews.')));
  const newProject = button('New project', event => openProjectEditor(null, event.currentTarget), { id: 'new-project' });
  const importButton = button('Import trace JSON', event => { $('#import-error').textContent = ''; showDialog('import-dialog', event.currentTarget); }, { className: 'secondary', id: 'import-trace' });
  heading.append(node('div', { className: 'actions' }, newProject, importButton));
  const stats = node('div', { className: 'stats', 'aria-label': 'Retained collection counts' }, stat(active.length, 'Active projects'), stat(reports.length, 'Retained reports'), stat(unknown, 'Availability unreviewed'));
  const search = node('input', { id: 'project-search', type: 'search', placeholder: 'Name, location, or notes', autocomplete: 'off' });
  search.value = state.query;
  const showArchived = node('input', { id: 'show-archived', type: 'checkbox', checked: state.archived });
  const list = node('div', { id: 'project-list', className: 'project-list' });
  const listCount = node('p', { className: 'count-text', role: 'status' });
  const selectedCount = node('p', { id: 'cohort-count', className: 'cohort-count', role: 'status' });
  const reportName = node('input', { id: 'cohort-report-name', name: 'name', maxlength: 200, required: true, placeholder: 'Name this historical review' });
  reportName.value = state.cohortName;
  reportName.addEventListener('input', () => { state.cohortName = reportName.value; });
  const cohortError = node('p', { id: 'cohort-error', className: 'error', role: 'alert' });
  const createReport = node('button', { type: 'submit', id: 'create-cohort-report' }, 'Freeze cohort report');
  const clear = button('Clear selection', () => { state.selected.clear(); drawList(); }, { className: 'quiet' });
  const cohortForm = node('form', { novalidate: true }, node('label', { for: 'cohort-report-name' }, 'Report name'), reportName, selectedCount, cohortError, node('div', { className: 'actions' }, createReport, clear));
  const cohort = node('aside', { className: 'panel', 'aria-labelledby': 'cohort-heading' }, node('p', { className: 'eyebrow' }, 'REPRODUCIBLE COHORT'), node('h2', { id: 'cohort-heading' }, 'Compare a bounded set'), node('p', {}, 'Select 1–50 active projects. A report freezes their current evidence, records every decision, and keeps unresolved availability explicit.'), cohortForm, node('p', { className: 'hint' }, 'Historical lead is comparison availability minus first investigation time. Negative leads are retained. Missing clocks stay unresolved.'), node('a', { href: '#/reports', className: 'inline-link' }, 'Browse retained reports →'));
  function updateSelection() {
    selectedCount.textContent = `${state.selected.size} of 50 projects selected`;
    createReport.disabled = state.selected.size < 1 || state.selected.size > 50;
    clear.disabled = state.selected.size === 0;
  }
  function drawList() {
    const query = state.query.toLowerCase();
    const filtered = projects.filter(project => (state.archived || !project.archived) && [project.name, project.location, project.notes].some(value => String(value || '').toLowerCase().includes(query))).sort((a, b) => a.name.localeCompare(b.name) || a.id.localeCompare(b.id));
    list.replaceChildren();
    listCount.textContent = `${filtered.length} project${filtered.length === 1 ? '' : 's'} shown`;
    if (!filtered.length) {
      list.append(projects.length ? empty('No matching projects', 'Try a different search or include archived projects. Your cohort selection is retained.') : empty('Begin with a project', 'Create your first project to retain source excerpts and research notes. Nothing is acquired automatically.'));
    }
    for (const project of filtered) {
      const open = button(project.name, () => goProject(project), { className: 'project-open', 'data-open-project': project.id });
      const card = node('article', { className: 'project-card' }, open, node('p', {}, project.location || 'Location not recorded'), node('div', { className: 'card-meta' }, badge(project.archived ? 'Archived' : 'Active'), node('small', {}, `${project.evidence.length} evidence records · revision ${project.revision}`)));
      if (!project.archived) {
        const check = node('input', { type: 'checkbox', checked: state.selected.has(project.id), 'aria-label': `Select ${project.name} for cohort` });
        check.addEventListener('change', () => {
          if (check.checked && state.selected.size >= 50) { check.checked = false; cohortError.textContent = 'A cohort can contain at most 50 projects.'; return; }
          check.checked ? state.selected.add(project.id) : state.selected.delete(project.id);
          cohortError.textContent = '';
          updateSelection();
        });
        card.append(node('label', { className: 'check-label' }, check, 'Include in cohort'));
      }
      list.append(card);
    }
    updateSelection();
  }
  search.addEventListener('input', () => { state.query = search.value; drawList(); });
  showArchived.addEventListener('change', () => { state.archived = showArchived.checked; drawList(); });
  cohortForm.addEventListener('submit', async event => {
    event.preventDefault();
    cohortError.textContent = '';
    if (!state.selected.size || state.selected.size > 50) { cohortError.textContent = 'Select between 1 and 50 active projects.'; return; }
    if (!validation(cohortForm, cohortError)) return;
    await busy(createReport, async () => {
      try { const { report } = await api('/api/reports', { method: 'POST', body: { name: reportName.value, projectIds: [...state.selected].sort() } }); goReport(report); }
      catch (failure) { cohortError.textContent = `Could not freeze report. ${failure.message} Your selection and report name are retained.`; }
    });
  });
  main.replaceChildren(heading, stats, node('div', { className: 'collection-layout' }, node('section', { 'aria-labelledby': 'collection-heading' }, node('h2', { id: 'collection-heading' }, 'Project collection'), node('div', { className: 'collection-toolbar' }, node('label', { for: 'project-search' }, 'Search projects'), search, node('label', { className: 'check-label', for: 'show-archived' }, showArchived, 'Include archived projects')), listCount, list), cohort));
  drawList();
}
function stat(value, label) { return node('div', { className: 'stat' }, node('strong', {}, value), node('span', {}, label)); }

function evidenceCard(evidence) {
  const attested = evidence.availabilityStatus === 'ATTESTED';
  const card = node('article', { className: 'evidence-card' }, badge(attested ? 'Operator-attested availability' : 'Awaiting availability review', attested ? '' : 'unresolved'), node('h3', {}, evidence.title), node('p', { className: 'hint' }, `${evidence.signalType} · ${evidence.id}`), sourceLink(evidence.sourceUrl), node('blockquote', {}, evidence.quote), node('dl', { className: 'facts' }, field('Event time', date(evidence.eventAt)), field('Document time', date(evidence.documentAt)), field('Historical availability', attested ? date(evidence.availableAt) : 'Unreviewed — no availability established'), field('Recorded locally', date(evidence.recordedAt))), detail('Retained exact excerpt', node('pre', {}, evidence.excerpt)), node('p', { className: 'hash' }, `Excerpt SHA-256: ${evidence.sourceSha256}`));
  if (attested) card.append(node('div', { className: 'callout' }, node('strong', {}, `Operator assertion by ${evidence.reviewer}`), node('p', {}, evidence.availabilityNote), sourceLink(evidence.proofUrl, 'Availability proof reference'), node('p', { className: 'hint' }, 'This attestation does not independently authenticate the source or its historical availability.')));
  const claims = Object.entries(evidence.claims || {});
  if (claims.length) card.append(detail('Retained baseline claims', node('dl', { className: 'metadata' }, claims.map(([key, value]) => field(key.replaceAll('_', ' '), String(value))))));
  return card;
}
function importedReferences(context) {
  const section = node('section', { className: 'section', 'aria-labelledby': 'references-heading' }, node('h2', { id: 'references-heading' }, 'Imported reference context'), badge('NOT_AUTHENTICATED', 'unresolved'), node('p', {}, 'Original trace hashes are retained assertions. Observation timestamps are not proof of historical availability. Add separately supported evidence through the normal evidence form.'), node('p', { className: 'hash' }, `Supplied trace hash: ${context.traceHash}`));
  const signals = node('div', { className: 'evidence-list' });
  for (const signal of context.original?.signals || []) {
    signals.append(node('article', { className: 'evidence-card' }, badge('Imported reference — availability unreviewed', 'unresolved'), node('h3', {}, signal.title), node('p', { className: 'hint' }, `${signal.signal_type} · ${signal.signal_id}`), sourceLink(signal.source_url), signal.source_quote ? node('blockquote', {}, signal.source_quote) : node('p', { className: 'hint' }, 'No source quote supplied.'), node('p', {}, `Reported observation: ${signal.observed_at}`), node('p', { className: 'hash' }, `Supplied source hash: ${signal.source_sha256}`)));
  }
  section.append(detail(`Inspect ${context.original?.signals?.length || 0} original signal references`, signals), detail('Complete retained trace JSON', node('pre', {}, JSON.stringify(context.original, null, 2))));
  return section;
}
function projectDetail(project) {
  state.project = project;
  const errors = node('p', { id: 'action-error', className: 'error', role: 'alert' });
  const edit = button('Edit project', event => openProjectEditor(project, event.currentTarget), { id: 'edit-project' });
  const archive = button('Archive project', event => openArchive(project, event.currentTarget), { id: 'archive-project', className: 'secondary' });
  const restore = button('Restore project', async event => {
    errors.textContent = '';
    await busy(event.currentTarget, async () => {
      try { await api(projectPath(project.id), { method: 'PATCH', body: { revision: project.revision, archived: false } }); await route(); }
      catch (failure) { errors.textContent = `Could not restore project. ${failure.message} Reload to obtain the current revision if it changed.`; }
    });
  }, { id: 'restore-project' });
  const runReport = button('Run Pre-RFP review', async event => {
    errors.textContent = '';
    await busy(event.currentTarget, async () => {
      try { const { report } = await api('/api/reports', { method: 'POST', body: { name: `${project.name} · Pre-RFP review`, projectIds: [project.id] } }); goReport(report); }
      catch (failure) { errors.textContent = `Could not create report. ${failure.message} Retry when the local store is available.`; }
    });
  }, { id: 'run-project-report', className: 'secondary', disabled: project.archived });
  const heading = node('div', {}, node('a', { id: 'back-projects', href: '#/', className: 'inline-link' }, '← Back to projects'), node('p', { className: 'eyebrow' }, 'PROJECT FIELD NOTEBOOK'), node('h1', { id: 'project-name' }, project.name), node('div', { className: 'card-meta' }, badge(project.archived ? 'Archived project' : 'Active project'), node('span', { className: 'hint' }, `Revision ${project.revision} · ${project.id}`)), node('div', { className: 'actions' }, edit, project.archived ? restore : archive, runReport), errors);
  if (project.archived) heading.append(node('p', { className: 'callout' }, 'This project is archived. Its evidence remains retained. Restore it before including it in a new report.'));
  const metadata = node('div', { className: 'detail-grid' }, node('section', {}, node('h2', {}, 'Research notes'), node('div', { id: 'project-notes', className: 'notes' }, project.notes || 'No research notes yet.')), node('aside', { className: 'panel' }, node('h2', {}, 'Project record'), node('dl', { className: 'metadata' }, field('Location', project.location || 'Not recorded'), field('Created', project.createdAt), field('Updated', project.updatedAt)), node('p', { className: 'hint' }, 'Evidence is append-only. Metadata edits do not alter frozen reports.')));
  const evidenceList = node('div', { id: 'evidence-list', className: 'evidence-list' });
  if (!project.evidence.length) evidenceList.append(empty('No captured evidence yet', 'Append an exact excerpt and quote. Historical availability stays unreviewed until an operator explicitly attests it.'));
  else evidenceList.append(...project.evidence.map(evidenceCard));
  const section = node('section', { className: 'section', 'aria-labelledby': 'evidence-heading' }, node('div', { className: 'section-heading' }, node('h2', { id: 'evidence-heading' }, `Retained evidence · ${project.evidence.length}`), button('Add evidence', event => openEvidence(project, event.currentTarget), { id: 'add-evidence' })), evidenceList);
  main.replaceChildren(heading, metadata, section);
  if (project.importContext) main.append(importedReferences(project.importContext));
}

function reportList(reports) {
  const list = node('div', { className: 'report-list' });
  if (!reports.length) list.append(empty('No frozen reports yet', 'Run a review from a project or select a cohort in the project collection. Reports retain their inputs even as projects change.'));
  for (const report of reports) {
    const passed = report.integrity === 'PASS';
    const card = node('article', { className: 'report-card' }, badge(passed ? 'Integrity PASS' : 'Integrity FAIL', passed ? '' : 'failure'), node('h2', {}, node('a', { href: `#/reports/${encodeURIComponent(report.id)}` }, report.name)), node('p', {}, `Frozen ${date(report.createdAt)}`));
    if (passed) card.append(node('p', {}, `${report.summary.projectCount} projects · ${report.summary.matchedCount} measured leads · ${report.summary.unresolvedCount} unresolved`));
    else card.append(node('p', { className: 'error' }, 'Integrity failed. Results are withheld; this retained record needs investigation.'));
    list.append(card);
  }
  main.replaceChildren(node('p', { className: 'eyebrow' }, 'RETAINED RESEARCH'), node('h1', {}, 'Frozen cohort reports'), node('p', { className: 'intro' }, 'Reports preserve the selected project revisions and their evidence. Integrity checks retained hashes; explicit replay independently recomputes the bounded baseline.'), node('a', { href: '#/', className: 'inline-link' }, '← Select projects for a new report'), list);
}
function signedLead(value) { return typeof value === 'number' ? `${value > 0 ? '+' : ''}${value} days` : 'Historical lead unresolved'; }
function reportCase(result, input) {
  const caseNode = node('article', { className: 'report-case' }, node('h2', {}, result.projectName), node('div', { className: 'case-status' }, badge(result.status, result.leadDays === null ? 'unresolved' : '')), node('dl', { className: 'facts' }, field('First investigation / surfaced time', result.firstSurfaceAt || 'Unresolved — no investigation'), field('Comparison availability', result.comparisonAt || 'Unresolved — no attested milestone'), field('Signed historical lead', signedLead(result.leadDays), 'signed-lead')), node('p', { className: 'hint' }, `${result.unknownAvailabilityCount} unreviewed evidence records · ${result.decisions.length} retained decisions`));
  const panel = node('section', { className: 'decision-panel', 'aria-label': 'Evidence visible at selected decision time', 'aria-live': 'polite' });
  const times = node('div', { className: 'decision-times', 'aria-label': 'Select decision time' });
  const controls = [];
  function selectDecision(decision, selected) {
    controls.forEach(control => control.setAttribute('aria-pressed', String(control === selected)));
    panel.replaceChildren(node('h4', {}, `${decision.decision} · ${decision.at}`), node('p', { className: 'hint' }, 'Only attested non-procurement evidence available at or before this decision time is shown below.'), node('p', {}, `Basis evidence: ${decision.basisEvidenceIds.length ? decision.basisEvidenceIds.join(', ') : 'None — WATCH has no qualifying basis'}`), node('p', {}, `Visible evidence IDs: ${decision.visibleEvidenceIds.length ? decision.visibleEvidenceIds.join(', ') : 'None'}`), node('p', {}, `Buyer organizations: ${decision.buyerOrganizations.length ? decision.buyerOrganizations.join('; ') : 'No known buyer in visible evidence'}`));
    const visible = node('div', { className: 'evidence-list' });
    if (!decision.visibleEvidence.length) visible.append(empty('No visible evidence', 'No policy evidence was available at this decision time.'));
    else visible.append(...decision.visibleEvidence.map(evidenceCard));
    panel.append(visible);
  }
  for (const decision of result.decisions) {
    const control = button(`${decision.at} · ${decision.decision}`, () => selectDecision(decision, control), { className: 'secondary', 'aria-pressed': 'false' });
    controls.push(control);
    times.append(control);
  }
  caseNode.append(node('h3', { className: 'section' }, 'Decision-time evidence'));
  if (result.decisions.length) { caseNode.append(times, panel); selectDecision(result.decisions[0], controls[0]); }
  else caseNode.append(empty('No decision times available', 'Decision times require attested non-target evidence. Unreviewed references and procurement milestones do not create policy decisions.'));
  const comparisons = (input?.evidence || []).filter(evidence => evidence.signalType === 'PROCUREMENT_SIGNAL');
  const comparisonList = node('div', { className: 'evidence-list' });
  if (comparisons.length) comparisonList.append(...comparisons.map(evidenceCard));
  else comparisonList.append(empty('No retained procurement milestone', 'Comparison availability remains unresolved.'));
  caseNode.append(node('section', { className: 'comparison-context', 'aria-label': 'Comparison context outside policy inputs' }, node('h3', {}, 'Retained comparison context'), node('p', { className: 'hint' }, 'Procurement milestones below are comparison targets only. They are outside the selected decision panel and never enter the policy inputs.'), detail(`Inspect ${comparisons.length} procurement reference${comparisons.length === 1 ? '' : 's'}`, comparisonList)));
  return caseNode;
}
function reportDetail(report, verification) {
  if (verification?.integrity !== 'PASS') { integrityFailure(); return; }
  const integrity = badge('Integrity PASS');
  const replayStatus = node('p', { id: 'replay-status', role: 'status' }, 'Explicit replay has not been run in this view.');
  const result = node('section', { id: 'report-result', 'aria-label': 'Frozen report results' });
  const summary = report.summary;
  result.append(node('div', { className: 'stats' }, stat(summary.projectCount, 'Projects in frozen cohort'), stat(summary.matchedCount, 'Measured historical leads'), stat(summary.unresolvedCount, 'Unresolved cases')), node('dl', { className: 'facts' }, field('Surfaced / all projects', `${summary.surfacedCount} / ${summary.projectCount}`), field('With comparison target / all projects', `${summary.targetCount} / ${summary.projectCount}`), field('Coverage: matched / targets', summary.coverage === null ? 'Unresolved — no comparison targets' : `${summary.matchedCount} / ${summary.targetCount} = ${summary.coverage}`)), node('dl', { className: 'facts' }, field('Median measured lead (lower middle)', summary.medianLeadDays === null ? 'Historical lead unresolved' : signedLead(summary.medianLeadDays)), field('Action burden: retained decisions', summary.decisionCount), field('Policy', `${report.policyId} · ${report.policyVersion}`)), node('p', { className: 'callout' }, 'Historical lead = comparison availability − first investigation time. Negative and zero values are retained. Missing surfaces or milestones remain unresolved. Coverage is measured cases divided by cases with an attested comparison target; it is not predictive accuracy.'));
  if (summary.unresolvedCount) result.append(node('p', {}, 'Historical lead unresolved for one or more cases. Inspect each explicit status below.'));
  for (const item of report.cases) result.append(reportCase(item, report.inputs.find(project => project.id === item.projectId)));
  const replayButton = button('Verify replay', async event => {
    replayStatus.textContent = 'Recomputing retained report inputs…';
    await busy(event.currentTarget, async () => {
      try {
        const replay = await api(`/api/reports/${encodeURIComponent(report.id)}/replay`, { method: 'POST', body: {} });
        if (replay.integrity !== 'PASS' || replay.replay !== 'PASS') {
          replayStatus.textContent = 'Replay failed. Results withheld pending integrity review.';
          integrity.textContent = `Integrity ${replay.integrity || 'FAIL'}`;
          integrity.className = 'badge failure';
          result.replaceChildren(node('div', { className: 'failure-panel' }, node('h2', {}, 'Report verification failed'), node('p', {}, 'The retained report could not be verified and replayed. Healthy result cards are withheld.')));
          return;
        }
        replayStatus.textContent = 'Replay matched';
      } catch (failure) {
        replayStatus.textContent = `Replay failed. ${failure.message}`;
        if (failure.status === 422) {
          integrity.textContent = 'Verification FAIL';
          integrity.className = 'badge failure';
          result.replaceChildren(node('div', { className: 'failure-panel' }, node('h2', {}, 'Report verification failed'), node('p', {}, 'Results are withheld. Retained inputs could not be verified and replayed.')));
        }
      }
    });
  }, { id: 'verify-replay' });
  const exportError = node('p', { className: 'error', role: 'alert' });
  const exportButton = button('Export verified JSON', async event => {
    exportError.textContent = '';
    await busy(event.currentTarget, async () => {
      try {
        const exported = await api(`/api/reports/${encodeURIComponent(report.id)}/export`);
        const url = URL.createObjectURL(new Blob([JSON.stringify(exported, null, 2) + '\n'], { type: 'application/json' }));
        const anchor = node('a', { href: url, download: `trailforge-${report.id}.json` });
        document.body.append(anchor);
        anchor.click();
        anchor.remove();
        setTimeout(() => URL.revokeObjectURL(url), 1000);
      } catch (failure) {
        exportError.textContent = `Could not export report. ${failure.message}`;
        if (failure.status === 422) {
          integrity.textContent = 'Integrity FAIL';
          integrity.className = 'badge failure';
          result.replaceChildren(node('div', { className: 'failure-panel' }, node('h2', {}, 'Report integrity failure'), node('p', {}, 'Results and export are withheld.')));
        }
      }
    });
  }, { className: 'secondary', id: 'export-report' });
  const checks = node('dl', { className: 'metadata' }, field('Input hash check', verification.checks.inputHash ? 'PASS' : 'FAIL'), field('Result hash check', verification.checks.resultHash ? 'PASS' : 'FAIL'), field('Recomputed result at load', verification.checks.recomputedResult ? 'PASS' : 'FAIL'));
  main.replaceChildren(node('a', { href: '#/reports', className: 'inline-link' }, '← Retained reports'), node('p', { className: 'eyebrow' }, 'FROZEN HISTORICAL REVIEW'), node('h1', { id: 'report-title' }, report.name), node('p', { className: 'hint' }, `Frozen ${report.createdAt} · ${report.id}`), integrity, node('div', { className: 'actions' }, replayButton, exportButton), replayStatus, exportError, detail('Integrity checks and retained hashes', node('div', {}, checks, node('p', { className: 'hash' }, `Inputs: ${report.inputHash}`), node('p', { className: 'hash' }, `Results: ${report.resultHash}`))), result, detail('Frozen report JSON — includes all retained input context', node('pre', {}, JSON.stringify(report, null, 2))));
}
function integrityFailure(message = 'The retained report failed integrity checks. Results and export are withheld.') {
  main.replaceChildren(node('a', { href: '#/reports', className: 'inline-link' }, '← Retained reports'), node('div', { className: 'failure-panel', role: 'alert' }, badge('Integrity FAIL', 'failure'), node('h1', { id: 'report-title' }, 'Report integrity failure'), node('p', {}, message), button('Retry integrity check', route, { className: 'secondary' })));
}

async function route() {
  const version = ++state.routeVersion;
  main.setAttribute('aria-busy', 'true');
  main.replaceChildren(node('p', { className: 'loading', role: 'status' }, 'Loading retained records…'));
  const hash = location.hash || '#/';
  try {
    const parts = hash.slice(1).split('/').filter(Boolean).map(decodeURIComponent);
    for (const link of document.querySelectorAll('[data-nav]')) {
      const current = parts[0] === 'reports' ? 'reports' : 'projects';
      if (link.dataset.nav === current) link.setAttribute('aria-current', 'page');
      else link.removeAttribute('aria-current');
    }
    if (!parts.length) {
      const [collection, retained] = await Promise.all([api('/api/projects?includeArchived=true'), api('/api/reports')]);
      if (version !== state.routeVersion) return;
      home(collection.projects, retained.reports);
      document.title = 'TrailForge · Historical signal workbench';
    } else if (parts[0] === 'projects' && parts.length === 2) {
      const { project } = await api(projectPath(parts[1]));
      if (version !== state.routeVersion) return;
      projectDetail(project);
      document.title = `${project.name} · TrailForge`;
    } else if (parts[0] === 'reports' && parts.length === 1) {
      const { reports } = await api('/api/reports');
      if (version !== state.routeVersion) return;
      reportList(reports);
      document.title = 'Retained reports · TrailForge';
    } else if (parts[0] === 'reports' && parts.length === 2) {
      const { report, verification } = await api(`/api/reports/${encodeURIComponent(parts[1])}`);
      if (version !== state.routeVersion) return;
      reportDetail(report, verification);
      document.title = `${report.name} · TrailForge`;
    } else {
      main.replaceChildren(empty('View not found', 'Use the navigation to open the project collection or retained reports.'), node('a', { href: '#/', className: 'inline-link' }, 'Back to projects'));
    }
  } catch (failure) {
    if (version !== state.routeVersion) return;
    if (failure.status === 422) integrityFailure(failure.message);
    else main.replaceChildren(node('div', { className: 'failure-panel', role: 'alert' }, node('h1', {}, failure.status === 404 ? 'Record not found' : 'Could not load workspace'), node('p', {}, failure.message), node('div', { className: 'actions' }, button('Retry loading', route), node('a', { href: '#/', className: 'inline-link' }, 'Back to projects'))));
  } finally {
    if (version === state.routeVersion) {
      main.setAttribute('aria-busy', 'false');
      const heading = main.querySelector('h1');
      if (heading && !document.querySelector('dialog[open]')) { heading.tabIndex = -1; heading.focus({ preventScroll: true }); }
    }
  }
}
window.addEventListener('hashchange', route);
route();
