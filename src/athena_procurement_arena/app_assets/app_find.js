// Find tab: live public-web searches stored as UNREVIEWED leads, triaged into Potential RFPs / Early projects.
// Titles, snippets and captured pages are untrusted web text: everything is rendered with textContent via el(),
// never as HTML. Relies on el/tag/stat/show/day/hostOf from app.js and TOKEN from app_ops.js.
"use strict";

const FIND = { state: null, tab: "RFP", status: "NEW", q: "", selected: new Set(), custom: "", leads: [],
  open: new Set(), captures: {}, timer: null, runState: "idle", confirming: false, nodes: {} };
const FIND_STATUS_FILTERS = [["NEW", "To triage"], ["SNOOZED", "Snoozed"], ["CAPTURED", "Captured"],
  ["DISMISSED", "Dismissed"], ["", "All"]];

async function findGet(path) {
  const response = await fetch(path, { headers: { Accept: "application/json" } });
  const body = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(body.error || `HTTP ${response.status}`);
  return body;
}

async function findPost(path, payload) {
  const response = await fetch(path, {
    method: "POST", headers: { "Content-Type": "application/json", "X-Trailforge-Token": TOKEN },
    body: JSON.stringify(payload),
  });
  const body = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(body.error || `HTTP ${response.status}`);
  return body;
}

function stopFindPolling() {
  if (FIND.timer) { clearInterval(FIND.timer); FIND.timer = null; }
}

// Links are only rendered for http(s); anything else is shown as plain text.
function safeHref(url) {
  try { const u = new URL(url); return u.protocol === "https:" || u.protocol === "http:" ? u.href : null; } catch { return null; }
}

const stamp = (iso) => (iso ? `${String(iso).slice(0, 10)} ${String(iso).slice(11, 16)} UTC` : "never");
const plural = (n, word) => `${n} ${word}${n === 1 ? "" : "es"}`;

function selectedSearches() {
  const catalog = FIND.state.catalog.filter((q) => FIND.selected.has(q.id)).reduce((sum, q) => sum + q.searches, 0);
  return catalog + (FIND.custom.trim() ? 1 : 0);
}

// ----- header stats -----
function paintStats() {
  const counts = FIND.state.counts, matrix = counts.matrix;
  const live = (kind) => matrix[kind].NEW + matrix[kind].SNOOZED + matrix[kind].CAPTURED;
  FIND.nodes.stats.replaceChildren(
    stat(counts.by_status.NEW, "new, untriaged"), stat(live("RFP"), "potential RFPs"),
    stat(live("PROJECT"), "early projects"), stat(counts.by_status.CAPTURED, "captured"),
    stat(counts.by_status.DISMISSED, "dismissed"),
    stat(FIND.state.last_run ? stamp(FIND.state.last_run.finished_at) : "never", "last search run"));
}

// ----- run panel -----
function paintRun() {
  const run = FIND.state.run, box = FIND.nodes.run;
  const running = run.state === "running";
  if (FIND.runState === "running" && !running) loadLeads();
  FIND.runState = run.state;
  const lines = [];
  if (running) {
    lines.push(el("p", { role: "status", text: `Running: ${run.done} of ${run.total} searches done` +
      `${run.current ? ` (now: ${run.current})` : ""}. ${run.new_leads} new lead${run.new_leads === 1 ? "" : "s"} so far.` }));
  } else if (run.state === "finished") {
    lines.push(el("p", { role: "status", text: `Finished ${run.done} of ${run.total} searches: ${run.seen_hits} results, ` +
      `${run.new_leads} new lead${run.new_leads === 1 ? "" : "s"}${run.errors.length ? `, ${run.errors.length} failed` : ""}.` }));
  }
  if (run.errors && run.errors.length) {
    lines.push(el("ul", { class: "kv", "aria-label": "Search errors" }, run.errors.map((e) =>
      el("li", { class: "form-error", text: `${e.query}: ${e.error}` }))));
  }
  box.replaceChildren(...lines);
  if (FIND.nodes.runButton) FIND.nodes.runButton.disabled = running || selectedSearches() === 0;
}

function paintEstimate() {
  const n = selectedSearches();
  FIND.nodes.estimate.textContent = n
    ? `≈${plural(n, "search")}, about ${n}×${FIND.state.limits.max_results} results. Uses Firecrawl credits.`
    : "Select at least one query or enter a custom query.";
  if (FIND.nodes.runButton) FIND.nodes.runButton.disabled = FIND.state.run.state === "running" || n === 0;
  if (n === 0) setConfirm(false);
}

function setConfirm(on) {
  FIND.confirming = on;
  FIND.nodes.confirm.hidden = !on;
  if (on) {
    const n = selectedSearches();
    FIND.nodes.confirmText.textContent = `Run ≈${plural(n, "search")} now? This calls Firecrawl and uses credits. ` +
      "Results are stored as unreviewed leads.";
    FIND.nodes.confirmButton.focus();
  }
}

function runPanel(state) {
  const n = FIND.nodes;
  const boxes = state.catalog.map((q) => {
    const input = el("input", { type: "checkbox", id: `q-${q.id}`, value: q.id });
    input.checked = FIND.selected.has(q.id);
    input.addEventListener("change", () => { input.checked ? FIND.selected.add(q.id) : FIND.selected.delete(q.id); setConfirm(false); paintEstimate(); });
    return el("div", { class: "check" }, input,
      el("label", { for: `q-${q.id}` }, el("strong", { text: q.id }), el("span", { class: "sub", text: q.query + (q.domains.length ? ` · site: ${q.domains.join(", ")}` : "") })));
  });
  const all = (on) => () => {
    FIND.selected = new Set(on ? state.catalog.map((q) => q.id) : []);
    n.catalogBox.querySelectorAll("input[type=checkbox]").forEach((c) => { c.checked = on; });
    setConfirm(false); paintEstimate();
  };
  n.catalogBox = el("div", { class: "catalog" }, boxes);
  const custom = el("input", { type: "text", maxlength: state.limits.custom_query_max, value: FIND.custom,
    placeholder: "e.g. temporary generator rental RFP county" });
  custom.addEventListener("input", () => { FIND.custom = custom.value; setConfirm(false); paintEstimate(); });
  n.estimate = el("p", { class: "fit-note", "aria-live": "polite" });
  n.runButton = el("button", { type: "button", class: "primary", text: "Run searches…", onclick: () => setConfirm(true) });
  n.confirmText = el("span");
  n.confirmError = el("span", { class: "form-error", role: "alert" });
  n.confirmButton = el("button", { type: "button", class: "primary", text: "Confirm and run", onclick: async () => {
    n.confirmError.textContent = "";
    try {
      const body = { query_ids: [...FIND.selected], limit: state.limits.max_results };
      if (FIND.custom.trim()) body.custom = FIND.custom.trim();
      const started = await findPost("/api/find/run", body);
      FIND.state.run = started.run;
      setConfirm(false); paintRun(); startPolling();
    } catch (error) { n.confirmError.textContent = error.message; }
  } });
  n.confirm = el("div", { class: "confirm", role: "group", "aria-label": "Confirm search run", hidden: true },
    n.confirmText, " ", n.confirmButton, " ", el("button", { type: "button", text: "Cancel", onclick: () => { setConfirm(false); n.runButton.focus(); } }), n.confirmError);
  n.run = el("div", { class: "runbox", "aria-live": "polite" });
  return el("section", { class: "panel spaced", "aria-labelledby": "run-title" },
    el("h2", { id: "run-title", text: "Run searches" }),
    el("p", { class: "fit-note", text: "Each search calls Firecrawl once (web and news, up to 10 results) and stores the hits as unreviewed leads. Nothing runs until you confirm." }),
    state.catalog_error ? el("p", { class: "form-error", role: "alert", text: state.catalog_error }) : null,
    state.catalog.length ? el("fieldset", { class: "catalog-set" }, el("legend", { text: "Catalog queries" }),
      el("p", {}, el("button", { type: "button", text: "Select all", onclick: all(true) }), " ", el("button", { type: "button", text: "Clear", onclick: all(false) })),
      n.catalogBox)
      : el("p", { class: "muted", text: "No discovery catalog loaded (start with --discovery-catalog PATH). Custom queries still work." }),
    field("Custom query (optional)", custom),
    n.estimate, el("p", {}, n.runButton), n.confirm, n.run);
}

// ----- polling -----
function startPolling() {
  if (FIND.timer || !location.hash.startsWith("#/find")) return;
  FIND.timer = setInterval(async () => {
    try {
      const status = await findGet("/api/find/status");
      const before = JSON.stringify(FIND.captures);
      FIND.state = { ...FIND.state, ...status };
      FIND.captures = status.captures;
      paintStats(); paintRun();
      if (before !== JSON.stringify(FIND.captures)) loadLeads();
      if (status.run.state !== "running" && !Object.values(status.captures).some((c) => c.state === "running")) stopFindPolling();
    } catch { /* transient; the next tick retries */ }
  }, 2000);
}

// ----- lead list -----
async function loadLeads() {
  const params = new URLSearchParams({ limit: "500" });
  if (FIND.status) params.set("status", FIND.status);
  if (FIND.q.trim()) params.set("q", FIND.q.trim());
  try {
    FIND.leads = (await findGet(`/api/find/leads?${params}`)).leads;
    paintLeads();
  } catch (error) {
    FIND.nodes.list.replaceChildren(el("p", { class: "form-error", role: "alert", text: error.message }));
  }
}

function paintLeads() {
  const by = (kind) => FIND.leads.filter((l) => l.kind === kind);
  const tabs = [["RFP", "Potential RFPs"], ["PROJECT", "Early projects"]];
  FIND.nodes.tabs.replaceChildren(...tabs.map(([kind, name]) => el("button", { type: "button", class: "tabbtn",
    "aria-current": FIND.tab === kind ? "true" : null, text: `${name} (${by(kind).length})`,
    onclick: () => { FIND.tab = kind; paintLeads(); } })));
  const shown = by(FIND.tab);
  FIND.nodes.list.replaceChildren(shown.length ? el("ul", { class: "leads" }, shown.map(leadCard))
    : el("p", { class: "muted", text: FIND.state.counts.total
      ? "No leads in this list with the current filters." : "No leads yet. Run a search above; nothing is shown until you do." }));
  const other = by("OTHER");
  FIND.nodes.otherSummary.textContent = `Other (${other.length}): not RFP-like or project-like; each card says why`;
  FIND.nodes.other.replaceChildren(other.length ? el("ul", { class: "leads" }, other.map(leadCard))
    : el("p", { class: "muted", text: "Nothing here." }));
}

function chips(label_, words) {
  return words.length ? el("span", { class: "kwgroup" }, el("span", { class: "k", text: label_ }),
    words.map((w) => el("span", { class: "kw", text: w }))) : null;
}

// A date quoted from the search snippet beside deadline wording. It is shown as an unverified quote, never as a
// status: nothing here says a solicitation is open, closed, active or current.
function deadlineChip(lead) {
  const hint = lead.matched.deadline_hint;
  if (!hint) return null;
  const word = hint.word || String(hint.text || "").split(/\W/)[0];
  const text = !hint.date ? "Date in snippet could not be read (unverified)"
    : lead.deadline_status === "past" ? `Date in snippet after "${word}" is in the past: ${hint.date} (unverified)`
      : `Date in snippet after "${word}": ${hint.date} (unverified)`;
  return el("span", { class: "kw note", title: `Snippet wording: ${hint.text}`, text });
}

function leadCard(lead) {
  const href = safeHref(lead.original_url || lead.url);
  const error = el("p", { class: "form-error", role: "alert" });
  const capture = FIND.captures[lead.id];
  const act = (text, fn, extra) => el("button", { type: "button", text, "aria-label": `${text}: ${lead.title || lead.url}`,
    disabled: extra?.disabled, onclick: async () => {
      error.textContent = "";
      try { await fn(); } catch (e) { error.textContent = e.message; }
    } });
  const setStatus = (action, days) => async () => {
    await findPost(`/api/find/leads/${lead.id}/status`, days ? { action, days } : { action });
    FIND.state.counts = (await findGet("/api/find/status")).counts;
    paintStats(); await loadLeads();
  };
  const days = el("select", { "aria-label": `Snooze length for ${lead.title || lead.url}` },
    [[3, "3 days"], [7, "7 days"], [30, "30 days"]].map(([v, t]) => el("option", { value: v, text: t })));
  days.value = "7";
  const buttons = [];
  if (lead.status === "NEW" || lead.status === "SNOOZED") {
    if (!lead.capture) buttons.push(act(capture?.state === "running" ? "Capturing…" : "Capture", async () => {
      const name = (document.getElementById("reviewer-name")?.value || reviewer()).trim();
      if (!name) throw new Error("Enter your reviewer name in the left rail first.");
      try { localStorage.setItem("tf-reviewer", name); } catch { /* storage is a convenience only */ }
      await findPost(`/api/find/leads/${lead.id}/capture`, { reviewer: name });
      FIND.captures[lead.id] = { state: "running", error: null };
      paintLeads(); startPolling();
    }, { disabled: capture?.state === "running" }));
  }
  if (lead.status === "NEW" || lead.status === "CAPTURED") {
    buttons.push(act("Dismiss", setStatus("dismiss")), days,
      act("Snooze", async () => setStatus("snooze", Number(days.value))()));
  } else if (lead.status === "SNOOZED") {
    buttons.push(act("Dismiss", setStatus("dismiss")));
  }
  if (lead.status === "DISMISSED" || lead.status === "SNOOZED") buttons.push(act("Restore", setStatus("restore")));
  const detail = el("div", { class: "detail" });
  const expanded = FIND.open.has(lead.id);
  const toggle = el("button", { type: "button", text: expanded ? "Hide details" : "Details", "aria-expanded": String(expanded),
    onclick: () => { FIND.open.has(lead.id) ? FIND.open.delete(lead.id) : FIND.open.add(lead.id); paintLeads(); } });
  if (expanded) paintDetail(lead, detail);
  const m = lead.matched;
  const explainer = m.explainer || [];
  return el("li", { class: `lead${lead.status === "DISMISSED" ? " dim" : ""}` },
    el("h4", { class: "lead-title", text: lead.title || "(untitled result)" }),
    el("div", { class: "lead-meta" },
      tag("Unreviewed", "UNKNOWN"), tag(`Heuristic: ${lead.kind === "RFP" ? "RFP-like words" : lead.kind === "PROJECT" ? "project-like words" : "not RFP-like or project-like"}`, "neutral"),
      el("span", { class: "fit-note", title: "Keyword-weight rank, highest first. A heuristic ordering, not a rating.", text: `Rank score ${lead.score}` }),
      lead.status !== "NEW" ? tag(lead.status, "neutral") : null,
      el("span", { class: "mono", text: lead.host }),
      href ? el("a", { href, target: "_blank", rel: "noopener noreferrer", text: "Open source ↗" }) : el("span", { class: "muted", text: "(link withheld)" }),
      lead.status === "SNOOZED" && lead.snooze_until ? el("span", { class: "fit-note", text: `until ${day(lead.snooze_until)}` }) : null),
    lead.snippet ? el("p", { class: "snippet", text: lead.snippet }) : null,
    el("div", { class: "why" }, el("span", { class: "k", text: "Why flagged (word match, not verification):" }),
      chips("RFP words", m.rfp), chips("Project words", m.project), chips("Power words", m.power),
      explainer.length ? el("span", { class: "kwgroup" }, el("span", { class: "k", text: "Explainer-like:" }),
        explainer.map((w) => el("span", { class: "kw note", text: w }))) : null,
      deadlineChip(lead),
      lead.kind !== "OTHER" && m.reason ? el("span", { class: "kw note", text: `Caution: ${m.reason}` }) : null,
      !m.rfp.length && !m.project.length && !m.power.length && !explainer.length
        ? el("span", { class: "muted", text: " nothing matched" }) : null),
    lead.kind === "OTHER" && m.reason ? el("p", { class: "fit-note", text: `Why this is in Other: ${m.reason}` }) : null,
    el("p", { class: "fit-note", text: `First seen ${day(lead.first_seen)} · last seen ${day(lead.last_seen)} · surfaced by: ${lead.query_ids.join("; ")}` }),
    capture?.state === "failed" ? el("p", { class: "form-error", role: "alert", text: `Capture failed: ${capture.error}` }) : null,
    el("div", { class: "actions" }, buttons, toggle), error, detail);
}

async function paintDetail(lead, box) {
  if (!lead.capture) {
    box.replaceChildren(el("p", { class: "muted", text: FIND.captures[lead.id]?.state === "running"
      ? "Capture in progress…" : "Not captured. Capture the page to read its text here and to get an input template." }));
    return;
  }
  box.replaceChildren(el("p", { class: "muted", text: "Loading captured text…" }));
  try {
    const cap = await findGet(`/api/find/leads/${lead.id}/capture`);
    box.replaceChildren(
      el("p", { class: "fit-note mono", text: `Captured ${stamp(cap.captured_at)} by ${cap.captured_by} · sha256 ${cap.content_sha256} · ${cap.total_chars.toLocaleString()} characters` }),
      el("p", { class: "banner", text: cap.notice }),
      el("pre", { class: "capture-text", tabindex: "0", "aria-label": "Captured page text (excerpt)", text: cap.text }),
      cap.truncated ? el("p", { class: "fit-note", text: "Display truncated; the full text is retained in the capture file." }) : null,
      el("p", {}, el("a", { href: `/api/find/leads/${lead.id}/template`, download: `opportunity-input-lead-${lead.id}.json`,
        text: "Download opportunity input template (empty skeleton: title, facts and review fields are blank)" })));
  } catch (error) {
    box.replaceChildren(el("p", { class: "form-error", role: "alert", text: error.message }));
  }
}

// ----- screen -----
async function renderFind() {
  stopFindPolling();
  show(el("h1", { text: "Find" }), el("p", { class: "muted", text: "Loading…" }));
  let state;
  try { state = await findGet("/api/find/state"); } catch (error) {
    show(el("h1", { text: "Find" }), el("p", { class: "banner", text: `Could not load the Find tab: ${error.message}` }));
    return;
  }
  if (!location.hash.startsWith("#/find")) return;  // navigated away while loading
  FIND.state = state; FIND.captures = state.captures; FIND.runState = state.run.state;
  const n = FIND.nodes = {};
  n.stats = el("div", { class: "strip" });
  n.tabs = el("div", { class: "tabs", role: "group", "aria-label": "Lead lists" });
  n.list = el("div", { id: "lead-list" });
  n.otherSummary = el("summary");
  n.other = el("div");
  const status = el("select", { "aria-label": "Lead status" }, FIND_STATUS_FILTERS.map(([v, t]) => el("option", { value: v, text: t })));
  status.value = FIND.status;
  status.addEventListener("change", () => { FIND.status = status.value; loadLeads(); });
  const search = el("input", { type: "search", "aria-label": "Filter leads by text", placeholder: "Filter title, snippet, URL…", value: FIND.q });
  let wait = null;
  search.addEventListener("input", () => { clearTimeout(wait); wait = setTimeout(() => { FIND.q = search.value; loadLeads(); }, 250); });
  show(el("h1", { text: "Find" }),
    el("p", { class: "banner", role: "note", text: "Unreviewed leads from public web search. Nothing here is verified, contacted, or sent." }),
    n.stats, runPanel(state),
    el("section", { class: "spaced", "aria-labelledby": "leads-title" }, el("h2", { id: "leads-title", text: "Leads" }),
      el("div", { class: "controls" }, n.tabs, status, search), n.list,
      el("details", { class: "other" }, n.otherSummary, n.other)));
  paintStats(); paintRun(); paintEstimate();
  await loadLeads();
  if (state.run.state === "running" || Object.values(state.captures).some((c) => c.state === "running")) startPolling();
}
