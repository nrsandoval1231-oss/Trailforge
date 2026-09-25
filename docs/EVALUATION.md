# Evaluation and reproducibility

`evaluate_replay` reports discovery, trail, procurement, power, action, and
efficiency dimensions independently. Missing verified truth or unknown supply
remains unavailable; it is not converted into a score.

Discovery is policy dependent. A forecast may include a `discovery` object with
an `episode_id` and nonempty `basis_evidence_ids`. A claim is scored only when
all basis IDs were visible to that decision. `discovery.precision` is `null`
when there are no supported explicit claims; a known positive truth still
receives a recall miss. Precision deduplicates by claimed episode identity, so
repeated claims cannot change it. Visibility by itself is not a discovery
claim. `useful_lead_seconds` can be scored only when the cited event has an
optional `action_support` attestation naming the exact procurement episode,
`PREPARE` or `BID_REVIEW`, a reviewer, review time, exact source span, and
specific rationale. The span must belong to that event; the event cannot be
prediction evidence or carry contradiction references. The review must follow
the evidence chronology and already exist at the frozen decision time. Replay
also requires a valid decision hash on the same scenario, an explicit correct
discovery claim that cites the event, actual visibility at decision time, an
action matching the attestation, and a decision before solicitation. Lead is
measured from the earliest qualifying decision. Missing or mismatched
attestations leave lead time `null`. Reviewer attestations are trusted
annotations, not independently verified proof that an action was objectively
sufficient. Synthetic mechanics do not establish real-world accuracy.

`run_with_manifest` records scenario hash, policy, seed, environment, result
hash, and local source commit. The CLI's `batch`, `compare`, `benchmark`, and
`tournament` modes use seeded synthetic runs. A green synthetic campaign proves
mechanics and comparative robustness only, not real-world forecasting accuracy.

`calculate_power_profile` evaluates phased intervals at every need and supply
boundary. Unknown supply produces an unknown segment; verified numeric profiles
can be passed to `evaluate_power_profile` for peak-gap error.

`attention_metrics` reports Precision@K and Recall@K at K=5, 10, 25, and 50;
it treats duplicate/excess alerts as attention burden rather than free recall.
