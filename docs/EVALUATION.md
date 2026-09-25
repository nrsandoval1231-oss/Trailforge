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
claim. `useful_lead_seconds` remains `null` because the current evidence
schema has no typed episode linkage or customer-action sufficiency field.
`PREPARE` or `BID_REVIEW` plus visible IDs cannot establish that the cited
content supports a real customer action; `WATCH` and `RESEARCH` cannot earn
lead-time credit either. A future evidence contract must establish
deterministic linkage and sufficiency before useful lead time can be scored.
These mechanics do not establish real-world accuracy.

`run_with_manifest` records scenario hash, policy, seed, environment, result
hash, and local source commit. The CLI's `batch`, `compare`, `benchmark`, and
`tournament` modes use seeded synthetic runs. A green synthetic campaign proves
mechanics and comparative robustness only, not real-world forecasting accuracy.

`calculate_power_profile` evaluates phased intervals at every need and supply
boundary. Unknown supply produces an unknown segment; verified numeric profiles
can be passed to `evaluate_power_profile` for peak-gap error.

`attention_metrics` reports Precision@K and Recall@K at K=5, 10, 25, and 50;
it treats duplicate/excess alerts as attention burden rather than free recall.
