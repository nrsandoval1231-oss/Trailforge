# Trailforge architecture

The smallest working path is `Scenario DSL -> TemporalWorld -> PolicyContract ->
FrozenDecisionLedger -> Evaluator`. Add tournament comparison only when a concrete
experiment needs to compare candidate policies.

The world reveals evidence only at its verified availability time. Policies
receive visible evidence and return deterministic forecast/action data. The
ledger freezes each result in a hash chain. Evaluator dimensions remain
separate. Any candidate review or quarantine is part of a defined research
comparison; it never grants execution authority.

The existing Athena market Arena hashing primitive is reused; Trailforge's
procurement domain remains a separate package and data model.
