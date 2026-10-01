# Retrospective cohort evaluation 029

## Objective

Evaluate a cohort-bound early-signal backtest against an explicit retrospective
outcome cohort while preserving unresolved and inconclusive states.

## Allowed files

- `src/athena_procurement_arena/trace_backtest.py`
- `src/athena_procurement_arena/retrospective_seal.py`
- `src/athena_procurement_arena/retrospective_evaluation.py`
- `src/athena_procurement_arena/__init__.py`
- `src/athena_procurement_arena/cli.py`
- `tests/procurement_arena/test_trace_backtest.py`
- `tests/procurement_arena/test_cohort_backtest.py`
- `tests/procurement_arena/test_retrospective_evaluation.py`
- `docs/PROJECT_SIGNAL_TRACING.md`
- `README.md`
- `.agent/artifacts/retrospective-cohort-evaluation-029/*`
- `.agent/CURRENT_STATE.md`
- `.agent/DECISIONS.md`

## Requirements

- Preserve one case per reviewed trace, including traces without a target.
- Bind every case to its exact trace hash.
- Load and hash-verify both the cohort backtest and retrospective outcome cohort.
- Require matching trace-cohort hashes and target signal types.
- Exclude inconclusive outcomes from precision/recall rather than treating them as negatives.
- Report confusion counts, precision, recall, false-alarm rate, unmatched cases, and a stable evaluation hash.

## Exclusions

No Athena policy update, automatic threshold change, inferred outcome, promotion,
crawling, outreach, or execution authority.

## Acceptance checks

- Focused evaluation tests pass.
- Full repository validation and diff checks pass.
- End-to-end CLI produces a hash-bound evaluation.
- Completion and review artifacts record the remaining evidence limits.
