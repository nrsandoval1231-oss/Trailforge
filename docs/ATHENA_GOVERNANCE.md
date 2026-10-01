# Athena governance

Athena may emit an attribution, candidate lesson, or explicit candidate policy
artifact. `govern_candidate` requires zero hard-invariant failures, robustness
passes, sealed-holdout evidence, minimum floors, and objective improvement
before promotion. Otherwise the result is rejected or quarantined.

`NegativeKnowledge` keeps rejected lessons in memory and supports hash-checked
save/load snapshots and exact-context reuse. Persistence was added in the
later local hardening history and is covered by the existing tests. No Athena
artifact self-promotes and no Trailforge artifact grants commercial or
execution authority.
