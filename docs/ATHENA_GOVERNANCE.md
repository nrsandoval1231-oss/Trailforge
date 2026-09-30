# Athena governance

Athena may emit an attribution, candidate lesson, or explicit candidate policy
artifact. `govern_candidate` requires zero hard-invariant failures, robustness
passes, sealed-holdout evidence, minimum floors, and objective improvement
before promotion. Otherwise the result is rejected or quarantined.

`NegativeKnowledge` keeps rejected lessons in an in-memory dictionary on one
instance so failed ideas are not silently rediscovered during that process.
It has no save or load path and does not persist across runs. No Athena
artifact self-promotes and no Trailforge artifact grants commercial or
execution authority.
