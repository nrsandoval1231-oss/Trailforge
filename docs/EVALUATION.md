# Evaluation and reproducibility

`evaluate_replay` reports discovery, trail, procurement, power, action, and
efficiency dimensions independently. Missing verified truth or unknown supply
remains unavailable; it is not converted into a score.

`run_with_manifest` records scenario hash, policy, seed, environment, result
hash, and local source commit. The CLI's `batch`, `compare`, `benchmark`, and
`tournament` modes use seeded synthetic runs. A green synthetic campaign proves
mechanics and comparative robustness only, not real-world forecasting accuracy.
