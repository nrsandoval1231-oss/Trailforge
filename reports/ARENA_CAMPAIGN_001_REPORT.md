# Trailforge Arena Campaign 001

Re-verified against the current tree on 2026-10-20 (Linux cloud container,
Python 3.13.16). Earlier checkpoint figures are kept only where labeled.

## Scope

This campaign validates deterministic mechanics and comparative policy behavior
only. It is not evidence of real-world forecasting accuracy.

## Results

- Full test suite: 474 passed.
- Ruff: passed for `src` and `tests`.
- Scenario-family regression (`tournament`): 40/40 registered families executed
  through `KEYWORD` and `BASELINE_A`; zero invariant failures.
- 10,000-run seeded campaign (seed 12): `PASS`, zero invariant failures for both
  policies, approximately 1,589 runs/second.
- 100,000-run seeded campaign (seed 30): `PASS`, zero invariant failures for both
  policies, approximately 1,647 runs/second.
- CLI: 30 declared modes (up from 10 at the first checkpoint).
- Tournament: candidate is `QUARANTINE` when sealed holdout evidence is absent;
  all other gates pass.
- Adversarial recurrence: amendment-only observations remain `UNKNOWN`.
- Counterfactual extension pair: replay hashes change when the extension fact
  changes.

## Throughput audit

Earlier checkpoints reported approximately 7,651 runs/second (10k) and 6,053
runs/second (100k) on a Windows 11 development machine. Those figures do not
compare directly with this container. On the same container:

| Tree | Runs/second (1k–2k runs, seed 12) |
| --- | --- |
| First checkpoint (`c78a141`) | ~2,630 |
| Before fix (`5eb1838`) | ~359 |
| After fix | ~1,600 |

Bisect identified `8bb4db9`, which wrapped every batch run in `tracemalloc`. That
roughly 5x cost was a measurement artifact, not arena work. Memory tracing is now
opt-in (`--trace-memory`). Throughput figures must come from untraced runs, and
`peak_memory_bytes` is `null` unless tracing is requested. The remaining gap to
the first checkpoint comes from scenario validation and canonical hashing that
later commits added on purpose.

## Invariant results

Temporal cutoff, prediction-as-evidence, tenant isolation, immutable snapshots,
lineage handling, unknown supply, power-scope overlap, and unauthorized-action
checks all have passing tests. The campaign and replay paths make no network
calls. Network acquisition exists only as explicit operator-invoked public
capture and Firecrawl discovery (`capture-public`, `trailforge-discovery`). There
is no autofill, submission, or execution-authority path.

## Failures and limits

No mechanics test failure remains. Subprocess CLI tests require the package to
be installed (`pip install -e .`). The built-in replay registry covers
historical fixtures GT-001 through GT-006. The checked-in source fixtures GT-003,
GT-007, and GT-008 remain non-scoreable until they are independently sealed.
Synthetic family templates are mechanics fixtures, not verified buyer-history
evidence. Power evaluation is unavailable when numeric truth is not supplied.

## Bottlenecks

The campaign is single-process and in-memory. Profiling shows canonical JSON
hashing (`athena_arena.contracts`) and per-run `validate_scenario` dominate
runtime. Caching scenario validation per scenario is the cheapest next speedup.
Verified historical timelines remain the main quality bottleneck.

## Next candidate experiments

1. Add verified, sealed historical timelines with point-in-time availability.
2. Add domain-specific mutations for extensions, rebids, private routes,
   utility delays, and partial supply.
3. Compare a challenger against `BASELINE_A` through the full governed gate
   sequence, including a real sealed holdout.
4. Add prospective shadow-cohort hooks without granting runtime authority.
