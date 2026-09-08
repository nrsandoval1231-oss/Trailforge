# Verified outcome scoring 005

## Objective

Add a fail-closed evaluator for source-backed fixture outcomes so Athena can measure prediction correctness on a sealed holdout.

## Allowed files

- `.agent/tasks/verified-outcome-scoring-005.md`
- `.agent/artifacts/verified-outcome-scoring-005/COMPLETION.json`
- `.agent/artifacts/verified-outcome-scoring-005/REVIEW.json`
- `.agent/CURRENT_STATE.md`
- `.agent/DECISIONS.md`
- `src/athena_procurement_arena/fixtures.py`
- `src/athena_procurement_arena/athena_optimizer.py`
- `src/athena_procurement_arena/__init__.py`
- `tests/procurement_arena/test_fixtures.py`
- `tests/procurement_arena/test_athena_optimizer.py`

## Requirements

- Score exact final procurement-state predictions against fixture truth outcomes.
- Require `SEALED_READY` fixtures for holdout scoring.
- Report accuracy, correct count, fixture count, and invariant failures separately.
- Preserve the existing synthetic evaluator and six governance gates.
- Do not claim real-world accuracy until actual source-backed fixtures are supplied.

## Acceptance checks

- `python -m pytest -q`
- `python -m ruff check src\\athena_procurement_arena tests\\procurement_arena`
- A matching sealed fixture scores correctly.
- Unsealed or unavailable holdout input fails closed.

## Output artifacts

- Completion and reviewer JSON under `.agent/artifacts/verified-outcome-scoring-005/`.

## Role budgets

- Builder: bounded implementation and tests.
- Reviewer: inspect diff, artifacts, and validation output.
