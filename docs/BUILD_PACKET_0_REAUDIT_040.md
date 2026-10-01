# Build Packet #0 independent re-audit — packet 040

**Exact audited candidate:** clean local `main` at `32a536fca60fc4ea32a2a3d6c480d9e480a1971b`.
**Controlling packet:** archived Build Packet #0 v1.0 named in [PRD alignment](PRD_ALIGNMENT.md), independently hash-checked as `7abb4c4aeb6ab049ea1f2f8888f76bc4f9e96daa3217797b07706bf7858236d8`.
**Independent raw verdict:** `CORRECT` for full packet acceptance. Nine bounded mechanisms are `PROVEN`; eleven requirements remain `PARTIAL`. `PROVEN` means local mechanism proof, not real-world accuracy.

| # | Definition of done | Status | Current proof and acceptance gap |
| --- | --- | --- | --- |
| 1 | DSL and schemas | PARTIAL | JSON/provenance/action-attestation round trips pass. Loading does not enforce the JSON schema; full world/invariant structure and checked-in YAML acceptance remain absent. |
| 2 | No-future temporal engine | PROVEN | Availability cutoff, prediction rejection, frozen world replay and review-time hiding are tested. Historical source dates remain unverified. |
| 3 | Lineage and world state | PARTIAL | Deduplication and conservative identity helpers are tested, but `BASELINE_A` does not use them end to end. |
| 4 | Shared policy contract | PARTIAL | `BASELINE_A` implements eight contract methods; five controls remain standalone callbacks. |
| 5 | Immutable replayable ledger | PROVEN | Nested freeze/detachment, unsupported-value rejection, chain verification and rewrite tests pass. Manifest breadth is assessed in item 15. |
| 6 | Separate evaluator metrics | PARTIAL | Six dimensions exist. Packets 038–039 prevent visibility-only discovery and unsupported useful-lead credit, but discovery basis is not semantically linked to an episode and trail, calibration, cost and numeric error coverage is incomplete. Built-in policies emit no discovery claim. |
| 7 | Hard invariants invalidate runs | PARTIAL | Selected temporal/action/ledger failures invalidate. I-03/04/06/08/11 lack complete integrated enforcement; campaign counts mainly check the ledger chain. |
| 8 | Coherent seeded mutations | PARTIAL | A deterministic 1,000-variant test preserves truth, but route/funding/power changes lack causal reconciliation with that truth. |
| 9 | Unknown supply and scope | PROVEN | Phased profile, unknown supply, shared-supply cap and overlap rejection have synthetic tests. |
| 10 | Adversarial/counterfactual suites | PARTIAL | Robustness checks reject hash/confidence-only false positives. Cancellation sensitivity still fails and the adversary has one static amendment world. |
| 11 | Athena candidates without self-promotion | PARTIAL | Typed artifacts and default quarantine exist; caller-supplied holdout availability can reach tournament without a verified fixture score. |
| 12 | Deterministic promotion outcomes | PARTIAL | `PROMOTE`/`REJECT`/`QUARANTINE` branches exist; low-level gates trust booleans and lack complete sealed-holdout, uncertainty, final regression and approval proof. |
| 13 | Persistent negative knowledge | PROVEN | Hash-checked save/load and exact-context rejected-idea reuse are tested. Authentic external rejection authority is separate. |
| 14 | Historical registry/status | PROVEN | GT-001–006 are `UNVERIFIED`; GT-003/007/008 bundles are `VERIFIED` but unsealed. |
| 15 | Reproducible manifests | PARTIAL | Scenario/result replay is tested, but source/config/policy version binding and campaign per-run traces remain incomplete. |
| 16 | Mechanics/regression gates | PROVEN | Exact-candidate local gate: 163 tests, compilation, Ruff and three bundle checks passed; each bundle reported `holdout_available: false`. |
| 17 | 10,000-run campaign | PROVEN | Exact-candidate seed-30 batch: 10,000 scenarios, 20,000 policy runs, zero counted failures; both policies made zero actionable decisions. |
| 18 | Credible 100,000-run path | PROVEN | Bounded runner and retained historical 100,000-run benchmark support a credible path; prior throughput is not a measurement of this candidate. |
| 19 | Developer documentation | PROVEN | README and scenario, policy, evaluation and architecture docs explain extension and replay. Historical report counts remain dated. |
| 20 | Arena scope boundary | PARTIAL | Research-only authority remains. Adjacent intake/trace work exists while the core packet still has gaps; completion is not certified. |

## First campaign and invariant limits

Build Packet §26 A, B and I have bounded local proof. C–H and J remain partial: mutations lack causal coherence; the campaign compares only `KEYWORD` and `BASELINE_A`; full candidate-bound metric vectors and per-run traces are absent; weak-challenger rejection is not retained as a complete campaign; the adversary is narrow; four of five counterfactual pairs pass and cancellation fails. The Campaign 001 report is a historical checkpoint, including its `66 passed`.

I-01, I-02, I-05, I-07, I-09, I-10 and I-12 have bounded mechanics proof. I-03, I-04, I-06, I-08 and I-11 remain partial. In particular, `permission_scope` is retained on evidence but not authorized before policy exposure. Zero counted campaign failures cannot establish complete I-01–I-12 coverage.

## Exact local evidence and direction

- `uv run --python 3.11 --with pytest --with ruff python scripts/validate.py`: exit 0, 163 tests, compilation, Ruff, three bundle checks; `holdout_available: false` in each bundle.
- `uv run --python 3.11 python -m athena_procurement_arena batch --count 10000 --seed 30`: exit 0, 10,000 scenarios/20,000 policy runs, zero counted invariant failures, zero actionable decisions for both policies.
- Only local validation was used. The older GitHub CI billing blocker remains external; no remote status is asserted for this candidate.

Next bounded direction: fail-closed permission enforcement in temporal replay (I-08), with `PUBLIC` as the only currently explicit authorized scope. Reject unknown/non-public scope before policy invocation and ledger append; preserve the research-only boundary. Then run the full local gate and independent audit. Real sealed outcomes, governed holdout comparison, predictive accuracy and a resulting promotion decision remain `UNKNOWN`.
