# Trailforge architecture

The execution path is `Scenario DSL -> TemporalWorld -> policy callable ->
FrozenDecisionLedger -> Evaluator -> Governance/Tournament`.

The world reveals evidence only at its verified availability time. A policy
receives visible evidence and returns a deterministic forecast/action pair.
`TemporalWorld` accepts any callable with that shape. Only `BaselineA`
implements `PolicyContract`. The keyword, static-score, latest-event,
buyer-frequency, and seeded-random controls are plain callables. The ledger
freezes each result in a hash chain. Evaluator dimensions remain separate;
governance may quarantine or reject a candidate, but never grants execution
authority.

Hashing uses `canonical_hash` in this repository's `athena_arena.contracts`
module. There is no separate market Arena package. Trailforge's procurement
domain remains its own package and data model.
