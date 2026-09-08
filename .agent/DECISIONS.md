# Decisions

## 2026-09-08 — Procurement Arena foundation

- Keep Procurement Arena in its own package because the existing
  `athena_arena` package is a separate market-replay Arena.
- Reuse only the existing canonical hashing primitive; do not create a second
  product database or execution interface.
- Treat unknown dependable supply as an explicit unknown result rather than a
  zero-supply estimate.
- Use a small mapping-based DSL loader with JSON required and YAML optional;
  keep scenario persistence separate from the existing market Arena storage.
- Make the world engine callback-based until the policy contract is defined;
  every timeline point still receives a frozen ledger record.
- Synthetic throughput is recorded as a mechanics result only; it is not
  evidence of production forecasting quality.
## Athena optimization loop 002

- Use a deterministic local adapter as Athena's first optimizer integration.
- Evaluate candidates on the full 40-family corpus and report discovery, action
  burden, and cost-proxy metrics separately.
- Preserve the existing six-gate tournament and default to quarantine/rejection
  until verified sealed holdout evidence exists.
- Keep Athena advisory and research-only; it cannot self-promote or perform live
  procurement actions.

## Athena threshold search 003

- Make optimization concrete with a small bounded weighted-score threshold
  search rather than comparing only fixed policy implementations.
- Keep threshold results subordinate to the existing governance gates; a lower
  alert count alone is not an accuracy improvement.
- Continue treating the synthetic family corpus as mechanics evidence, not as a
 substitute for verified historical holdout evidence.

## Verified fixture boundary 004

- Require provenance and a content fingerprint before accepting a source-backed
  fixture into a local bundle.
- Treat train/holdout allocation as separate from evidence verification.
- Require explicit `SEALED_READY` status for holdout scoring; parsing alone never
  makes a fixture scoreable.
