// Operator evidence + action loop (docs/UI_VISION.md Phases 2-3). Judgement is appended to the
// operator log via /api/operator; imports are never edited. Relies on helpers from app.js.
"use strict";

let OP = { events: 0, head: "", projects: {} };
let TOKEN = "";

async function loadOps() {
  const [session, ops] = await Promise.all([fetch("/api/session"), fetch("/api/operator")]);
  if (!session.ok || !ops.ok) throw new Error("operator log unavailable");
  TOKEN = (await session.json()).token;
  OP = await ops.json();
}

function reviewer() {
  try { return localStorage.getItem("tf-reviewer") || ""; } catch { return ""; }
}

async function record(event, errorNode) {
  const name = (document.getElementById("reviewer-name")?.value || reviewer()).trim();
  if (!name) { errorNode.textContent = "Enter your reviewer name in the left rail first."; return false; }
  try { localStorage.setItem("tf-reviewer", name); } catch { /* storage is a convenience only */ }
  const response = await fetch("/api/operator", {
    method: "POST", headers: { "Content-Type": "application/json", "X-Trailforge-Token": TOKEN },
    body: JSON.stringify({ ...event, reviewer: name }),
  });
  const body = await response.json();
  if (!response.ok) { errorNode.textContent = body.error || `HTTP ${response.status}`; return false; }
  await loadOps();
  route();
  return true;
}

const bucket = (projectId, kind) => ((OP.projects[projectId] || {})[kind] || []);
// Superseded events and decisions made on an earlier version of a changed claim are not live.
const live = (projectId, kind) => bucket(projectId, kind).filter((e) => !e.superseded && !e.stale);
const field = (label_, input) => el("label", { class: "field" }, el("span", { text: label_ }), input);

function formPanel(title, hint, fields, submit) {
  const error = el("p", { class: "form-error", role: "alert" });
  const form = el("form", { class: "ops-form", onsubmit: async (event) => {
    event.preventDefault();
    error.textContent = "";
    const ok = await submit(error);
    if (ok) form.reset();
  } }, fields, el("button", { class: "primary", type: "submit", text: "Record" }), error);
  return el("details", { class: "ops" }, el("summary", { text: title }), hint ? el("p", { class: "fit-note", text: hint }) : null, form);
}

function opsInput(name, attrs) {
  return el(attrs?.tag || "input", { name, ...attrs });
}

// ----- per-requirement evidence review -----
function reviewState(projectId, requirementId, fieldName) {
  const hit = live(projectId, "claim_review").filter((e) => e.requirement_id === requirementId && e.payload.field === fieldName);
  return hit.length ? hit[hit.length - 1] : null;
}

function claimEntries(req) {
  const rows = [["phase", req.phase], ["use_case", req.use_case]];
  for (const group of ["demand", "delivery", "procurement"]) {
    for (const [name, claim] of Object.entries(req[group])) rows.push([`${group}.${name}`, claim]);
  }
  return rows.filter(([, claim]) => claim.basis !== "UNKNOWN");
}

function reviewPanel(project, req) {
  const pid = project.project_id, rid = req.requirement_id;
  const claims = claimEntries(req);
  const rows = claims.map(([name, claim]) => {
    const current = reviewState(pid, rid, name);
    const error = el("span", { class: "form-error", role: "alert" });
    const act = (decision) => el("button", { type: "button", text: decision === "REVIEWED" ? "Mark reviewed" : "Reject",
      onclick: () => record({ kind: "claim_review", project_id: pid, requirement_id: rid, supersedes: current?.event_id,
        payload: { field: name, decision } }, error) });
    const conflict = claim.basis === "CONFLICT" ? conflictControl(pid, rid, name, claim) : null;
    return el("li", {},
      el("span", { class: "k", text: label(name.split(".").pop()) }),
      current ? [tag(current.payload.decision, current.payload.decision === "REVIEWED" ? "go" : "stop"),
        el("span", { class: "fit-note", text: ` ${current.reviewer} · ${day(current.recorded_at)}` })] : tag("UNREVIEWED", "neutral"),
      " ", act("REVIEWED"), " ", act("REJECTED"), error, conflict);
  });
  const done = claims.filter(([name]) => reviewState(pid, rid, name)?.payload.decision === "REVIEWED").length;
  return el("details", { class: "ops" }, el("summary", { text: `Evidence review — ${done} of ${claims.length} claims reviewed` }),
    el("p", { class: "fit-note", text: "Check each quote against its source before marking a claim reviewed. Recording is append-only; a new decision supersedes the old one." }),
    el("ul", { class: "kv" }, rows));
}

function conflictControl(pid, rid, name, claim) {
  const sources = [...new Set(claim.alternatives.flatMap((a) => a.evidence.map((e) => e.source)))];
  const resolved = live(pid, "conflict_resolution").filter((e) => e.requirement_id === rid && e.payload.field === name).pop();
  const select = el("select", { "aria-label": "Source you trust" }, sources.map((s) => el("option", { value: s, text: s })));
  const note = el("input", { type: "text", placeholder: "Why this source?", "aria-label": "Resolution note" });
  const error = el("span", { class: "form-error", role: "alert" });
  return el("div", { class: "conflict" },
    el("strong", { text: "Conflict — you decide: " }),
    resolved ? el("span", { text: `${resolved.payload.chosen_source} chosen by ${resolved.reviewer} (${resolved.payload.note})` }) : null,
    el("div", { class: "inline" }, select, note, el("button", { type: "button", text: "Resolve", onclick: () =>
      record({ kind: "conflict_resolution", project_id: pid, requirement_id: rid, supersedes: resolved?.event_id,
        payload: { field: name, chosen_source: select.value, note: note.value } }, error) }), error));
}

// ----- project: buying chain + activity -----
function opsDossier(project) {
  const pid = project.project_id;
  const sourceKeys = [...Object.keys(project.sources), ...live(pid, "source_note").map((e) => String(e.event_id))];
  const chain = live(pid, "buying_chain");
  const table = chain.length ? el("div", { class: "table-wrap" }, el("table", {},
    el("thead", {}, el("tr", {}, ["Organization", "Person", "Role", "Evidence"].map((h) => el("th", { scope: "col", text: h })))),
    el("tbody", {}, chain.map((e) => el("tr", {},
      el("td", { "data-label": "Organization", text: e.payload.organization }),
      el("td", { "data-label": "Person", text: e.payload.person || "—" }),
      el("td", { "data-label": "Role" }, tag(e.payload.role, e.payload.role === "FUEL_PROVIDER" ? "neutral" : "go")),
      el("td", { "data-label": "Evidence" }, `“${e.payload.evidence_quote}”`,
        el("span", { class: "sub", text: `${e.payload.evidence_source} · ${e.reviewer} ${day(e.recorded_at)}` })))))))
    : el("p", { class: "muted", text: "No buying-chain entries yet. Authority is never assumed: every entry needs a source quote." });
  const f = {};
  const chainForm = formPanel("Add buying-chain entry", "Direct buyers first. Fuel providers are accepted only after a direct buyer and a logged conversation.", [
    field("Organization", f.org = opsInput("organization", { required: true, maxlength: 200 })),
    field("Person (optional)", f.person = opsInput("person", { maxlength: 200 })),
    field("Role", f.role = el("select", {}, ["OWNER", "OPERATOR", "EPC", "EPCM", "GC", "ELECTRICAL_CONTRACTOR", "FUEL_PROVIDER", "OTHER"].map((r) => el("option", { value: r, text: humanize(r) })))),
    field("Evidence source", f.src = el("select", {}, sourceKeys.map((s) => el("option", { value: s, text: s })))),
    field("Quote supporting this role", f.quote = el("textarea", { required: true, rows: 2, maxlength: 2000 })),
  ], (error) => record({ kind: "buying_chain", project_id: pid, payload: {
    organization: f.org.value, person: f.person.value || null, role: f.role.value,
    evidence_source: f.src.value, evidence_quote: f.quote.value } }, error));
  return el("section", { class: "panel spaced" }, el("h3", { text: "Buying chain" }), table, chainForm,
    activityPanel(project));
}

function activityPanel(project) {
  const pid = project.project_id;
  const entries = live(pid, "activity").slice().reverse();
  const f = {};
  const options = project.requirements.map((r) => el("option", { value: r.requirement_id, text: r.requirement_id }));
  const form = formPanel("Log conversation or outcome", "Records what happened so forecasts can be scored later. Nothing is sent from here.", [
    field("Requirement", f.req = el("select", {}, options)),
    field("Type", f.entry = el("select", {}, el("option", { value: "CONVERSATION", text: "Conversation" }), el("option", { value: "OUTCOME", text: "Outcome" }))),
    field("Outcome (outcomes only)", f.outcome = el("select", {}, ["QUALIFIED", "DISQUALIFIED", "WON", "LOST", "UNRESOLVED"].map((o) => el("option", { value: o, text: humanize(o) })))),
    field("Counterparty (optional)", f.who = opsInput("who", { maxlength: 200 })),
    field("When", f.when = el("input", { type: "datetime-local", required: true })),
    field("What happened", f.summary = el("textarea", { required: true, rows: 3, maxlength: 2000 })),
  ], (error) => record({ kind: "activity", project_id: pid, requirement_id: f.req.value, payload: {
    entry: f.entry.value, outcome: f.entry.value === "OUTCOME" ? f.outcome.value : null,
    counterparty: f.who.value || null, summary: f.summary.value,
    occurred_at: new Date(f.when.value).toISOString() } }, error));
  return el("div", {}, el("h3", { text: "Activity" }),
    entries.length ? el("ul", { class: "kv" }, entries.map(activityRow)) : el("p", { class: "muted", text: "Nothing logged yet." }), form);
}

function activityRow(e) {
  return el("li", {}, el("span", { class: "mono", text: day(e.payload.occurred_at) }), " ",
    e.payload.outcome ? tag(e.payload.outcome, e.payload.outcome === "WON" || e.payload.outcome === "QUALIFIED" ? "go" : "neutral") : tag("CONVERSATION", "neutral"),
    el("span", { class: "sub", text: `${e.requirement_id}${e.payload.counterparty ? " · " + e.payload.counterparty : ""} · logged by ${e.reviewer}` }),
    el("div", { text: e.payload.summary }));
}

// ----- brief addendum (copy only) -----
function opsBriefLines(project) {
  const pid = project.project_id;
  const lines = [];
  const chain = live(pid, "buying_chain");
  if (chain.length) {
    lines.push("", "Buying chain (operator-recorded):");
    for (const e of chain) lines.push(`  - ${e.payload.organization}${e.payload.person ? " / " + e.payload.person : ""} — ${humanize(e.payload.role)} [${e.payload.evidence_source}]`);
  }
  const activity = live(pid, "activity");
  if (activity.length) {
    lines.push("", "Activity:");
    for (const e of activity) lines.push(`  - ${day(e.payload.occurred_at)} ${e.payload.outcome ? humanize(e.payload.outcome) : "Conversation"}: ${e.payload.summary}`);
  }
  return lines;
}

// ----- Evidence screen -----
function renderEvidence() {
  const blocks = DATA.projects.map((project) => {
    const pid = project.project_id;
    const all = project.requirements.flatMap((req) => claimEntries(req).map(([name, claim]) => ({ req, name, claim })));
    const unreviewed = all.filter(({ req, name }) => !reviewState(pid, req.requirement_id, name));
    const conflicts = all.filter(({ claim, req, name }) => claim.basis === "CONFLICT"
      && !live(pid, "conflict_resolution").some((e) => e.requirement_id === req.requirement_id && e.payload.field === name));
    const notes = live(pid, "source_note");
    const f = {};
    const noteForm = formPanel("Capture a source", "Pasted excerpts are hashed and first-observed now. They do not become claims until a requirement cites them; mark confidential material as such.", [
      field("URL", f.url = el("input", { type: "url", required: true, maxlength: 1000 })),
      field("Title", f.title = el("input", { type: "text", required: true, maxlength: 300 })),
      field("Access", f.access = el("select", {}, el("option", { value: "PUBLIC", text: "Public" }), el("option", { value: "CONFIDENTIAL", text: "Confidential" }))),
      field("Published (optional)", f.pub = el("input", { type: "date" })),
      field("Excerpt", f.excerpt = el("textarea", { required: true, rows: 4, maxlength: 3500 })),
    ], (error) => record({ kind: "source_note", project_id: pid, payload: {
      url: f.url.value, title: f.title.value, access: f.access.value, excerpt: f.excerpt.value,
      published_at: f.pub.value ? new Date(f.pub.value + "T00:00:00Z").toISOString() : null } }, error));
    return el("section", { class: "panel spaced" },
      el("h2", {}, el("a", { href: `#/p/${encodeURIComponent(pid)}`, text: project.project.name.value || pid })),
      el("div", { class: "strip" }, stat(all.length - unreviewed.length, "claims reviewed"), stat(unreviewed.length, "awaiting review"),
        stat(conflicts.length, "open conflicts"), stat(notes.length, "captured notes")),
      unreviewed.length ? el("div", { class: "table-wrap" }, el("table", {},
        el("thead", {}, el("tr", {}, ["Requirement", "Claim", "Basis"].map((h) => el("th", { scope: "col", text: h })))),
        el("tbody", {}, unreviewed.slice(0, 40).map(({ req, name, claim }) => el("tr", {},
          el("td", { "data-label": "Requirement" }, el("a", { href: `#/p/${encodeURIComponent(pid)}/${project.requirements.indexOf(req)}`, text: req.requirement_id })),
          el("td", { "data-label": "Claim", text: `${label(name.split(".").pop())}` }),
          el("td", { "data-label": "Basis" }, tag(claim.basis))))))) : el("p", { class: "muted", text: "Every claim has a review decision." }),
      notes.length ? el("ul", { class: "kv" }, notes.map((e) => el("li", {}, el("span", { class: "k mono", text: `#${e.event_id}` }), tag(e.payload.access, e.payload.access === "CONFIDENTIAL" ? "stop" : "neutral"), " ",
        e.payload.access === "CONFIDENTIAL" ? e.payload.title : el("a", { href: e.payload.url, target: "_blank", rel: "noopener noreferrer", text: e.payload.title }),
        el("span", { class: "sub mono", text: `sha256 ${e.payload.excerpt_sha256.slice(0, 16)}… · first observed ${day(e.recorded_at)} · ${e.reviewer}` })))) : null,
      noteForm);
  });
  show(el("h1", { text: "Evidence" }),
    el("p", { class: "muted", text: `Operator log: ${OP.events} events, chain head ${OP.head.slice(0, 12)}…. Decisions are append-only; the imports are never edited.` }),
    blocks);
}

// ----- Activity screen -----
function renderActivity() {
  const rows = DATA.projects.flatMap((p) => live(p.project_id, "activity").map((e) => ({ p, e })))
    .sort((a, b) => b.e.payload.occurred_at.localeCompare(a.e.payload.occurred_at));
  const count = (o) => rows.filter(({ e }) => e.payload.outcome === o).length;
  show(el("h1", { text: "Activity" }),
    el("p", { class: "muted", text: "Conversations and outcomes, newest first. Log them from the project dossier." }),
    el("div", { class: "strip" }, stat(rows.length, "entries"), stat(count("QUALIFIED"), "qualified"), stat(count("WON"), "won"), stat(count("LOST") + count("DISQUALIFIED"), "lost / disqualified")),
    rows.length ? el("ul", { class: "kv" }, rows.map(({ p, e }) => el("li", {},
      el("a", { href: `#/p/${encodeURIComponent(p.project_id)}`, text: p.project.name.value || p.project_id }), " ", activityRow(e))))
      : el("p", { class: "muted", text: "No activity logged yet." }));
}
