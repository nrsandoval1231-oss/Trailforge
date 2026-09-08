# Athena threshold search 003

## Objective

Extend the Athena adapter with deterministic search over a real weighted-score threshold parameter.

## Allowed files

- `.agent/tasks/athena-threshold-search-003.md`
- `.agent/artifacts/athena-threshold-search-003/COMPLETION.json`
- `.agent/artifacts/athena-threshold-search-003/REVIEW.json`
- `.agent/CURRENT_STATE.md`
- `.agent/DECISIONS.md`
- `src/athena_procurement_arena/athena_optimizer.py`
- `tests/procurement_arena/test_athena_optimizer.py`

## Requirements

- Generate weighted-score policy candidates for a bounded threshold range.
- Evaluate each candidate deterministically across the 40-family corpus.
- Preserve Athena artifacts and all six governance gates.
- Never promote without explicit sealed holdout evidence.
- Keep synthetic results labeled as mechanics evidence and preserve research-only scope.

## Acceptance checks

- `python -m pytest -q`
- `python -m ruff check src\\athena_procurement_arena tests\\procurement_arena`
- `python -m athena_procurement_arena optimize`
- Fixed seed and threshold range produce identical results.

## Output artifacts

- Completion and reviewer JSON under `.agent/artifacts/athena-threshold-search-003/`.

## Role budgets

- Builder: bounded implementation and tests.
- Reviewer: inspect diff, artifacts, and validation output.
