# TrailForge Audit

Audit date: 2026-10-01. Implementation baseline: local main `c216b5efbc1daeae5e62f28276f5d35f3d7b04c9`. Clean before audit commands. Findings below describe that baseline; Slice 1 validation is recorded separately. Repository source and fresh checks take precedence over historical progress claims.

## 1. What TrailForge Is

TrailForge is a local, deterministic procurement-policy research tool for Nick or a procurement analyst who can review source evidence. The core job is to test how a policy interprets a project timeline using only evidence available at each point, freeze its predictions/actions, and compare them with known outcomes without future leakage. A successful session loads a chosen case, runs a named policy, inspects its decisions and separate evaluation dimensions, saves the experiment, and reproduces it after restarting.

The controlling Build Packet #0 describes a research Arena, not a production lead-generation service. The repository also contains useful but adjacent temporary-power RFP screening and reviewed project-trace tools. Those are not a substitute for the Arena loop. No real-world forecast improvement is established by synthetic test counts.

The brief's illustrative browser-UI acceptance is adapted to the actual CLI product: Build Packet #0 explicitly says Arena first and excludes UI scope creep. No browser interface, authentication service, or hosted product currently exists. A future GUI is a separate scope decision.

## 2. Current State

**Approximately 60% of the small usable CLI V1**, a judgment estimate, not a computed completion metric. The domain engine, input serialization, ledger, replay verifier and many boundary tests exist; the operator-facing experiment loop is disconnected and its durable explanatory output is incomplete. Full Build Packet #0 and real-world validation have a larger gap than this small milestone. Do not reinterpret this estimate as 60% predictive accuracy or acceptance of the original packet.

Git evidence:

- Local main: `c216b5e`; audited feature branch subsequently created as `codex/trailforge-v1-audit-slice1` so main is unchanged.
- Refreshed remote main: `cb0b2419f9e2c627d0df2b180a28d868f12ae014`; local and remote diverge by **29 local-only / 1 remote-only commits**. Initial cached origin/main was stale.
- Remote-only commit is PR #2, removing completed packet files and correcting docs. The large runtime diff between the two tips reflects missing local hardening on the remote, not runtime deletion by PR #2 itself.
- No open PRs or issues returned by authenticated GitHub CLI. One worktree. All 11 non-main local branch tips are ancestors of local main: nine codex repair/audit branches, `master`, and `prospective-outcome-seal-018`. They are potential local branch cleanup candidates after retained-work review; none was deleted. Old remote discovery branch `origin/claude/repo-audit-71kufq` is outside the chosen path; its work is not silently discarded.
- Latest remote CI run `36793116570` failed with an empty steps list and no assigned runner. Check-run annotation access returned HTTP 403, so the current root cause is UNKNOWN. Prior docs cite billing; that is not fresh proof of this run's cause.

Structure at baseline: 240 tracked files; 144 under `.agent`, 32 source files, 28 test files, 17 docs, seven research files, four scenario files, one schema, two validation scripts. No tracked pyc/egg-info/env files were found. Generated caches and the local `.firecrawl` data folder are ignored. Canonical specification is retained outside the repository at the archived Nucleus path named in `docs/PRD_ALIGNMENT.md`, a portability weakness.

## 3. What Works

**A — WORKING + USABLE, within bounded local mechanics scope:**

- Complete local gate: `uv run --python 3.11 --with pytest --with ruff python scripts/validate.py`: exit 0, **182 tests passed**, source compilation, Ruff, and three fixture-bundle validations passed.
- Python packaging: `uv build --out-dir .firecrawl/audit-20261001/dist`: exit 0, source distribution and wheel built. Runtime has no declared third-party dependencies; optional YAML loading requires undeclared PyYAML. No configured static typecheck exists; compilation is not a typecheck.
- Seeded campaign: `batch --count 1000 --seed 30`: exit 0, 2,000 policy runs, zero counted ledger failures. Both policies made zero actionable decisions. This proves mechanics throughput, not useful commercial predictions or all invariant coverage.
- File-backed fixture loading and explainable screening: all three real checked-in bundles produced one visible NOT_CURRENT record each, with provenance and reason codes. Holdout availability was false in every bundle.
- Tests exercise temporal visibility, tenant/public permission gates, immutable ledger hashes, input/source fingerprints, review queues, trace/cohort binding, seals, retained negative knowledge and replay tampering. This is specific tested behavior, not blanket security certification.
- Direct five-case counterfactual execution with seed 21: extension, duplicate, unknown supply and private procurement cases pass; cancellation fails visibly in the suite result.

## 4. What Is Incomplete

**B — BUILT BUT INCOMPLETE:**

- `runner.py` can save/load manifests and verify scenario/result/source-commit hashes, but the CLI does not connect those functions to real replay.
- `ScenarioDsl` loads local JSON, but CLI scenario mode has no scenario-file parameter. The checked-in JSON schema is not automatically enforced by the loader.
- Frozen decisions are held in memory during a world run. CLI output includes counts and a manifest, not a durable full decision trace plus evaluator report. Many adjacent workflows do persist JSON, so storage is fragmented rather than absent everywhere.
- `BASELINE_A` implements the shared policy methods, while five controls remain callbacks. Broad comparison and optimization exist before one user-facing experiment loop is finished.
- Evaluator components explicitly contain unavailable/unknown values; complete discovery semantics, calibration, numeric ground truth, cost and action sufficiency remain partial.
- Source-backed fixtures are retained but unsealed; no checked-in sealed historical holdout or real prospective outcome cohort proves predictive value.
- Documentation is extensive, but current-state notes mix historic counts, superseded next steps and later fixes. Several architecture narratives describe a larger system than the actual 32-file package.

## 5. What Is Broken / Unverified

**C — BROKEN / UNVERIFIED:**

1. **Misleading replay:** `replay --seed 21` returns PASS with a newly generated synthetic scenario, new timestamp and empty artifact paths. It never loads a prior manifest. This is a confirmed workflow defect.
2. **No user-selected scenario path:** `scenario` falls through to the same synthetic generator. A user cannot supply their scenario using this entry point.
3. **Missing durable explanation:** terminal output cannot restore the frozen decision chain/evaluator result for inspection after restart.
4. **Cancellation sensitivity fails:** five-case suite reports `passed: false` for cancellation. The CLI `counterfactual` executes only the extension probe and unconditionally appends PASS, so it does not represent the full suite.
5. **Evidence identity is partial:** `runner.py` obtains Git HEAD from process cwd, does not bind the dirty source tree, and does not fully establish policy/config equivalence. A matching commit is not proof of identical executable code.
6. **Tournament CLI has illustrative metrics:** it passes literal recall/precision dictionaries and `holdout_available=False` to the gate. QUARANTINE is appropriately conservative, but this is not an empirical candidate promotion workflow.
7. **Currentness is a stored label:** `VerifiedFixture.current` tests OPEN/ACTIVE/SOURCES_SOUGHT, without an as-of freshness/closing-date check. Do not treat a saved OPEN label as live opportunity verification.
8. **Public capture boundary is incomplete:** `_public_url` checks a few literal private ranges and names, not all private IPv4/IPv6 ranges, DNS resolutions or redirects. No live capture/security proof was run; paid acquisition is unnecessary for this audit.
9. CI failed before tests; local and remote tips diverge. No remote certification of this local implementation. Current check annotations are inaccessible with this token.
10. Dependency advisory scan with `uv run --python 3.11 --with pytest --with ruff --with pip-audit pip-audit --skip-editable --progress-spinner off` returned exit 0, no known vulnerabilities for the resolved environment; editable TrailForge itself was skipped. An isolated `uv run --no-project --with <built-wheel> trailforge smoke --seed 21` passed for the baseline wheel. This is not clean-machine full V1/restart acceptance or a security certification.

Application inventory: local CLI/library only; no frontend, HTTP API server, database, authentication, scheduler/background jobs or deployment service. Python objects hold live state; JSON files retain selected evidence and results. Firecrawl CLI is the sole explicit acquisition integration. There is no model call in the verified campaign. Local command execution is the intended delivery path.

## 6. What Should Be Deleted or Simplified

**D — DEAD WEIGHT FOR V1, not a license to destroy evidence:**

- Consolidate `.agent/CURRENT_STATE.md` to one current pointer; archive its existing bytes before replacing. Stop producing overlapping chronological status narratives. Keep exact reviews and failed attempts accessible through Git/history or an archive.
- Reduce the primary README path from 29 mixed-purpose modes and roughly 60 global flags to a short run/save/replay guide. Full parser/subcommand rework is optional; fix behavior first.
- Pause `athena_optimizer.py` search expansion, tournament breadth and new mutations until one retained case has an inspectable outcome. Existing tested code can remain dormant; deletion has no immediate operational benefit.
- Reconcile overlapping `ARCHITECTURE.md`, `ARENA_ARCHITECTURE.md`, foundation and readiness docs only where they misdirect execution. Do not spend Slice 1 rewriting all documentation.
- Ignore generated `build/` and `dist/` products. No tracked generated binaries were found to delete.
- Keep `athena_arena/contracts.py`: it is actively imported for canonical hashing, not an abandoned second runtime. Moving it offers little V1 value.
- Keep raw captures, fixture provenance, review records and existing tests. Remote PR #2 cleanup can be reconciled later without sacrificing local hardening. No branches or evidence were removed by this audit.

## 7. Architecture Assessment

The useful core is already small: `ScenarioDsl -> TemporalWorld -> policy -> FrozenDecisionLedger -> evaluate_replay`, with `runner.py` managing manifest metadata. The repository is a Python package with flat modules, not a distributed application.

Keep that core and provide one direct CLI path that accepts a file, retains its run, explains the output and verifies replay. Use local files; no web server, database, queue, plugin framework or new orchestration layer is needed. Preserve explicit UNKNOWN values, timestamp boundaries and research-only authority. A human reviewer remains responsible for source attestation; automated parsing is not independent verification.

## 8. Decision

**SIMPLIFY-REFACTOR.** Salvage the current engine. Passing deterministic checks, working serialization and existing replay functions make a new repository objectively unnecessary. The fastest gain is connecting existing functions and removing misleading success behavior. Treat remote integration as a separate controlled operation because overwriting local main would lose tested fixes.

## 9. Frozen TrailForge V1

One researcher runs one reviewed local procurement case through BASELINE_A, sees time-ordered decisions with source basis and unavailable metrics clearly marked, saves input/trace/evaluation/manifest, restarts, verifies the retained run, and repeats with another case. It must report failure on tampering, mismatched input or unverifiable source identity.

Includes local JSON input, deterministic processing, explicit research-only output, durable inspectable artifacts, a clear command interface, restart verification and a documented runnable package. Unsealed cases may support mechanics inspection but must not yield historical-accuracy claims.

Excludes browser UI, live lead generation, autonomous extraction/review, paid integrations, commercial execution, submissions, hosted multiuser authentication, policy promotion, model optimization and distributed scaling. This small usable milestone does not waive the original Build Packet #0 requirements or certify its completion. Real predictive validation still requires independent outcome evidence.

## 10. Biggest Blocker

**The existing engine is not exposed as an honest, repeatable user-selected experiment loop.** Fixing missing real replay is the first bounded step. Lack of sealed evidence is separately the biggest blocker to predictive validation; building more synthetic campaigns cannot resolve it.

## 11. Build Slices

Strict order; only Slice 1 is authorized for implementation now.

### Slice 1 — Stabilize scenario/save/replay

- Objective: make file-input scenario execution and saved-manifest verification accessible and truthful.
- Files: `src/athena_procurement_arena/cli.py`, `tests/procurement_arena/test_cli.py`, `README.md`, `.gitignore`; bounded packet/evidence alongside.
- Requirements: require explicit scenario input and output for scenario mode; load saved manifests in replay; use existing verifier; reject unsupported policy/config, missing or invalid input and existing output; propagate failed checks; keep smoke explicitly synthetic.
- Do not touch: policy/evaluator semantics, source evidence, provider configuration, canonical requirements, remote integration, or UI.
- Validation: focused CLI tests, complete `scripts/validate.py` gate, `git diff --check`, separate-process source-backed scenario/save/replay and tamper/rejection checks.
- Acceptance: persisted manifest reloads, matching replay passes, changed/tampered inputs fail nonzero, output cannot be overwritten, existing behavior outside the bounded interface retains passing tests. Document existing source-tree identity limitations.

### Slice 2 — Retain decisions and explain the result

- Objective: one readable experiment result that exposes what happened at each timestamp.
- Files/systems: `runner.py`, `cli.py`, `evaluation.py` only as needed for serialization, runner/CLI/evaluation tests, README.
- Requirements: save exact input snapshot, decision ledger, separate evaluator dimensions and manifest in one run directory; refuse overwrites; bind every artifact hash; show UNKNOWN/unavailable and research-only status. Bind source identity to the actual implementation, not an unrelated cwd; reject unsupported config/policy replay.
- Do not touch: new policies, external capture, UI, fixture sealing or promotion.
- Validation: `uv run --python 3.11 --with pytest python -m pytest tests/procurement_arena/test_runner.py tests/procurement_arena/test_cli.py tests/procurement_arena/test_evaluation.py -q`; complete gate and diff check.
- Acceptance: a fresh process loads and inspects decisions/evaluation without rerunning; replay verifies all saved artifacts; any changed artifact fails; moving cwd cannot misattribute source identity.

### Slice 3 — One reviewed real case

- Objective: execute a small real source-backed chronological case with no fabricated availability or outcome facts.
- Files/systems: `scenarios/fixtures/verified/`, narrowly necessary `fixtures.py`/CLI selection, fixture/CLI tests; one case evidence note.
- Requirements: use retained source spans and hashes, reviewer-approved availability, explicit unknown outcomes, multi-step chronology where supported; connect the selected fixture directly to the experiment loop. Only an independently sealed outcome may unlock scoring. Fix cancellation behavior only with a bounded reproduction and agreed contract.
- Do not touch: synthetic truth to improve scores, guessed dates, unattended discovery, fabricated reviewer seals or automatic promotion.
- Validation: `validate-bundle --bundle <reviewed-case>`, focused fixture/policy/CLI tests, complete gate; run/save/replay on the reviewed case.
- Acceptance: source facts trace to exact evidence, future material stays hidden, missing evidence is visible, unsealed input remains unscored; a reviewer can explain every consequential output. Missing independent evidence is an explicit external prerequisite, not a reason to forge a fixture.

### Slice 4 — Local V1 acceptance and delivery

- Objective: prove the user loop in a clean environment and after process restart.
- Files/systems: `pyproject.toml`, `scripts/validate.py`, integration tests, minimal quickstart, CI only if an actual code/config fault is found.
- Requirements: portable install, command-level acceptance using the reviewed case, tamper/error paths, repeat run and retained state. Reconcile source/docs with remote cleanup only with integration authority; preserve the 29 local hardening commits and all required evidence.
- Do not touch: hosted deployment, billing, credentials, broader PRD requirements, speculative polish.
- Validation: wheel build/install in a fresh environment; full local gate; complete acceptance below; relevant dependency advisory scan; exact-candidate independent review. Remote CI is reported separately.
- Acceptance: fresh user can execute documented steps without Python snippets/manual internal API assembly, retain and restore results, see honest failures and run a second case. No claim of forecast quality beyond reviewed evidence.

## 12. Acceptance Test

1. Install the frozen candidate in a clean Python 3.11 environment and open its real interface, the terminal CLI.
2. Select a reviewed, local source-backed procurement case with known availability timestamps and an explicitly unsealed/unknown outcome unless independently sealed evidence exists.
3. Run BASELINE_A through the declared timeline into a new run directory using the documented command.
4. Inspect the visible-evidence IDs, frozen predictions/actions and separate evaluation results. Later evidence must be absent from earlier decisions; unsupported metrics/outcomes must stay UNKNOWN or unavailable.
5. Confirm the directory retains the exact input, complete decision ledger, evaluator report and hash-bound manifest; unsealed data must not be reported as historical forecast accuracy.
6. Exit the process. Start a fresh process from the documented installation and reopen the retained result.
7. Replay the saved experiment; the input/decision/result/source identity checks must pass against the frozen candidate.
8. Copy the result to a test directory, change one evidence fact or retained decision, and verify nonzero failure without rewriting the originals.
9. Run the case again into a new directory; deterministic result hashes must agree. An attempted reuse of the original output path must fail and preserve its bytes.
10. Complete all steps without mocks, hidden API assembly, fabricated seals or external execution. Independent review must qualify acceptance as small CLI V1, not full Build Packet #0 or predictive validation.

This full acceptance does not pass at the audit baseline. Slice 1 addresses only the entry-point/save/replay portion.

## 13. Stop Doing

Pause optimization/threshold search, new scenario families, larger throughput campaigns, generic agent machinery, repeated full architecture audits, broad documentation cleanup, autonomous discovery, extra RFP/trace workflow expansion, UI/dashboard design, cloud hosting and cosmetic refactors. Preserve existing work; resume only when it directly supports the acceptance test. Do not delete unused-looking evidence to make the repository appear finished.

## 14. Immediate Next Action

Implement Slice 1 on `codex/trailforge-v1-audit-slice1`, reusing the existing DSL and manifest verifier. One Luna owns the four implementation files; the controller reruns deterministic checks and Sol reviews the exact frozen candidate. Stop after its handoff. No automatic Slice 2, push, merge, deployment, branch deletion or paid acquisition.

### Slice 1 completed locally — 2026-10-01

The action above is now implemented and independently accepted for its bounded scope. `scenario --scenario-file <json> --output <manifest>` uses the user's scenario and refuses overwrite. `replay --scenario-file <json> --manifest <saved-manifest>` verifies the saved run and returns failure on invalid input or mismatched checks. Seed-only pseudo-replay is removed; `smoke` remains explicit synthetic mechanics. Research-only boundaries and existing runner identity limitations remain.

Implementation files changed: `src/athena_procurement_arena/cli.py`, `tests/procurement_arena/test_cli.py`, `README.md`, `.gitignore`. Audit, graph, packet and review/handoff artifacts are additional local documentation. No existing evidence or branches were deleted. Changes are uncommitted on the feature branch; main remains `c216b5e`.

Controller validation on the frozen final code:

- `uv run --python 3.11 --with pytest --with ruff python scripts/validate.py`: exit 0; **189 tests**, compilation, Ruff and all three bundle checks pass.
- `git diff --check`: exit 0.
- `uv run --python 3.11 python -m athena_procurement_arena scenario --scenario-file .firecrawl/audit-20261001/controller-gt003-scenario.json --output .firecrawl/audit-20261001/controller-gt003-manifest.json`: exit 0; three observations, final state OUT_OF_SCOPE.
- `uv run --python 3.11 python -m athena_procurement_arena replay --scenario-file .firecrawl/audit-20261001/controller-gt003-scenario.json --manifest .firecrawl/audit-20261001/controller-gt003-manifest.json`: exit 0; scenario_hash, result_hash and source_commit checks all true.
- `uv build --quiet --out-dir .firecrawl/audit-20261001/final-dist`: exit 0. Isolated `uv run --no-project --python 3.11 --with <final-wheel> trailforge replay` against the same retained input/manifest: exit 0, all checks true.
- Independent Sol review first returned FIX for non-object manifest JSON; Luna repaired it with four parameterized regressions. Final `REVIEW-2.md` returned **PASS**, bound to the four implementation-file hashes in `REVIEW.json`.

Remaining failures: cancellation sensitivity, full durable decision/evaluation output, complete source identity, real sealed-outcome evidence, incomplete public-URL checks, and remote CI/divergence remain as listed above. No Slice 1 gate remains failed. No claim of full V1 acceptance, full Build Packet #0 acceptance, forecast quality, remote acceptance or deployment is made.

**Exact next slice: Slice 2 — retain decisions and explain the result. It has not started.**


---

## 13. Owner Product Reset — 2026-10-01

This audit's earlier frozen-V1 roadmap is superseded as the active product roadmap by the owner direction captured in `docs/PRD_ALIGNMENT.md` and `.agent/CURRENT_STATE.md`.

The existing engine should be preserved, but the next objective is no longer completion of every historical V1 packet. The active objective is to prove **early-project lead-time advantage** on approximately 20-50 real historical power projects.

The target commercial sequence is:

`EARLY SIGNAL -> PROJECT -> POWER-GAP HYPOTHESIS -> DIRECT BUYING CHAIN -> CUSTOMER CONTACT -> VERIFIED REQUIREMENT -> FUEL STRATEGY`

TrailForge is the historical proving ground. Validated signal families should later feed GridLens as the live discovery surface. Fuel providers are downstream solution partners rather than the primary project-discovery channel.

The next implementation node is `HC-001`: use the existing trace, temporal replay, experiment persistence and evaluation primitives to run a historical cohort and report first valid surface date, downstream comparison milestone, lead-time advantage, buyer-path availability, coverage and action burden.

Historical findings in Sections 1-12 remain retained as an audit of the repository at that earlier baseline; this appendix changes product priority rather than rewriting those facts.
