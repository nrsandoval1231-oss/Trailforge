"use strict";
// All source-controlled and imported content is rendered as text, never executable markup.
const $ = (id) => document.getElementById(id);
const state = {
  projects: [],
  assessments: [],
  supplier: null,
  selected: null,
  phase: 0,
  query: "",
  type: "all",
  procurement: "all",
  phaseFilter: "all",
  fit: "all",
  view: "dashboard",
};
const human = (value) =>
  String(value ?? "Unknown")
    .replaceAll("_", " ")
    .toLowerCase()
    .replace(/^./, (s) => s.toUpperCase());
function el(tag, text, cls) {
  const n = document.createElement(tag);
  if (text !== undefined && text !== null) n.textContent = text;
  if (cls) n.className = cls;
  return n;
}
function append(parent, ...children) {
  children
    .flat()
    .filter(Boolean)
    .forEach((c) => parent.append(c));
  return parent;
}
function chip(value) {
  return el("span", human(value), "chip " + String(value).toLowerCase());
}
function button(text, action, cls = "") {
  const n = el("button", text, cls);
  n.type = "button";
  n.addEventListener("click", action);
  return n;
}
function link(text, href, cls = "") {
  const a = el("a", text, cls);
  a.href = href;
  return a;
}
function sourceLink(text, url) {
  try {
    const u = new URL(url);
    if (!["https:", "http:"].includes(u.protocol))
      return el("span", text + " (source link unavailable)");
    const a = link(text, u.href);
    a.target = "_blank";
    a.rel = "noopener noreferrer";
    return a;
  } catch {
    return el("span", text + " (source link unavailable)");
  }
}
function navigate(view) {
  location.hash =
    view +
    ((view === "matching" || view === "intelligence") && state.selected
      ? "?project=" +
        encodeURIComponent(state.selected) +
        "&phase=" +
        state.phase
      : "");
}
function all() {
  return [
    ...state.assessments.map((a) => ({
      kind: "assessment",
      id: a.id,
      name: a.name,
      a,
    })),
    ...state.projects.map((p) => ({
      kind: "import",
      id: "import-" + p.index,
      name: p.project.project.name.value || p.project.project_id,
      p,
    })),
  ];
}
function selected() {
  const items = all();
  return items.find((x) => x.id === state.selected) || items[0];
}
function choose(item, view = "intelligence") {
  state.selected = item.id;
  state.phase =
    state.view === "explorer" && item.kind === "import"
      ? (TrailforgeModel.matchingPhases(item, state)[0] ?? 0)
      : 0;
  if (state.view === view) render();
  else navigate(view);
}
function notice(text) {
  return el("p", text, "notice");
}
function intro(title, subtitle) {
  return append(
    el("div", null, "intro"),
    append(
      el("div"),
      el("span", "MINING INTELLIGENCE / WORKSPACE", "eyebrow"),
      el("h1", title),
      el("p", subtitle, "muted"),
    ),
  );
}
function panel(title) {
  return append(el("section", null, "panel"), el("h2", title));
}
function projectPick() {
  const wrap = el("div", null, "phase-select");
  const label = el("label", "Project");
  label.htmlFor = "project-select";
  const s = el("select");
  s.id = "project-select";
  for (const item of all()) {
    const o = el(
      "option",
      item.name +
        (item.kind === "assessment" ? " · research assessment" : " · imported"),
    );
    o.value = item.id;
    o.selected = item.id === selected()?.id;
    s.append(o);
  }
  s.addEventListener("change", () => {
    state.selected = s.value;
    state.phase = 0;
    location.hash =
      state.view +
      "?project=" +
      encodeURIComponent(state.selected) +
      "&phase=0";
  });
  return append(wrap, label, s);
}
function phasePick(item) {
  const wrap = el("div", null, "phase-select");
  const label = el("label", "Requirement / phase");
  label.htmlFor = "phase-select";
  const s = el("select");
  s.id = "phase-select";
  item.p.project.requirements.forEach((r, i) => {
    const o = el(
      "option",
      human(r.phase.value || r.phase.basis) +
        " / " +
        human(r.use_case.value || r.use_case.basis) +
        " — " +
        r.requirement_id,
    );
    o.value = i;
    o.selected = i === state.phase;
    s.append(o);
  });
  s.addEventListener("change", () => {
    state.phase = Number(s.value);
    location.hash =
      state.view +
      "?project=" +
      encodeURIComponent(state.selected) +
      "&phase=" +
      state.phase;
  });
  return append(wrap, label, s);
}
function provenance(item) {
  if (item.kind === "assessment")
    return append(
      el("div", null, "chips"),
      chip("SECONDARY_RESEARCH"),
      chip("AS_OF_2026-10-16"),
      chip("PROCUREMENT_UNCONFIRMED"),
    );
  const p = item.p.project;
  return append(
    el("div", null, "chips"),
    ...[...new Set(Object.values(p.sources).map((s) => s.access))].map(chip),
    chip("REVIEWED"),
    el("small", "Evidence cutoff " + p.cutoff),
  );
}
function evidence(e) {
  const q = el("blockquote", e.quote);
  append(
    q,
    sourceLink("Original source", e.source_url),
    el(
      "small",
      "Access: " + e.access + " · Published: " + (e.published_at || "unknown"),
    ),
    el(
      "small",
      "Captured: " + e.captured_at + " · Observed: " + e.first_observed_at,
    ),
    el(
      "small",
      "Available: " + e.available_at + " · Event: " + (e.event_at || "unknown"),
    ),
    el("small", "Capture: " + e.capture_hash),
    el("small", "Content SHA-256: " + e.content_sha256),
  );
  return q;
}
function claim(label, c) {
  const row = el("div", null, "fact");
  const dd = el("dd");
  c = c || { value: null, basis: "UNKNOWN" };
  const v =
    c.value == null
      ? c.basis === "CONFLICT"
        ? "Unresolved source disagreement"
        : "Unknown"
      : Array.isArray(c.value)
        ? c.value.join(", ")
        : c.value;
  append(dd, el("span", v), chip(c.basis));
  if (c.method)
    append(
      dd,
      el(
        "p",
        (c.basis === "ESTIMATE" ? "Estimate method: " : "Claim method: ") +
          c.method,
      ),
    );
  const range = TrailforgeModel.claimRange(c);
  if (range !== null) dd.append(el("small", "Range: " + range));
  for (const alt of c.alternatives || []) {
    const d = el("dl");
    d.append(claim("Alternative", alt));
    dd.append(d);
  }
  if (c.evidence?.length) {
    const d = el("details");
    append(
      d,
      el("summary", "Supporting evidence (" + c.evidence.length + ")"),
      ...c.evidence.map(evidence),
    );
    dd.append(d);
  }
  return append(row, el("dt", label), dd);
}
function group(title, values) {
  const p = panel(title);
  const dl = el("dl");
  for (const [k, v] of Object.entries(values)) dl.append(claim(human(k), v));
  p.append(dl);
  return p;
}
function matchesFilter(item) {
  const text =
    item.kind === "assessment"
      ? JSON.stringify(item.a)
      : JSON.stringify(item.p.project);
  if (!text.toLowerCase().includes(state.query)) return false;
  if (state.type !== "all" && item.kind !== state.type) return false;
  if (item.kind === "import")
    return TrailforgeModel.matchingPhases(item, state).length > 0;
  return (
    state.phaseFilter === "all" &&
    state.fit === "all" &&
    (state.procurement === "all" || state.procurement === "UNCONFIRMED")
  );
}
function card(item) {
  const c = el("article", null, "card");
  append(c, provenance(item), el("h2", item.name));
  if (item.kind === "assessment")
    append(
      c,
      el("p", item.a.description),
      el("p", item.a.signal),
      button("Open project intelligence", () => choose(item), "primary"),
    );
  else {
    const p = item.p.project;
    append(
      c,
      el("p", p.project.location.value || "Location unknown"),
      el(
        "p",
        p.requirements.length +
          " distinct requirements · No combined load implied",
      ),
      button("Review phase requirements", () => choose(item), "primary"),
    );
  }
  return c;
}
function dashboard(root) {
  append(
    root,
    intro(
      "Find the opportunity. Understand the gap.",
      "Your mining power intelligence, organized for the next commercial decision.",
    ),
  );
  const hero = append(
    el("section", null, "hero"),
    el("span", "BUILT FOR SUPPLIERS. GROUNDED IN EVIDENCE.", "eyebrow"),
    el("h2", "Real projects. Clear requirements. Better conversations."),
    el(
      "p",
      "Separate a project signal from an available package. Resolve the questions that change a pursuit decision.",
    ),
    button(
      "Explore mining opportunities",
      () => navigate("explorer"),
      "primary",
    ),
  );
  root.append(hero);
  const stats = el("div", null, "stats");
  const reqs = state.projects.flatMap((p) => p.project.requirements);
  const realReqs = state.projects
    .filter((p) =>
      Object.values(p.project.sources).every((s) => s.access !== "SYNTHETIC"),
    )
    .flatMap((p) => p.evaluations);
  for (const [n, label] of [
    [state.assessments.length, "Public-source assessments"],
    [state.projects.length, "Imported project records"],
    [
      realReqs.filter((e) => e.qualification.procurement === "OPEN").length,
      "Open package statuses in imported records",
    ],
    [reqs.length, "Phase records · includes labeled demos"],
  ])
    append(
      stats,
      append(el("div", null, "stat"), el("strong", n), el("span", label)),
    );
  root.append(stats);
  append(
    root,
    append(
      el("div", null, "section-head"),
      el("h2", "Research priorities"),
      button("View all projects", () => navigate("explorer")),
    ),
    notice(
      "Five-project screen · 16 October 2026. No verified open power package in that bounded research. Priorities are analyst judgment, not win probabilities.",
    ),
  );
  const table = el("table");
  append(
    table,
    append(
      el("thead"),
      append(
        el("tr"),
        ...["Project", "Power question", "Next commercial action"].map((x) =>
          el("th", x),
        ),
      ),
    ),
  );
  const body = el("tbody");
  for (const item of all().filter((x) => x.kind === "assessment")) {
    const tr = el("tr");
    append(
      tr,
      append(
        el("td"),
        button(item.name, () => choose(item)),
        el("p", item.a.description, "muted"),
      ),
      el("td", item.a.signal),
      el("td", item.a.action),
    );
    body.append(tr);
  }
  table.append(body);
  append(root, append(el("div", null, "panel table-wrap"), table));
  if (state.projects.length) {
    append(
      root,
      append(
        el("div", null, "section-head"),
        el("h2", "Imported requirement workspace"),
      ),
    );
    const cards = el("div", null, "cards");
    all()
      .filter((x) => x.kind === "import")
      .forEach((x) => cards.append(card(x)));
    root.append(cards);
  }
}
function explorer(root) {
  append(
    root,
    intro(
      "Mining Opportunity Explorer",
      "Discover the need first. Assess supplier compatibility after the requirement is understood.",
    ),
  );
  const filters = el("div", null, "filters");
  for (const [id, label, values] of [
    [
      "type",
      "Record type",
      [
        ["all", "All records"],
        ["assessment", "Research assessments"],
        ["import", "Imported projects"],
      ],
    ],
    [
      "procurement",
      "Procurement accessibility",
      [
        ["all", "All accessibility states"],
        ["UNCONFIRMED", "Unconfirmed"],
        ["OPEN", "Explicitly open"],
        ["UNAVAILABLE", "Unavailable"],
      ],
    ],
    [
      "phaseFilter",
      "Requirement phase",
      [
        ["all", "All phases"],
        ...Array.from(
          new Set(
            state.projects.flatMap((p) =>
              p.project.requirements.map((r) => r.phase.value).filter(Boolean),
            ),
          ),
        ).map((v) => [v, human(v)]),
      ],
    ],
    [
      "fit",
      "Supplier research verdict",
      [
        ["all", "All verdicts"],
        ["RESEARCH_REQUIRED", "Research required"],
        ["DO_NOT_PURSUE", "Do not pursue"],
      ],
    ],
  ]) {
    const l = el("label", label);
    const s = el("select");
    s.id = id;
    for (const [v, t] of values) {
      const o = el("option", t);
      o.value = v;
      o.selected = state[id] === v;
      s.append(o);
    }
    s.addEventListener("change", () => {
      state[id] = s.value;
      render();
    });
    append(filters, append(l, s));
  }
  append(root, filters);
  const list = all().filter(matchesFilter);
  append(
    root,
    el(
      "p",
      list.length + (list.length === 1 ? " project shown" : " projects shown"),
      "muted",
    ),
  );
  const cards = el("div", null, "cards");
  list.forEach((item) => cards.append(card(item)));
  append(root, cards);
  if (!list.length)
    append(
      root,
      append(
        el("div", null, "panel empty"),
        el("h2", "No projects match these filters"),
        el("p", "Try a broader search or reset record type and accessibility."),
        button("Reset filters", () => {
          state.query = "";
          state.type = "all";
          state.procurement = "all";
          state.phaseFilter = "all";
          state.fit = "all";
          $("search").value = "";
          render();
        }),
      ),
    );
}
function assessmentDetail(root, item, matching = false) {
  const a = item.a;
  append(root, provenance(item), intro(a.name, a.description));
  append(
    root,
    notice(
      "Research assessment only. The original imported manifests and retained captures are not bundled; no phase-level or supplier-engine conclusion is recreated from this summary.",
    ),
  );
  const grid = el("div", null, "grid");
  append(
    grid,
    append(panel("Power-gap assessment"), el("p", a.signal)),
    append(panel("Buying chain & access"), el("p", a.buyer)),
  );
  append(
    root,
    grid,
    append(
      el("section", null, "action"),
      el("span", "NEXT COMMERCIAL ACTION · ANALYST JUDGMENT", "eyebrow"),
      el("p", a.action),
    ),
  );
  if (matching)
    append(
      root,
      append(
        panel("Supplier screening awaits imported evidence"),
        el(
          "p",
          "No match score or engineering compliance is established for this assessment. Import its authorized reviewed manifest with --mining-input PATH, then select that imported project.",
        ),
        el(
          "p",
          "Configured supplier: " +
            state.supplier.supplier +
            " / " +
            state.supplier.offering,
        ),
        el("p", state.supplier.profile_basis, "muted"),
      ),
    );
  else
    append(
      root,
      append(
        panel("Phase-specific power requirements"),
        el(
          "p",
          "Normal kW, peak kW, accepted fuels, duration and available package scope remain unconfirmed in this assessment. No aggregate MW is inferred.",
        ),
      ),
    );
  const sources = panel("Research source links");
  append(
    sources,
    el(
      "p",
      "Links retained from the 16 October research note. Linked content has not been refreshed by this interface.",
      "muted",
    ),
  );
  const ul = el("ul", null, "sources");
  a.sources.forEach((s) =>
    ul.append(append(el("li"), sourceLink(s.label, s.url))),
  );
  append(
    sources,
    ul,
    el(
      "p",
      "Assessment provenance: " + "research/mining-power-screen-2026-10-16.md",
      "muted",
    ),
  );
  root.append(sources);
}
function phaseSummary(root, item) {
  const p = item.p.project;
  const req = p.requirements[state.phase];
  const e = item.p.evaluations[state.phase];
  append(
    root,
    provenance(item),
    intro(item.name, p.project.location.value || "Location unknown"),
    phasePick(item),
    append(
      el("div", null, "chips"),
      chip(req.status),
      chip(e.qualification.procurement),
      chip(
        req.phase.basis === "CONFLICT"
          ? "CONFLICT"
          : req.phase.value || "UNKNOWN",
      ),
    ),
  );
  append(
    root,
    append(
      el("section", null, "action"),
      el("span", "NEXT RESEARCH / COMMERCIAL ACTION", "eyebrow"),
      el("p", e.qualification.next_action),
    ),
  );
  const stats = el("div", null, "stats");
  for (const [value, label, basis] of [
    [
      req.demand.normal_kw.value,
      "Normal demand · kW",
      req.demand.normal_kw.basis,
    ],
    [req.demand.peak_kw.value, "Peak demand · kW", req.demand.peak_kw.basis],
    [
      req.delivery.expected_months.value,
      "Expected duration · months",
      req.delivery.expected_months.basis,
    ],
    [
      req.procurement.package_status.value,
      "Package status",
      req.procurement.package_status.basis,
    ],
  ])
    append(
      stats,
      append(
        el("div", null, "stat"),
        el("strong", value ?? "Unknown"),
        el("span", label),
        chip(basis),
      ),
    );
  root.append(stats);
  return { p, req, e };
}
function matching(root) {
  append(
    root,
    intro(
      "Supplier Matching",
      "Explain compatibility, hard constraints and missing evidence for each phase.",
    ),
    projectPick(),
  );
  const item = selected();
  if (!item) return emptyImported(root);
  if (item.kind === "assessment") return assessmentDetail(root, item, true);
  const { req, e } = phaseSummary(root, item);
  const m = e.match;
  const profile = panel(m.supplier);
  append(
    profile,
    el("p", m.offering),
    el("p", m.profile_basis, "muted"),
    append(
      el("div", null, "chips"),
      chip(m.verdict),
      chip("ENGINEERING_COMPLIANCE_NOT_ESTABLISHED"),
    ),
  );
  root.append(profile);
  const dims = el("div", null, "dimensions");
  for (const [k, d] of Object.entries(m.dimensions))
    append(
      dims,
      append(
        el("article", null, "dimension"),
        el("h3", human(k)),
        chip(d.verdict),
        el(
          "p",
          k === "fuel"
            ? "Permitted fuels: " +
                (req.delivery.fuel_constraints.value?.join(", ") || "unknown") +
                ". Offering: " +
                state.supplier.fuels.join(", ") +
                ". Confirm delivery and storage."
            : d.reason,
        ),
      ),
    );
  root.append(dims);
  append(
    root,
    notice(
      "A research verdict is not permission to bid. Demand qualification remains independent of this supplier profile.",
    ),
    group("Requirement constraints behind this match", {
      fuel_constraints: req.delivery.fuel_constraints,
      technology_constraints: req.delivery.technology_constraints,
      needed_by: req.delivery.needed_by,
      package_status: req.procurement.package_status,
      model: req.procurement.model,
    }),
  );
}
function download(item) {
  const data =
    item.kind === "import"
      ? item.p
      : {
          basis: "SECONDARY_RESEARCH",
          as_of: "2026-10-16",
          assessment: item.a,
          original_captures_bundled: false,
        };
  const a = link("", "");
  const blob = new Blob([JSON.stringify(data, null, 2) + "\n"], {
    type: "application/json",
  });
  a.href = URL.createObjectURL(blob);
  a.download = item.id + ".json";
  document.body.append(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(a.href), 1000);
}
function intelligence(root) {
  append(
    root,
    intro(
      "Project Intelligence",
      "Read the evidence. Understand dependencies. Resolve the next decision.",
    ),
    projectPick(),
  );
  const item = selected();
  if (!item) return emptyImported(root);
  const bar = el("div", null, "toolbar");
  append(
    bar,
    button("Export evidence JSON", () => download(item)),
    button("Review supplier compatibility", () => navigate("matching")),
  );
  if (item.kind === "import")
    append(
      bar,
      link("Open printable report", "/mining/" + item.p.index, "button"),
    );
  root.append(bar);
  if (item.kind === "assessment") return assessmentDetail(root, item);
  const { p, req, e } = phaseSummary(root, item);
  append(root, group("Project overview & buying chain", p.project));
  const grid = el("div", null, "grid");
  append(
    grid,
    group("Phase-specific power requirement", {
      phase: req.phase,
      use_case: req.use_case,
      ...req.demand,
    }),
    group("Procurement & package boundaries", req.procurement),
  );
  append(
    root,
    grid,
    group("Infrastructure, delivery & operating envelope", req.delivery),
  );
  const deps = panel("Infrastructure dependencies");
  if (!e.qualification.hypotheses.length)
    deps.append(
      el("p", "No dependency hypotheses established from this record."),
    );
  for (const h of e.qualification.hypotheses)
    append(
      deps,
      chip(h.status),
      el("p", h.statement),
      el("p", "Test / falsifier: " + h.falsifier, "muted"),
      ...h.evidence.map(evidence),
    );
  root.append(deps);
  const unknowns = panel("Questions still open");
  append(
    unknowns,
    el(
      "p",
      e.qualification.unknowns.length +
        " unresolved requirement fields. Unknown does not mean no demand.",
    ),
  );
  const ul = el("ul");
  e.qualification.unknowns.forEach((x) =>
    ul.append(el("li", human(x.replace(".", " / ")))),
  );
  append(root, append(unknowns, ul));
  const sources = panel("Retained source captures");
  for (const s of Object.values(p.sources)) {
    const d = el("details");
    append(
      d,
      el("summary", s.capture_id + " · " + s.access),
      sourceLink("Original source", s.source_url),
      el("p", "Captured " + s.captured_at),
      el("code", "Capture hash " + s.capture_hash),
      el("pre", s.content),
    );
    sources.append(d);
  }
  append(
    root,
    sources,
    el(
      "p",
      "Reviewed by " + p.reviewed_by + " · Independent discovery credit: false",
      "muted",
    ),
  );
}
function emptyImported(root) {
  append(
    root,
    append(
      el("section", null, "panel empty"),
      el("h2", "No mining projects loaded"),
      el(
        "p",
        "Start this app with --mining-input PATH to an authorized reviewed manifest. Existing research assessments remain available in the Explorer.",
      ),
    ),
  );
}
function render() {
  if (!state.supplier) return;
  const params = new URLSearchParams(location.hash.split("?")[1] || "");
  if (
    params.has("project") &&
    all().some((x) => x.id === params.get("project"))
  )
    state.selected = params.get("project");
  const current = selected();
  state.phase =
    current?.kind === "import"
      ? TrailforgeModel.phaseIndex(
          current.p.project.requirements.length,
          params.get("phase"),
        )
      : 0;
  const hash = location.hash.slice(1).split("?")[0];
  state.view = ["dashboard", "explorer", "matching", "intelligence"].includes(
    hash,
  )
    ? hash
    : "dashboard";
  document.querySelectorAll("nav a").forEach((a) => {
    if (a.hash === "#" + state.view) a.setAttribute("aria-current", "page");
    else a.removeAttribute("aria-current");
  });
  const root = $("content");
  root.replaceChildren();
  ({ dashboard, explorer, matching, intelligence })[state.view](root);
  document.title = "TrailForge · " + human(state.view);
}
async function load() {
  $("status").textContent = "Loading reviewed intelligence…";
  try {
    const responses = await Promise.all([
      fetch("/api/mining"),
      fetch("/assessments.json"),
    ]);
    for (const r of responses)
      if (!r.ok)
        throw new Error("Intelligence could not be loaded (" + r.status + ").");
    const [data, research] = await Promise.all(responses.map((r) => r.json()));
    state.projects = data.projects;
    state.supplier = data.supplier;
    state.assessments = research.assessments;
    $("status").textContent = "";
    render();
  } catch (e) {
    $("status").className = "error";
    $("status").replaceChildren(
      el("span", e.message + " "),
      button("Retry", load),
    );
  }
}
$("search").addEventListener("input", (e) => {
  state.query = e.target.value.trim().toLowerCase();
  if (state.view === "explorer") render();
  else navigate("explorer");
});
window.addEventListener("hashchange", render);
load();

document.querySelector(".skip").addEventListener("click", (event) => {
  event.preventDefault();
  $("workspace").focus();
});
