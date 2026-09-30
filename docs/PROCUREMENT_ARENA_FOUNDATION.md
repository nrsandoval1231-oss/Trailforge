# Procurement Arena foundation

The `athena_procurement_arena` package is the bounded research slice of
Procurement Arena. It has no execution, autofill, or submission authority.
Simulation and replay do not fetch the network. The explicit `capture-public`
command is the exception: it runs the Firecrawl CLI (`firecrawl scrape`) for
one public HTTP(S) URL and stores the returned markdown locally.

`EvidenceEvent` keeps `event_date`, `document_date`, `verified_available_at`,
and `observed_at` separate. Replay uses `visible_at(cutoff)`, which is gated by
verified availability and excludes predictions. `validate_scenario` rejects
prediction-as-evidence and duplicate IDs.

`calculate_power_gap` represents unknown dependable supply as `UNKNOWN`; it does
not silently convert uncertainty to zero supply. `FrozenDecisionLedger` stores
detached, hash-chained snapshots so later evidence cannot rewrite earlier
decisions.

Run the foundation checks with:

```text
PYTHONPATH=src python -m pytest tests/procurement_arena/test_foundation.py -q
```

`ScenarioDsl` accepts the versioned `procurement-arena-scenario-v1` JSON
contract (and YAML when PyYAML is installed). `TemporalWorld` advances only on
declared timeline points, reveals eligible evidence, invokes a deterministic
policy callback, and freezes one decision per point.
