# Build Packet #0 acceptance audit

**Audited candidate:** `b73dd45330b4628f1ba3c2680e99176db10a3400`
(`main`, clean; GitHub `main` matched after push on 2026-09-24).
**Controlling packet:** archived Athena Procurement Arena Build Packet #0 v1.0,
SHA-256 `7abb4c4aeb6ab049ea1f2f8888f76bc4f9e96daa3217797b07706bf7858236d8`.
**Independent strategic verdict:** `CORRECT`. This is an audit of packet
acceptance, not authorization to promote a policy or execute commercial work.

`PROVEN` below means the bounded packet mechanism has current repository and
test evidence. `PARTIAL` means evidence exists but a required behavior or proof
is missing. `UNPROVEN` means the required behavior has no durable proof. Remote
CI and real-world outcome evidence are assessed separately.

| # | Packet definition of done | Status | Evidence and acceptance limit |
| --- | --- | --- | --- |
| 1 | DSL and schemas | PARTIAL | `scenario_dsl.py`, `schemas/procurement-arena-scenario-v1.schema.json`, `test_world.py` cover versioned parsing/round trip. The compact `Scenario` does not establish the packet's full world and expected-invariants DSL; YAML requires optional PyYAML and has no checked-in YAML test. |
| 2 | Temporal no-future-evidence engine | PROVEN | `EvidenceEvent.visible_at`, `validate_scenario`, `TemporalWorld.step`, foundation/world tests gate on verified availability and reject prediction-as-evidence. Supplied historical availability itself still needs independent verification. |
| 3 | Evidence lineage and world state | PARTIAL | `deduplicate_evidence`, `resolve_identity`, and temporal replay exist, but `BaselineA.resolveEntities` copies lineage rather than invoking those conservative helpers end to end. |
| 4 | Shared controls and `BASELINE_A` contract | PARTIAL | `policies.py` has five callable controls and `BaselineA`; controls return the runner tuple but do not implement the eight-method `PolicyContract`. |
| 5 | Immutable, replayable frozen ledger | PARTIAL | Ledger hashes and replay tests exist. `FrozenDecision.forecast` is only shallowly frozen: a nested forecast can be changed after append, making `ledger.verify()` false. |
| 6 | Separate evaluator dimensions | PARTIAL | `evaluation.py` reports six components and keeps unavailable power explicit. Discovery is based on visible evidence IDs rather than policy discoveries; some requested trail/power measures remain unavailable, and lead-time credit is not bound to the actionable helper. |
| 7 | Invariants invalidate bad runs | PARTIAL | Structural checks exist, but `TemporalWorld` does not call `validate_recommended_action`. Campaign functions count ledger failures yet still return `status: PASS`; a bad run is therefore not consistently invalidated. |
| 8 | Coherent seeded mutations | PARTIAL | `mutations.py` and 1,000-variant test prove deterministic truth-preserving variants. Causal coherence across the packet's wider domain dimensions is not demonstrated. |
| 9 | Unknown supply and scope accounting | PARTIAL | Foundation tests cover UNKNOWN supply, phased segments, and `I-12` overlap. A known `PowerNeed.dependable_supply_mw` of 4 with load 10 gives a 6 MW primitive gap but a 10 MW profile gap with no external supply; profile accounting is inconsistent. |
| 10 | Adversarial and counterfactual suites | PARTIAL | One amendment adversary and five named pairs exist. Every pair reports `changed: true` for a constant `IGNORE` policy because the replay hash includes added evidence; appropriate policy behavior change is not proven. |
| 11 | Athena candidates without self-promotion | PARTIAL | Candidate/input/lesson artifacts and default holdout quarantine exist. `holdout_available` is caller-supplied rather than bound to verified holdout results at the tournament boundary. |
| 12 | Deterministic promotion outcomes | PARTIAL | Tournament tests show `PROMOTE`/`REJECT`/`QUARANTINE` mechanics. The full packet gate, including authenticated sealed holdout, uncertainty, and final regression, is not demonstrated; the lower-level `tournament_decision` can return `PROMOTE` without a holdout. |
| 13 | Persistent negative knowledge | UNPROVEN | `NegativeKnowledge` stores rejected lessons in one in-memory dictionary. Its test checks same-instance retention; no save/load or future-run reuse exists. |
| 14 | Historical registry and statuses | PROVEN | `runner.py` lists GT-001–GT-006 as `UNVERIFIED`; checked-in GT-003/007/008 bundles are `VERIFIED` with no holdout IDs. This proves registry handling, not a sealed historical cohort. |
| 15 | Reproducible manifests | PARTIAL | `runner.py` can write/load and verify scenario/result hashes. Replay depends on a separately supplied policy/scenario; campaign runs do not retain per-run manifests, and policy-version/config identity is not fully checked. |
| 16 | Mechanics and regression gates | PARTIAL | Exact-SHA local gate passed 124 tests, source compilation, Ruff, and three bundle validations. The suite misses the concrete invalidation, mutation, and counterfactual failures above. GitHub CI did not start steps. |
| 17 | Successful 10,000-run campaign | PARTIAL | Fresh `batch --count 10000 --seed 30` exited 0 with zero counted ledger failures for each of `KEYWORD` and `BASELINE_A`. Both reported `actionable: 0`, so this proves execution scale and hash checks, not useful policy behavior. |
| 18 | Credible 100,000-run path | PROVEN | Bounded in-memory campaign runner and retained Campaign 001 report record a prior 100,000-run benchmark. Its historical throughput is not a measurement of this SHA. |
| 19 | Scenario/policy/replay documentation | PROVEN | Scenario, policy, evaluation, architecture docs and README describe entrypoints and reproduction. Some claims need correction as the incomplete mechanics are repaired. |
| 20 | No Arena-displacing scope creep | PARTIAL | No bid autofill, submission, broker, or execution authority is established; prospective artifacts retain `ABSENT`. Explicit reviewer-bound public capture exists, so the older campaign report's absolute “No network ... path” statement is stale. The Arena remains research-only, but core packet gaps remain. |

## Deterministic evidence on the audited SHA

- `uv run --python 3.11 --with pytest --with ruff python scripts/validate.py`:
  exit 0; 124 tests passed, compilation and Ruff passed, and GT-003/007/008
  validation returned `holdout_available: false`.
- `uv run --python 3.11 python -m athena_procurement_arena batch --count 10000 --seed 30`:
  exit 0; 10,000 scenarios and 20,000 policy runs, zero counted ledger failures,
  zero actionable decisions for each policy. This is synthetic mechanics proof.
- Read-only probes confirmed nested ledger forecast mutation, five false-positive
  counterfactual change flags for a constant policy, and the 6 MW versus 10 MW
  power-profile discrepancy described in rows 5, 10, and 9.
- GitHub [run 36067565548](https://github.com/nrsandoval1231-oss/Trailforge/actions/runs/36067565548)
  targeted this SHA but had zero job steps. Its check annotation cites failed
  account payments or a spending limit. Remote validation is **blocked**, not
  a failed executed test or a pass. Keep the CI gate unchanged.

## First execution campaign and real-world boundary

The local suite covers 40 scenario families and 1,000 seeded variants. The
retained Campaign 001 report records earlier 10,000/100,000-run benchmarks.
The required all-controls comparison, full component vector and traces,
meaningful weak-policy rejection, policy-sensitive counterfactuals, and
candidate-bound campaign artifacts are not all established. No checked-in
fixture is `SEALED_READY`; there is no governed real-world challenger-versus-
`BASELINE_A` sealed holdout comparison, uncertainty assessment, or resulting
promotion record. Forecast accuracy and completion remain **UNKNOWN**.

## Controller direction: CORRECT

Next bounded repair packet: make a nested frozen decision immutable and make
every invariant failure invalidate the world/campaign result, with tests that
inject bad ledger and unauthorized action paths. Then rerun the complete local
gate and independent audit on the repaired exact candidate. Follow-on packets
should address policy-sensitive counterfactuals, power-profile accounting, and
durable negative knowledge before another full Build Packet #0 acceptance
attempt. No packet authorizes live outreach, submission, or policy promotion.
