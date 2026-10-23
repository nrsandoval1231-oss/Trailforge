# Pre-RFP implementation graph

Owner brief: pre-RFP discovery lab, received 2026-10-02. Canonical strategy is
already approved; this is implementation, not a new architecture initiative.
Base: `6a9ffa332f6dd0b89a14acfcbaed2a99cc7f06cb` (remote main fetched this turn).
Branch: `codex/trailforge-pre-rfp-lab`. Original dirty operator checkout preserved.

| Node | Dependency | State | Acceptance |
| --- | --- | --- | --- |
| HC-A | approved strategy | IMPLEMENTATION_ACCEPTED | Case import, family integrity, source binding, offline replay, 5â€“10 real seed families, reproducible report |
| HC-A-HISTORY | HC-A | BOUNDED_IMPLEMENTATION_ACCEPTED; EVIDENCE_GAPS | Independently supported historical version availability and precursor timelines |
| HC-B | HC-A | PENDING | Deterministic relevance classification, broad scanner, 20+ cases, matched negatives |
| HC-C | HC-A-HISTORY, HC-B | PENDING | Frozen policy comparison, untouched family holdout, Athena and research-order experiment |
| HC-D | HC-C | PENDING | 30â€“50 deep cases plus prospective name-blind discovery |

HC-A implements existing TemporalWorld, ledger and experiment machinery. A green
HC-A gate cannot satisfy the parent success criterion. Current capture observations
and backtrace hypotheses cannot be credited as historical or prospective discovery.

Ownership: Luna owns implementation/tests/schema/runner and Slice A packet;
controller owns real corpus, this graph, status, verification and PR integration.
One builder; no independent READY implementation node warrants parallel builders.
Sol reviews the frozen integrated candidate before commit/push/PR. No merge.

Independent Sol PASS: source candidate `afd3c7eacd95f02f4fbea0def99eecb1c287d1b6884eaa207c853753a305b7a1`.
See `artifacts/pre-rfp-slice-a/REVIEW-portability.json`. Graph transition records acceptance
only for the frozen source files; this bookkeeping is outside source audit scope.
Next direction CONTINUE. Full product finish contract remains unmet.

Portability delta independently accepted; original review retained. Fresh Windows checkout: 213 retained files byte-identical, eight cases and eight bundles verified.

Current bounded packet: tasks/hc-a-history.md. Direction: reuse PR9 runtime and PR7 exact evidence only, on local codex/trailforge-historical-path. No push/merge authorization. No holdout or discovery credit.

HC-A-HISTORY independent Sol PASS: candidate `a7ba2f5ee6dbc2c3026e6eb3a7917675b776b4d09b4adfed8be3f13bc120bee5`. See `artifacts/hc-a-history/ACCEPTANCE.json`. Direction CONTINUE; no positive lead finding or parent completion. Next bounded work is same-family milestone/buyer-route evidence recovery with timed burden, followed by fresh independent holdout replacements and prospective protocol freeze. No push/merge authorization.
