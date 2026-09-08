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
