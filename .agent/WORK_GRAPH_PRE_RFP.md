# Pre-RFP implementation graph

Owner brief: pre-RFP discovery lab, received 2026-10-02. Canonical strategy is
already approved; this is implementation, not a new architecture initiative.
Base: `6a9ffa332f6dd0b89a14acfcbaed2a99cc7f06cb` (remote main fetched this turn).
Branch: `codex/trailforge-pre-rfp-lab`. Original dirty operator checkout preserved.

| Node | Dependency | State | Acceptance |
| --- | --- | --- | --- |
| HC-A | approved strategy | IMPLEMENTATION_ACCEPTED | Case import, family integrity, source binding, offline replay, 5–10 real seed families, reproducible report |
| HC-A-HISTORY | HC-A | READY | Independently supported historical version availability and precursor timelines |
| HC-B | HC-A | PENDING | Deterministic relevance classification, broad scanner, 20+ cases, matched negatives |
| HC-C | HC-A-HISTORY, HC-B | PENDING | Frozen policy comparison, untouched family holdout, Athena and research-order experiment |
| HC-D | HC-C | PENDING | 30–50 deep cases plus prospective name-blind discovery |

HC-A implements existing TemporalWorld, ledger and experiment machinery. A green
HC-A gate cannot satisfy the parent success criterion. Current capture observations
and backtrace hypotheses cannot be credited as historical or prospective discovery.

Ownership: Luna owns implementation/tests/schema/runner and Slice A packet;
controller owns real corpus, this graph, status, verification and PR integration.
One builder; no independent READY implementation node warrants parallel builders.
Sol reviews the frozen integrated candidate before commit/push/PR. No merge.

Independent Sol PASS: source candidate `790cb80ca9fe5657efb4eb8ee43c55c5d5d0825a54dd38788dd68ef247c258d6`.
See `artifacts/pre-rfp-slice-a/REVIEW.json`. Graph transition records acceptance
only for the frozen source files; this bookkeeping is outside source audit scope.
Next direction CONTINUE. Full product finish contract remains unmet.
