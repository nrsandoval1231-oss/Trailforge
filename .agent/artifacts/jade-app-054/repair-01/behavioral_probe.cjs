"use strict";
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

class FakeElement {
  constructor(tag) { this.tagName = tag; this.children = []; this.listeners = {}; this.dataset = {}; this.isConnected = true; this.disabled = false; this.value = ""; }
  append(...nodes) { this.children.push(...nodes); }
  addEventListener(name, callback) { this.listeners[name] = callback; }
  setAttribute(name, value) { this[name] = value; }
  querySelector(selector) {
    if (selector === "input" && this.tagName === "input") return this;
    for (const child of this.children) { const found = child.querySelector?.(selector); if (found) return found; }
    return null;
  }
  querySelectorAll() { return []; }
  findButton(label) {
    if (this.tagName === "button" && this.textContent === label) return this;
    for (const child of this.children) { const found = child.findButton?.(label); if (found) return found; }
    return null;
  }
}

const repo = path.resolve(__dirname, "../../../..");
const appPath = path.join(repo, "src/athena_procurement_arena/operator_assets/app.js");
const source = fs.readFileSync(appPath, "utf8");
const sideEffects = source.indexOf(String.fromCharCode(10) + 'document.querySelectorAll("[data-route]")');
assert.notEqual(sideEffects, -1, "expected app bootstrap boundary");
const script = source.slice(0, sideEffects) + String.fromCharCode(10) + "globalThis.__hooks={candidateCard,createProject,openProject,reloadCurrent,replaceCurrent,markDraft,save,loadDiscovery};";
let confirms = 0;
let confirmResult = false;
const fakeView = new FakeElement("view");
const document = {
  getElementById(id) { return id === "view" ? fakeView : null; },
  querySelectorAll() { return []; },
  createElement(tag) { return new FakeElement(tag); },
  documentElement: { dataset: { motion: "on" } }
};
const window = { confirm() { confirms++; return confirmResult; } };
const context = vm.createContext({ document, window, structuredClone, TextEncoder, URL, apiCalls: [], saveResponse: null });
vm.runInContext(script, context, { filename: "app.js" });
vm.runInContext(`notify=()=>{};renderRoute=()=>{};refreshProjects=async()=>{};api=async (url,data)=>{apiCalls.push({url,data});return saveResponse;};`, context);
const setState = (project, isDirty, revision=1) => vm.runInContext(`current=${JSON.stringify(project)};dirty=${isDirty};draftRevision=${revision};route="detail";`, context);
const read = expr => vm.runInContext(expr, context);
const old = { id: "project-one", name: "unsaved draft", version: 1, evidence: [], organizations: [], people: [], interactions: [], fuel: { status: "NOT_STARTED", notes: "" }, _history_lengths: { evidence: 0, organizations: 0, people: 0, interactions: 0 } };

(async () => {
  setState(old, true, 3);
  confirmResult = false;
  const beforeRequests = context.apiCalls.length;
  assert.equal(await read("openProject('project-one')"), false, "same-project reopen should cancel");
  assert.equal(await read("openProject('project-two')"), false, "different-project switch should cancel");
  await read("createProject({preventDefault(){}})");
  const candidate = read(`__hooks.candidateCard({id:"candidate-1",status:"PENDING_REVIEW",source_id:"fixture",first_seen:"t",title:"Candidate",source_date:"",url:"https://example.test"})`);
  await candidate.findButton("Create project file").listeners.click();
  await read("reloadCurrent()");
  assert.equal(context.apiCalls.length, beforeRequests, "cancel paths must make no replacement requests");
  assert.equal(read("current.name"), "unsaved draft", "cancel paths must retain draft data");
  assert.equal(read("dirty"), true, "cancel paths must retain dirty state");
  const cancelPrompts = confirms;
  const cancelRequestCount = context.apiCalls.length - beforeRequests;

  let releaseReplacement;
  const pending = read(`replaceCurrent(()=>new Promise(resolve=>{globalThis.__releaseReplacement=resolve}),"detail","open this project",{confirmed:true})`);
  vm.runInContext(`current.name="edited while request pending";markDraft();`, context);
  context.__releaseReplacement({ ...old, id: "project-two", name: "server copy" });
  assert.equal(await pending, false, "late replacement should be rejected after a draft edit");
  assert.equal(read("current.id"), "project-one");
  assert.equal(read("current.name"), "edited while request pending");
  assert.equal(read("dirty"), true);

  setState(old, true, 20);
  context.saveResponse = { ...old, id: "project-one", name: "saved copy", version: 2 };
  const lateReplace = read(`replaceCurrent(()=>new Promise(resolve=>{globalThis.__releaseLate=resolve}),"detail","open project",{confirmed:true})`);
  const saving = read("save()");
  context.__releaseLate({ ...old, id: "project-two", name: "late server copy" });
  await Promise.all([lateReplace, saving]);
  assert.equal(read("current.name"), "saved copy", "pending replacement must not override save response");
  assert.equal(read("current.id"), "project-one");
  assert.equal(read("dirty"), false);
  assert.equal(read("saving"), false);

  console.log(JSON.stringify({
    result: "PASS",
    app_sha256: require("node:crypto").createHash("sha256").update(source).digest("hex").toUpperCase(),
    checks: {
      cancel_same_project_reopen_does_not_request_or_discard: "PASS",
      cancel_other_project_switch_does_not_request_or_discard: "PASS",
      cancel_create_does_not_request_or_discard: "PASS",
      cancel_candidate_admission_does_not_request_or_discard: "PASS",
      cancel_reload_does_not_request_or_discard: "PASS",
      edits_during_pending_replacement_are_retained: "PASS",
      save_invalidates_pending_replacement: "PASS"
    },
    confirm_calls: cancelPrompts,
    replacement_api_requests_on_cancel: cancelRequestCount,
    vm: process.version
  }, null, 2));
})().catch(error => { console.error(error); process.exitCode = 1; });