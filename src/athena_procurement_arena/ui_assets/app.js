"use strict";
const $ = id => document.getElementById(id);
let session, current, busy = false;
function node(tag, text, className) {
  const el = document.createElement(tag);
  if (text !== undefined) el.textContent = text;
  if (className) el.className = className;
  return el;
}
function fact(parent, label, value) {
  const item = node("div", undefined, "fact");
  item.append(node("b", label), node("span", value ?? "UNKNOWN")); parent.append(item);
}
function raw(parent, title, value) {
  const detail = node("details"); detail.append(node("summary", title), node("pre", JSON.stringify(value, null, 2))); parent.append(detail);
}
function notice(message, error = false) { $("notice").textContent = message; $("notice").dataset.error = String(error); }
async function api(path, data) {
  const options = data === undefined ? {} : {method: "POST", headers: {"Content-Type": "application/json", "X-Trailforge-Token": session.token}, body: JSON.stringify(data)};
  const response = await fetch(path, options);
  const result = await response.json();
  if (!response.ok && !result.integrity) throw new Error(result.error || "Request failed. Reload the workbench and try again.");
  return result;
}
async function task(message, work) {
  if (busy) return;
  busy = true; document.body.setAttribute("aria-busy", "true"); notice(message);
  document.querySelectorAll("button,select").forEach(el => { el.disabled = true; });
  try { await work(); } catch (error) { notice(error.message, true); }
  finally {
    busy = false; document.body.setAttribute("aria-busy", "false");
    document.querySelectorAll("button,select").forEach(el => { el.disabled = false; });
    $("run").disabled = !session?.cases.length;
    $("cases").disabled = !session?.cases.length;
    const replay = $("replay"); if (replay) replay.disabled = current?.integrity !== "PASS";
  }
}
function source(parent, fixture) {
  fact(parent, "Stored fixture status (claim)", fixture.status);
  fact(parent, "Reviewer", fixture.verified_by);
  fact(parent, "Source", fixture.source_url);
  fact(parent, "Retrieved", fixture.retrieved_at);
  fact(parent, "Review notes", fixture.verification_notes);
  fact(parent, "Outcome approval", "NOT ESTABLISHED — unsealed");
  raw(parent, "Retained source fingerprint and fixture", fixture);
}
function chooseCase() {
  const host = $("case-context"); host.replaceChildren();
  const selected = session.cases.find(c => c.id === $("cases").value);
  if (!selected) { host.append(node("p", "No configured runnable cases. Saved runs remain available.", "muted")); return; }
  host.append(node("p", "GT-003 · Morgan Hill generator maintenance. Negative mechanics case, not a temporary-power opportunity.", "muted"));
  fact(host, "Fixed policy / fixture seed", `BASELINE_A 1.0 / ${selected.fixture.scenario.seed}`);
  const detail = node("details"); detail.append(node("summary", "Source and reviewer context")); source(detail, selected.fixture); host.append(detail);
}
async function refresh() {
  const {runs} = await api("/api/runs"); const host = $("runs"); host.replaceChildren();
  if (!runs.length) host.append(node("p", "No saved runs yet. Run the configured case to create one.", "muted"));
  for (const run of runs) {
    const button = node("button", `${run.scenario}\n${run.id.slice(0, 10)}… · Integrity ${run.integrity}`, "run-item");
    button.setAttribute("aria-current", String(current?.id === run.id));
    button.addEventListener("click", () => task("Checking saved artifacts…", async () => {
      render(await api(`/api/runs/${run.id}`)); await refresh();
    })); host.append(button);
  }
}
function render(run) {
  current = run; const host = $("result"); host.replaceChildren();
  if (run.integrity !== "PASS") {
    const error = node("div", undefined, "error-panel");
    error.append(node("h2", "Saved run failed integrity verification"), node("p", run.error), node("p", `Run ${run.id}`, "mono"), node("p", "Replay is unavailable. Retain this failed run for investigation; run the case again to create a separate experiment."));
    host.append(error); notice("Integrity FAIL. No healthy result is shown.", true); return;
  }
  const heading = node("div", undefined, "result-heading"); const title = node("div");
  title.append(node("span", "Retained experiment", "eyebrow"), node("h2", run.config.scenario_id), node("div", run.id, "mono"));
  const replay = node("button", "Verify replay"); replay.id = "replay";
  replay.addEventListener("click", () => task("Replaying retained input through BASELINE_A…", async () => {
    render(await api("/api/replay", {run_id: run.id})); await refresh();
  })); heading.append(title, replay); host.append(heading);
  const statuses = node("div", undefined, "statuses");
  for (const [label, value] of [["Artifact integrity", run.integrity], ["Deterministic replay", run.replay.status], ["Evaluation", `${run.evaluation.status} / ${run.evaluation.scoring}`]]) {
    const status = node("div", label, `status${value === "FAIL" ? " fail" : ""}`); status.append(node("strong", value)); statuses.append(status);
  }
  host.append(statuses);
  host.append(node("p", `Fixed policy: ${run.config.policy_id} ${run.config.policy_version} · Seed ${run.config.seed}. Replay status applies to this server session; restart requires a new replay.`, "muted"));
  if (run.replay.status !== "NOT_RUN") raw(host, "Replay checks", run.replay);
  host.append(node("h3", "Decision-time evidence"), node("p", "Select a retained decision time. Only evidence visible then appears below. Times are recorded with their UTC offset.", "muted"));
  const strip = node("div", undefined, "timeline"); strip.setAttribute("aria-label", "Retained decision times");
  const panel = node("section", undefined, "decision"); panel.setAttribute("aria-live", "polite");
  const snapshots = run.decisions.decision_snapshots;
  snapshots.forEach((snapshot, index) => {
    const button = node("button", undefined, "tick");
    const time = node("time", snapshot.decision_time); time.dateTime = snapshot.decision_time;
    button.append(time, node("span", snapshot.action), node("span", `${snapshot.policy_input.visible_evidence.length} visible evidence records`));
    button.setAttribute("aria-pressed", String(index === 0));
    button.addEventListener("click", () => {
      strip.querySelectorAll("button").forEach(b => b.setAttribute("aria-pressed", String(b === button)));
      decision(panel, snapshot, run.decisions.records[index]);
    }); strip.append(button);
  });
  host.append(strip, panel);
  if (snapshots.length) decision(panel, snapshots[0], run.decisions.records[0]);
  else panel.append(node("p", "No decision times were retained."));
  const context = run.input.fixture_context;
  if (context) { const detail = node("details"); detail.append(node("summary", "Saved source and reviewer context")); source(detail, context.fixture); host.append(detail); }
  raw(host, "Unsealed evaluation — later evidence and declared truth", run.evaluation);
  raw(host, "Ledger and manifest", {manifest: run.manifest, records: run.decisions.records});
  raw(host, "Retained configuration and source identity", run.config);
  notice(run.replay.status === "FAIL" ? "Replay FAIL. Inspect the replay checks; artifact integrity is a separate result." : "Artifacts verified. Unsealed results do not establish forecast accuracy.", run.replay.status === "FAIL");
}
function decision(panel, snapshot, record) {
  panel.replaceChildren(node("h3", snapshot.action));
  fact(panel, "Decision time", snapshot.decision_time);
  const grid = node("div", undefined, "details-grid"); const rationale = node("div");
  rationale.append(node("h3", "Retained policy output / rationale"));
  fact(rationale, "Procurement state", snapshot.policy_output.procurement?.state);
  fact(rationale, "Target scope", snapshot.policy_output.procurement?.target_scope);
  fact(rationale, "Power status", snapshot.policy_output.power?.status);
  fact(rationale, "Power reason", snapshot.policy_output.power?.reason);
  raw(rationale, "Full retained policy output", snapshot.policy_output);
  const evidence = node("div"); evidence.append(node("h3", "Visible evidence"));
  if (!snapshot.policy_input.visible_evidence.length) evidence.append(node("p", "No evidence was visible at this decision time."));
  for (const item of snapshot.policy_input.visible_evidence) {
    const entry = node("div", undefined, "evidence"); fact(entry, "Evidence ID", item.evidence_id);
    fact(entry, "Available at", item.verified_available_at); fact(entry, "Observed at", item.observed_at);
    entry.append(node("pre", JSON.stringify(item.claims, null, 2))); raw(entry, "Provenance and full evidence", item); evidence.append(entry);
  }
  grid.append(rationale, evidence); panel.append(grid);
  fact(panel, "Decision hash", snapshot.decision_hash); raw(panel, "Frozen decision ledger record", record);
  raw(panel, "Full decision-time policy input", snapshot.policy_input);
}
$("cases").addEventListener("change", chooseCase);
$("run").addEventListener("click", () => task("Running BASELINE_A and saving a new experiment…", async () => {
  render(await api("/api/run", {case_id: $("cases").value})); await refresh();
}));
$("refresh").addEventListener("click", () => task("Checking saved runs…", async () => { await refresh(); notice("Saved run list refreshed."); }));
task("Loading configured cases and saved runs…", async () => {
  session = await api("/api/session"); $("cases").replaceChildren();
  for (const item of session.cases) { const option = node("option", `${item.fixture.fixture_id} · ${item.bundle_id}`); option.value = item.id; $("cases").append(option); }
  if (!session.cases.length) $("cases").append(node("option", "Saved runs only"));
  chooseCase(); await refresh(); notice("Ready. Choose a case or inspect a saved run.");
});
