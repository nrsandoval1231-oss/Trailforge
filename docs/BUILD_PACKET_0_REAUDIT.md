# Build Packet #0 independent re-audit

**Audited candidate:** clean local `main` at
`501efe73f313c3e031887ba10d8490b204eaa926`.
**Controlling packet:** archived Athena Procurement Arena Build Packet #0 v1.0,
SHA-256 `7abb4c4aeb6ab049ea1f2f8888f76bc4f9e96daa3217797b07706bf7858236d8`.
**Independent verdict:** `CORRECT` for full packet acceptance. Nine bounded
mechanisms are `PROVEN`; eleven items remain `PARTIAL`. The earlier
[audit](BUILD_PACKET_0_AUDIT.md) remains a dated record of candidate `b73dd45`.

`PROVEN` here means the named repository mechanism has current local evidence,
not that a policy predicts real outcomes accurately. `PARTIAL` means a required
behavior, campaign proof, or authority-bound input remains unproven. No item is
upgraded by an unexecuted remote check or by a prior slice review alone.

| # | Definition of done | Status | Current repository evidence and limit |
| --- | --- | --- | --- |
| 1 | DSL and schemas | PARTIAL | Versioned JSON round trip and timestamp tests exist; full world/expected-invariant schema validation and a checked-in YAML test are absent. |
| 2 | No-future temporal engine | PROVEN | Availability cutoff, prediction rejection, and deterministic world replay are tested. Authentic historical availability remains unverified. |
| 3 | Lineage and world state | PARTIAL | Deduplication and conservative identity helpers are tested separately; `BASELINE_A` does not use them end to end. |
| 4 | Shared policy contract | PARTIAL | `BASELINE_A` exposes eight methods; the five controls remain standalone tuple callbacks. |
| 5 | Immutable replayable ledger | PROVEN | Nested forecasts detach/freeze or reject unsupported mutable values; chain verification and rewrite tests pass. Full experiment manifests are assessed in item 15. |
| 6 | Separate evaluator dimensions | PARTIAL | Six components are emitted, but discovery and lead-time scoring can credit visible evidence even when the policy ignores it. Some trail/power measures remain unavailable. |
| 7 | Hard invariants invalidate runs | PARTIAL | Packet 033 made ledger and unauthorized-action failures visible. Integrated enforcement for all I-01–I-12, including permissions and unsupported certainty, is not proven. |
| 8 | Coherent seeded mutations | PARTIAL | One thousand deterministic truth-preserving variants are tested; causal coherence across changed route/funding/power claims remains unproven. |
| 9 | Unknown supply and scope | PROVEN | Packet 035 reconciled baseline/profile gaps, time slices, unknown peaks, per-need caps, and I-12 in synthetic tests. Real-world power accuracy is unknown. |
| 10 | Adversarial/counterfactual suites | PARTIAL | Packet 034 removed hash/confidence false positives; `BASELINE_A` still fails cancellation sensitivity and the adversary covers one static amendment world. |
| 11 | Athena candidates, no self-promotion | PARTIAL | Typed candidate artifacts and default quarantine exist; caller-supplied holdout availability reaches tournament before optional fixture scoring. |
| 12 | Deterministic promotion outcomes | PARTIAL | `PROMOTE`/`REJECT`/`QUARANTINE` mechanics exist; low-level promotion can bypass full sealed-holdout, uncertainty, and final-regression proof. |
| 13 | Persistent negative knowledge | PROVEN | Packet 036/036b added hash-checked save/load and exact-context rejected-idea reuse. Authentic rejection authority is not established. |
| 14 | Historical registry/status | PROVEN | GT-001–006 are `UNVERIFIED`; GT-003/007/008 bundles are `VERIFIED` without sealed holdout IDs. |
| 15 | Reproducible manifests | PARTIAL | Scenario/result hashes persist, but manifest loading and replay do not fully bind source/policy version/config; campaigns lack per-run manifests/traces. |
| 16 | Mechanics/regression gates | PROVEN | Exact candidate local gate passed 156 tests, compilation, Ruff, and three bundle validations, all with `holdout_available: false`. Known behavior gaps remain. |
| 17 | Successful 10,000-run campaign | PROVEN | Fresh local seed-30 run completed 10,000 scenarios/20,000 policy runs with zero counted invariant failures. Both policies had zero actionable decisions. |
| 18 | Credible 100,000-run path | PROVEN | Bounded single-process runner and retained Campaign 001 benchmark show a credible path; historical throughput is not this SHA's measurement. |
| 19 | Scenario/policy/replay docs | PROVEN | README and packet-named docs locate the interfaces. Historical report numbers and old claims must remain dated. |
| 20 | Arena scope boundary | PARTIAL | Research-only authority remains; explicit reviewer-bound public capture exists. Full packet gaps still prevent finish acceptance. |

## Exact local evidence

- `uv run --python 3.11 --with pytest --with ruff python scripts/validate.py`:
  exit 0; 156 tests, compilation, Ruff, and GT-003/007/008 bundle checks passed;
  each bundle reported `holdout_available: false`.
- `uv run --python 3.11 python -m athena_procurement_arena batch --count 10000 --seed 30`:
  exit 0; 10,000 scenarios, 20,000 policy runs, zero counted invariant
  failures, and zero actionable decisions for both `KEYWORD` and `BASELINE_A`.
- Packets 033–036/036b each received an independent `ACCEPT` for their bounded
  slices. Their review artifacts bind the code SHA and retain rejected repairs.
  Those verdicts do not replace this full acceptance result.

## First campaign and external evidence

The required all-controls comparison, full candidate-bound metric vector and
traces, executed weak-challenger rejection, wider adversarial attacks, and a
passing cancellation counterfactual remain open. The retained
[Campaign 001 report](../reports/ARENA_CAMPAIGN_001_REPORT.md) records older
throughput and `66 passed`; its absolute no-network and hash-based
counterfactual prose is historical, not the current implementation.

Only local validation was used for this re-audit. A previously inspected
GitHub run at older SHA `b73dd45` did not start job steps and cited account
payment or spending-limit trouble. No remote check is claimed for this SHA.
No sealed real-world outcomes or governed challenger-versus-`BASELINE_A`
holdout comparison exist here; real-world accuracy and a resulting policy
promotion decision remain **UNKNOWN**. The Arena has no commercial execution
authority.

## Controller direction: CORRECT

Next bounded packet: make discovery and actionable useful-lead-time evaluation
depend on policy output, so a constant `IGNORE` policy and vague early guesses
receive no discovery or lead-time credit. Preserve explicit `UNKNOWN` without
a prediction basis. Then run the complete local gate and independent audit on
the exact repaired candidate before repeating campaign comparisons.
