# Project trace backtest 024

## Objective

Measure deterministic lead time from reviewed early signals to a later,
explicitly observed project milestone across local traces. Report coverage and
unresolved cases without inventing negative outcomes or false alarms.

## Allowed files

- `src/athena_procurement_arena/trace_backtest.py`
- `src/athena_procurement_arena/__init__.py`
- `src/athena_procurement_arena/cli.py`
- `tests/procurement_arena/test_trace_backtest.py`
- `docs/PROJECT_SIGNAL_TRACING.md`
- `README.md`
- `.agent/artifacts/project-trace-backtest-024/COMPLETION.json`
- `.agent/artifacts/project-trace-backtest-024/REVIEW.json`
- `.agent/CURRENT_STATE.md`
- `.agent/DECISIONS.md`

## Exclusions

No outcome inference, false-alarm labeling without sealed negatives, Athena
optimization, crawling, identity resolution, outreach, or promotion.

## Acceptance checks

- Backtest exact reviewed traces against an explicit target signal type.
- Report matched cases, coverage, unresolved traces, and deterministic lead
  seconds for the earliest selected signal.
- Require the early signal to precede the target in observed time.
- Persist a stable, hash-bound JSON report through an explicit CLI mode.
- Tests, Ruff, compilation, fixture validation, and diff checks pass.
