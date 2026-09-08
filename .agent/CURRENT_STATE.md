# Procurement Arena current state

Foundation slice `procurement-arena-foundation-001` passed local validation.
The repository now has research-only typed temporal evidence, scenario
validation, conservative power-gap primitives, and an immutable frozen
decision ledger under `src/athena_procurement_arena`. The versioned scenario
DSL and deterministic temporal world engine are also implemented; the package
now reveals evidence by verified availability and freezes each policy output.

Also implemented: deterministic policy contract, controls, BASELINE_A,
component evaluator, adversarial/counterfactual helpers, Athena governance and
negative knowledge, historical registry boundaries, and run manifests. The
mechanics campaign completed 10,000 seeded runs with zero invariant failures.
The CLI now exposes all declared local mechanics modes and emits JSON output;
`compare --count 1000` and `replay --seed 21` both passed.

Next bounded slice: expand the scenario-family corpus and add tournament
minimum floors/Pareto gates; historical scoring remains blocked until fixture
availability is verified.
Piecewise power profiles now include need and supply boundaries, preserve
unknown supply, calculate gap/duration segments, and feed verified numeric
errors into the evaluator.
All 40 registered scenario families now produce validated seeded templates.
Seeded truth-preserving mutations and same-scope power-overlap protection are
implemented and tested.
Typed customer, utility, contract, research, readiness, and critical-path
contracts are implemented. Scenario DSL serialization round-trips with an
identical hash.

Next bounded slice: execute all 40 families through controls/BASELINE_A,
produce regression metrics, and tighten campaign/tournament reporting.
The 40-family regression and all 10 declared CLI modes now pass integration
checks; the full test suite is 23 passed.
Trailforge is now a local Git repository on `master`; manifests record the
source commit and the worktree is clean.
Current full suite: 30 passed.
Tenant isolation is now enforced on every scenario evidence item; synthetic
scenario factories assign matching tenant IDs and the full suite is 32 passed.

Packet-named architecture, DSL, policy, evaluation, governance, and historical documentation is present; unverified historical replay remains non-scoreable.
Evaluation now includes Precision@K/Recall@K attention metrics for K=5, 10,
25, and 50, with empty/late alerts receiving no early-credit.
Evidence lineage deduplication and conservative identity-resolution outcomes
(`MERGE`, `PROVISIONAL`, `UNRESOLVED`, etc.) are now executable and tested.
The 100,000-run seeded campaign completed with zero invariant failures at
approximately 5,888 runs/second; this remains mechanics evidence only.
CLI adversarial mode now runs the amendment recurrence adversary, and CLI
tournament mode now runs governed promotion gates rather than placeholders.
`verify_replay` now checks an existing manifest's scenario and result hashes
against a fresh replay.
Power profiles expose explicit segment durations, and readiness decisions now
distinguish mandatory failures from unknown blocker-resolution requirements.
