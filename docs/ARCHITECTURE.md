# Trailforge architecture

The execution path is `Scenario DSL -> TemporalWorld -> PolicyContract ->
FrozenDecisionLedger -> Evaluator -> Governance/Tournament`.

The world reveals evidence only at its verified availability time. Policies
receive visible evidence and return deterministic forecast/action data. The
ledger freezes each result in a hash chain. Evaluator dimensions remain
separate; governance may quarantine or reject a candidate, but never grants
execution authority.

The existing Athena market Arena hashing primitive is reused; Trailforge's
procurement domain remains a separate package and data model.
