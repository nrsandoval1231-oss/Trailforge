# Trailforge Arena Campaign 001

> **Behind HEAD.** This file is a retained earlier checkpoint. Its test count,
> CLI mode count, throughput figures, and "no network" statement describe that
> checkpoint, not the current tree.

## Scope

This campaign validates deterministic mechanics and comparative policy behavior
only. It is not evidence of real-world forecasting accuracy.

## Results

- Latest full test suite: 66 passed.
- Ruff: passed for Trailforge-owned source and tests.
- Scenario-family regression: 40/40 registered families executed through
  `KEYWORD` and `BASELINE_A`; zero invariant failures.
- 10,000-run seeded campaign: zero invariant failures; approximately 7,651
  runs/second in the earlier checkpoint.
- 100,000-run seeded campaign: zero invariant failures; approximately 6,053
  runs/second on Windows 11 / Python 3.13.15 (seed 30, current checkpoint).
- CLI integration: all 10 declared modes returned machine-readable `PASS`.
- Regression reporting now counts ledger invariant failures per scenario family.
- Tournament: candidate is `QUARANTINE` when sealed holdout evidence is absent.
- Adversarial recurrence: amendment-only observations remain `UNKNOWN`.
- Counterfactual extension pair: replay hashes change when the extension fact
  changes.

## Invariant results

Temporal cutoff, prediction-as-evidence, tenant isolation, immutable snapshots,
lineage handling, unknown supply, power-scope overlap, and unauthorized-action
checks all have passing tests. No network, scraper, autofill, submission, or
execution-authority path is present.

## Failures and limits

No current mechanics test failure remains. The built-in replay registry covers
historical fixtures GT-001 through GT-006; checked-in source-fixture examples
GT-003, GT-007, and GT-008 remain non-scoreable until independently sealed.
Synthetic family templates
are mechanics fixtures, not verified buyer-history evidence. Power evaluation is
unavailable when numeric truth is not supplied.

## Bottlenecks

The current campaign is single-process and in-memory. The evaluator and
baseline are intentionally compact; richer domain-specific mutations and
verified historical timelines are the next quality bottlenecks, not distributed
infrastructure.

## Next candidate experiments

1. Add verified, sealed historical timelines with point-in-time availability.
2. Add domain-specific mutations for extensions, rebids, private routes,
   utility delays, and partial supply.
3. Compare a challenger against `BASELINE_A` through the full governed gate
   sequence, including a real sealed holdout.
4. Add prospective shadow-cohort hooks without granting runtime authority.
