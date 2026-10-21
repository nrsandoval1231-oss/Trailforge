// TrailForge operator app (docs/UI_VISION.md, Phase 1: read-only Queue + Dossier).
// The engine decides; this file only renders /api/mining. All text goes in via text nodes.
"use strict";

const PHASE_ORDER = ["EXPLORATION", "EARLY_WORKS", "CONSTRUCTION", "COMMISSIONING", "INITIAL_OPERATION",
  "EXPANSION", "OPERATIONS", "RESTART", "CLOSURE", "UNKNOWN"];
const LABELS = {
  normal_kw: "Normal load", peak_kw: "Peak load", duty: "Duty", redundancy: "Redundancy",
  distribution_voltage_v: "Voltage", frequency_hz: "Frequency", load_profile: "Load profile",
  needed_by: "Needed by", expected_months: "Duration", grid_available: "Grid available",
  grid_ready_by: "Grid ready by", fuel_constraints: "Fuel constraints", available_fuel: "Available fuel",
  technology_constraints: "Technology constraints", altitude_m: "Altitude", temperature_c: "Temperature",
  emissions: "Emissions", site_access: "Site access", black_start: "Black start",
  model: "Contract model", package_status: "Package status", buyer_entity_id: "Buyer",
  buying_window: "Buying window", package_boundary: "Package boundary",
  name: "Project", company: "Owner", operator: "Operator", location: "Location", commodity: "Commodity",
  mining_method: "Mining method", stage: "Stage", construction_date: "Construction start",
  production_date: "Production start", epc: "EPC", epcm: "EPCM", decision_makers: "Named people",
  existing_power: "Existing power", phase: "Phase", use_case: "Use case",
};
const UNITS = { normal_kw: " kW", peak_kw: " kW", distribution_voltage_v: " V", frequency_hz: " Hz",
  expected_months: " months", altitude_m: " m", temperature_c: " °C" };
const DATES = new Set(["needed_by", "grid_ready_by", "construction_date", "production_date"]);
const GROUPS = [["demand", "Power requirement"], ["delivery", "Operating envelope & timing"], ["procurement", "Commercial"]];
const FIT_ORDER = { RESEARCH_REQUIRED: 0, DO_NOT_PURSUE: 1 };
// Gaps that decide whether a temporary-power conversation is worth having; shown first.
const KEY_GAPS = ["normal_kw", "peak_kw", "needed_by", "grid_ready_by", "expected_months", "fuel_constraints",
  "package_status", "buyer_entity_id", "model"];

let DATA = null;
const view = document.getElementById("view");
const show = (...nodes) => view.replaceChildren(...nodes.flat(Infinity).filter((n) => n !== null && n !== undefined && n !== false));

function el(tag, attrs, ...children) {
  const node = document.createElement(tag);
  for (const [key, value] of Object.entries(attrs || {})) {
    if (value === null || value === undefined || value === false) continue;
    if (key === "class") node.className = value;
    else if (key === "text") node.textContent = value;
    else if (key.startsWith("on")) node.addEventListener(key.slice(2), value);
    else node.setAttribute(key, value === true ? "" : String(value));
  }
  for (const child of children.flat(Infinity)) {
    if (child === null || child === undefined || child === false) continue;
    node.append(child instanceof Node ? child : document.createTextNode(String(child)));
  }
  return node;
}

const label = (field) => LABELS[field] || field.replace(/_/g, " ");
const day = (iso) => (iso ? String(iso).slice(0, 10) : "—");
const phaseOf = (req) => req.phase.value || "UNKNOWN";  // missing phase is UNKNOWN everywhere
const humanize = (v) => String(v).replace(/_/g, " ").toLowerCase().replace(/^\w/, (c) => c.toUpperCase());

function tag(text, kind) {
  return el("span", { class: `tag ${kind || text}`, text: humanize(text).toUpperCase() });
}

function formatValue(field, value) {
  if (value === null || value === undefined) return null;
  if (Array.isArray(value)) return value.join(", ");
  if (DATES.has(field)) return day(value);
  if (typeof value === "number") return value.toLocaleString() + (UNITS[field] || "");
  if (field === "phase" || field === "use_case" || field === "package_status" || field === "grid_available") return humanize(value);
  return String(value);
}

function evidenceBlock(claim) {
  const items = (claim.alternatives || [claim]).flatMap((c) => c.evidence || []);
  if (!items.length) return null;
  return el("details", {},
    el("summary", { text: `${items.length} source quote${items.length > 1 ? "s" : ""}` }),
    items.map((e) => el("blockquote", {},
      `“${e.quote}”`,
      el("span", { class: "meta" },
        el("a", { href: e.source_url, target: "_blank", rel: "noopener noreferrer", text: hostOf(e.source_url) }),
        ` · ${e.access} · published ${day(e.published_at)} · captured ${day(e.captured_at)} · available ${day(e.available_at)}`,
        e.event_at ? ` · event ${day(e.event_at)}` : ""))));
}

function hostOf(url) {
  try { return new URL(url).hostname.replace(/^www\./, ""); } catch { return url; }
}

// One claim: value + basis tag + method/range + collapsible evidence. Unknown is shown, never hidden.
function claimView(field, claim) {
  const shown = formatValue(field, claim.value);
  const parts = [shown === null ? el("span", { class: "muted", text: claim.basis === "CONFLICT" ? "Sources disagree" : "Unknown" }) : el("span", { text: shown }), " ", tag(claim.basis)];
  if (claim.method) parts.push(el("div", { class: "fit-note", text: `Estimate: ${claim.method}; range ${claim.range.join("–")}${UNITS[field] || ""}` }));
  if (claim.alternatives) {
    parts.push(el("ul", { class: "kv" }, claim.alternatives.map((alt) =>
      el("li", {}, el("span", { text: formatValue(field, alt.value) }), " ", tag(alt.basis), evidenceBlock(alt)))));
  } else {
    parts.push(evidenceBlock(claim));
  }
  return parts;
}

function procurementTag(q, req) {
  const pkg = req.procurement.package_status.value;
  if (q.procurement === "UNAVAILABLE") return tag(pkg || "AWARDED", "stop");
  if (q.procurement === "OPEN") return tag("OPEN", "go");
  return tag(pkg && pkg !== "UNKNOWN" ? pkg : "UNCONFIRMED", "neutral");
}

function fitTag(match) {
  return match.verdict === "DO_NOT_PURSUE" ? tag("DO NOT PURSUE", "stop") : tag("RESEARCH", "go");
}

function loadText(req) {
  const n = req.demand.normal_kw, p = req.demand.peak_kw;
  const fmt = (c) => (c.value === null ? "?" : c.value.toLocaleString()) + (c.basis === "ESTIMATE" ? "≈" : "");
  if (n.value === null && p.value === null) return null;
  return `${fmt(n)} / ${fmt(p)} kW`;
}

function allRequirements() {
  return DATA.projects.flatMap((project) => project.requirements.map((req, index) => ({ project, req, index })));
}

// ---------- Queue ----------
const state = { q: "", phase: "", hideBlocked: false };

function renderQueue() {
  const rows = allRequirements().sort((a, b) =>
    (FIT_ORDER[a.req.match.verdict] - FIT_ORDER[b.req.match.verdict])
    || (a.req.unknowns.length - b.req.unknowns.length)
    || a.req.requirement_id.localeCompare(b.req.requirement_id));
  const research = rows.filter((r) => r.req.match.verdict === "RESEARCH_REQUIRED").length;
  const open = rows.filter((r) => r.req.qualification.procurement === "OPEN").length;
  const unknowns = rows.reduce((sum, r) => sum + r.req.unknowns.length, 0);

  const tbody = el("tbody");
  const search = el("input", { type: "search", placeholder: "Filter by project, phase, owner, EPCM…", "aria-label": "Filter requirements", value: state.q });
  const phases = el("select", { "aria-label": "Phase" }, el("option", { value: "", text: "All phases" }),
    PHASE_ORDER.filter((p) => rows.some((r) => phaseOf(r.req) === p)).map((p) => el("option", { value: p, text: humanize(p) })));
  phases.value = state.phase;
  const hide = el("input", { type: "checkbox" });
  hide.checked = state.hideBlocked;

  function fill() {
    tbody.replaceChildren();
    const needle = state.q.trim().toLowerCase();
    const shown = rows.filter(({ project, req }) => {
      if (state.phase && phaseOf(req) !== state.phase) return false;
      if (state.hideBlocked && req.match.verdict === "DO_NOT_PURSUE") return false;
      if (!needle) return true;
      const p = project.project;
      return [req.requirement_id, req.phase.value, req.use_case.value, p.name.value, p.company.value, p.epcm.value, p.location.value]
        .some((v) => v && String(v).toLowerCase().includes(needle));
    });
    for (const { project, req, index } of shown) {
      const q = req.qualification;
      const href = `#/p/${encodeURIComponent(project.project_id)}/${index}`;
      const go = () => { location.hash = href; };
      tbody.append(el("tr", { class: req.match.verdict === "DO_NOT_PURSUE" ? "blocked" : null, onclick: go },
        el("td", { "data-label": "Project · phase" },
          el("a", { href, text: project.project.name.value || project.project_id, onclick: (e) => e.stopPropagation() }),
          el("span", { class: "sub", text: `${humanize(req.phase.value || "UNKNOWN")} · ${humanize(req.use_case.value || "UNKNOWN")}` })),
        el("td", { "data-label": "Status" }, tag(req.status)),
        el("td", { "data-label": "Load (normal / peak)" }, loadText(req) ? el("span", { class: "mono", text: loadText(req) }) : tag("UNKNOWN")),
        el("td", { "data-label": "Needed by" }, req.delivery.needed_by.value ? el("span", { class: "mono", text: day(req.delivery.needed_by.value) }) : tag("UNKNOWN")),
        el("td", { "data-label": "Procurement" }, procurementTag(q, req)),
        el("td", { "data-label": "Supplier fit" }, fitTag(req.match),
          el("span", { class: "sub", text: `Fuel: ${humanize(req.match.dimensions.fuel.verdict)}` })),
        el("td", { "data-label": "Evidence" }, el("span", { class: "mono", text: `${req.evidence.length} quotes` }),
          el("span", { class: "sub", text: `${req.unknowns.length} unknowns` })),
        el("td", { class: "next", "data-label": "Next action", text: q.next_action })));
    }
    if (!shown.length) tbody.append(el("tr", {}, el("td", { colspan: 8, class: "muted", text: "No requirements match these filters." })));
  }

  search.addEventListener("input", () => { state.q = search.value; fill(); });
  phases.addEventListener("change", () => { state.phase = phases.value; fill(); });
  hide.addEventListener("change", () => { state.hideBlocked = hide.checked; fill(); });
  fill();

  show(
    el("h1", { text: "Requirement queue" }),
    el("p", { class: "muted", text: `Each row is one phase-specific power requirement. Loads are never summed across phases. Supplier fit: ${DATA.supplier.supplier}.` }),
    el("div", { class: "strip" },
      stat(DATA.projects.length, "projects"), stat(rows.length, "requirements"), stat(research, "need research"),
      stat(open, "open packages"), stat(unknowns, "open unknowns")),
    el("div", { class: "controls" }, search, phases, el("label", {}, hide, "Hide do-not-pursue")),
    el("div", { class: "table-wrap" }, el("table", {},
      el("thead", {}, el("tr", {}, ["Project · phase", "Status", "Load", "Needed by", "Procurement", "Supplier fit", "Evidence", "Next action"].map((h) => el("th", { scope: "col", text: h })))),
      tbody)));
}

function stat(value, text) {
  return el("div", { class: "stat" }, el("b", { text: String(value) }), el("span", { text }));
}

// ---------- Dossier ----------
function renderProject(projectId, focus) {
  const project = DATA.projects.find((p) => p.project_id === projectId);
  if (!project) {
    show(el("p", {}, "Unknown project. ", el("a", { href: "#/", text: "Back to queue" })));
    return;
  }
  const p = project.project;
  const pending = /pending/i.test(project.reviewed_by);
  const facts = el("dl", { class: "facts" }, Object.entries(p).map(([field, claim]) =>
    el("div", { class: "fact" }, el("dt", { text: label(field) }), el("dd", {}, claimView(field, claim)))));

  const timeline = el("div", { class: "timeline", role: "list", "aria-label": "Requirements by phase" },
    PHASE_ORDER.filter((ph) => ph !== "UNKNOWN" || project.requirements.some((r) => !r.phase.value || r.phase.value === "UNKNOWN"))
      .map((ph) => {
        const reqs = project.requirements.map((r, i) => [r, i]).filter(([r]) => (r.phase.value || "UNKNOWN") === ph);
        return el("div", { class: `phase${reqs.length ? " has" : ""}`, role: "listitem" },
          el("div", { class: "name", text: humanize(ph) }),
          reqs.map(([r, i]) => el("a", { href: `#/p/${encodeURIComponent(projectId)}/${i}`, text: `${humanize(r.use_case.value || "UNKNOWN")}${r.delivery.needed_by.value ? " · " + day(r.delivery.needed_by.value) : ""}` })));
      }));

  const cards = project.requirements.map((req, i) => requirementCard(project, req, i));
  const brief = briefPanel(project);

  show(
    el("p", { class: "crumb" }, el("a", { href: "#/", text: "Queue" }), " / ", p.name.value || projectId),
    el("h1", { text: p.name.value || projectId }),
    el("p", { class: "muted mono", text: `Cutoff ${day(project.cutoff)} · reviewed by ${project.reviewed_by} · ${Object.keys(project.sources).length} sources · independent discovery credit: ${project.discovery_credit ? "yes" : "no"}` }),
    pending ? el("p", { class: "banner", text: "Review pending: these claims were drafted from public sources and have not yet been reviewed by the operator. Check each quote before relying on it." }) : null,
    facts,
    el("section", { class: "panel" }, el("h3", { text: "Phases" }), timeline),
    el("div", { class: "grid" }, cards),
    brief);
  view.querySelectorAll(":scope > section, :scope > .grid").forEach((n) => n.classList.add("spaced"));
  if (focus !== undefined) document.getElementById(`req-${focus}`)?.scrollIntoView({ block: "start" });
}

function requirementCard(project, req, i) {
  const q = req.qualification, m = req.match;
  const need = el("div", { class: "need" },
    el("ul", { class: "kv" },
      el("li", {}, el("span", { class: "k", text: "Phase" }), claimView("phase", req.phase)),
      el("li", {}, el("span", { class: "k", text: "Use case" }), claimView("use_case", req.use_case))),
    GROUPS.map(([group, title]) => {
      const known = Object.entries(req[group]).filter(([, c]) => c.basis !== "UNKNOWN");
      return [el("h3", { text: title }),
        known.length
          ? el("ul", { class: "kv" }, known.map(([f, c]) => el("li", {}, el("span", { class: "k", text: label(f) }), claimView(f, c))))
          : el("p", { class: "muted", text: "Nothing established from sources yet." })];
    }),
    unknownsView(req.unknowns),
    q.hypotheses.length ? [el("h3", { text: "Hypotheses to test" }),
      q.hypotheses.map((h) => el("div", { class: "hyp" }, el("strong", { text: "Hypothesis: " }), h.statement,
        el("div", { class: "fit-note", text: `Falsified if: ${h.falsifier}` })))] : null,
    el("div", { class: "next-action" }, "Next action: ", q.next_action));

  const fit = el("div", { class: "fit" },
    el("h3", { text: "Supplier fit (after need)" }),
    el("p", {}, el("strong", { text: m.supplier }), " ", fitTag(m)),
    el("p", { class: "fit-note", text: `${m.offering}. Engineering compliance not established. ${m.profile_basis}.` }),
    el("table", { class: "dims" }, el("tbody", {}, Object.entries(m.dimensions).map(([name, d]) =>
      el("tr", {}, el("td", { text: humanize(name) }),
        el("td", {}, tag(d.verdict, d.verdict === "INCOMPATIBLE" || d.verdict === "UNAVAILABLE" ? "stop" : d.verdict === "POTENTIAL" || d.verdict === "OPEN" ? "go" : "neutral"),
          el("div", { class: "fit-note", text: d.reason })))))));

  return el("article", { class: "req", id: `req-${i}` },
    el("header", {}, el("h2", { text: req.requirement_id }), tag(req.status), procurementTag(q, req)),
    el("div", { class: "body" }, need, fit));
}

function unknownsView(unknowns) {
  if (!unknowns.length) return null;
  const names = unknowns.map((u) => u.split(".").pop());
  const key = names.filter((n) => KEY_GAPS.includes(n) || n === "phase" || n === "use_case");
  const rest = names.filter((n) => !key.includes(n));
  return [el("h3", { text: `Deciding unknowns (${key.length} of ${names.length})` }),
    el("div", { class: "unknowns" }, key.map((n) => tag(label(n), "UNKNOWN"))),
    rest.length ? el("details", {}, el("summary", { text: `${rest.length} more engineering unknowns` }),
      el("div", { class: "unknowns" }, rest.map((n) => tag(label(n), "UNKNOWN")))) : null];
}

function briefText(project) {
  const p = project.project;
  const lines = [`DRAFT — not sent. ${p.name.value || project.project_id} (${p.company.value || "owner unknown"})`,
    `Location: ${p.location.value || "unknown"} · Stage: ${p.stage.value || "unknown"} · EPCM: ${p.epcm.value || "unknown"}`,
    `Evidence cutoff ${day(project.cutoff)}; reviewed by ${project.reviewed_by}.`, ""];
  for (const req of project.requirements) {
    const q = req.qualification;
    lines.push(`• ${req.requirement_id} — ${humanize(req.status)}; procurement ${humanize(q.procurement)}; ${req.match.supplier}: ${humanize(req.match.verdict)}`);
    for (const h of q.hypotheses) lines.push(`  Hypothesis: ${h.statement} (falsified if: ${h.falsifier})`);
    lines.push(`  Next: ${q.next_action}`);
    const keyGaps = req.unknowns.map((u) => u.split(".").pop()).filter((u) => KEY_GAPS.includes(u));
    if (keyGaps.length) lines.push(`  Ask: ${keyGaps.map(label).join(", ")}`);
  }
  return lines.join("\n");
}

function briefPanel(project) {
  const text = el("textarea", { readonly: true, "aria-label": "Research brief draft" });
  text.value = briefText(project);
  const status = el("span", { class: "copy-status", role: "status" });
  const copy = el("button", { class: "primary", type: "button", text: "Copy brief", onclick: async () => {
    try { await navigator.clipboard.writeText(text.value); status.textContent = "Copied. Nothing was sent."; }
    catch { text.select(); status.textContent = "Select-all done; copy with Ctrl+C."; }
  } });
  return el("section", { class: "panel brief spaced" }, el("h3", { text: "Research brief (copy only)" }), text, el("p", {}, copy, status));
}

// ---------- Sources ----------
function renderSources() {
  show(el("h1", { text: "Sources" }),
    el("p", { class: "muted", text: "Retained public captures behind every claim. Content is hashed; quotes must match it exactly." }),
    DATA.projects.map((project) => el("section", { class: "panel spaced" },
      el("h2", {}, el("a", { href: `#/p/${encodeURIComponent(project.project_id)}`, text: project.project.name.value || project.project_id })),
      el("div", { class: "table-wrap" }, el("table", {},
        el("thead", {}, el("tr", {}, ["Capture", "Source", "Access", "Captured", "Content hash"].map((h) => el("th", { scope: "col", text: h })))),
        el("tbody", {}, Object.values(project.sources).map((s) => el("tr", {},
          el("td", { "data-label": "Capture", class: "mono", text: s.capture_id }),
          el("td", { "data-label": "Source" }, el("a", { href: s.source_url, target: "_blank", rel: "noopener noreferrer", text: hostOf(s.source_url) })),
          el("td", { "data-label": "Access" }, tag(s.access, "neutral")),
          el("td", { "data-label": "Captured", class: "mono", text: day(s.captured_at) }),
          el("td", { "data-label": "Content hash", class: "mono", text: s.content_sha256.slice(0, 16) + "…" })))))))));
}

// ---------- Router ----------
function route() {
  if (!DATA) return;
  const parts = location.hash.replace(/^#\/?/, "").split("/").map(decodeURIComponent);
  const section = parts[0] === "sources" ? "sources" : "queue";
  for (const a of document.querySelectorAll("[data-nav]")) {
    if (a.dataset.nav === section) a.setAttribute("aria-current", "page");
    else a.removeAttribute("aria-current");
  }
  if (parts[0] === "p" && parts[1]) {
    renderProject(parts[1], parts[2] !== undefined && parts[2] !== "" ? Number(parts[2]) : undefined);
    document.title = `${parts[1]} · TrailForge`;
  } else if (section === "sources") {
    renderSources();
    document.title = "Sources · TrailForge";
  } else {
    renderQueue();
    document.title = "Queue · TrailForge";
  }
  if (!(parts[0] === "p" && parts[2])) window.scrollTo(0, 0);
}

async function start() {
  try {
    const response = await fetch("/api/mining", { headers: { Accept: "application/json" } });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    DATA = await response.json();
  } catch (error) {
    show(el("p", { class: "banner", text: `Could not load mining intelligence: ${error.message}. Restart trailforge-ui and reload.` }));
    return;
  }
  if (!DATA.projects.length) {
    show(el("h1", { text: "No projects loaded" }),
      el("p", {}, "Start with ", el("code", { text: "trailforge-ui --mining-input path/to/project.json" }), "."));
    return;
  }
  window.addEventListener("hashchange", route);
  route();
}

start();
