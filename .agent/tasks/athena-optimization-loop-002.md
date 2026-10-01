# Athena optimization loop 002

## Objective

Add a deterministic, research-only Athena adapter that evaluates candidate Trailforge policies across the registered scenario families and routes them through the existing governance/tournament gates.

## Allowed files

- `.agent/tasks/athena-optimization-loop-002.md`
- `.agent/artifacts/athena-optimization-loop-002/COMPLETION.json`
- `.agent/artifacts/athena-optimization-loop-002/REVIEW.json`
- `.agent/CURRENT_STATE.md`
- `.agent/DECISIONS.md`
- `src/athena_procurement_arena/athena_optimizer.py`
- `src/athena_procurement_arena/__init__.py`
- `src/athena_procurement_arena/cli.py`
- `tests/procurement_arena/test_athena_optimizer.py`

## Requirements

- Evaluate the incumbent and deterministic candidate policies over all 40 registered scenario families.
- Report separate comparable metrics for discovery, action burden, and cost proxy.
- Create explicit Athena lesson and candidate-policy artifacts without allowing self-promotion.
- Route each candidate through invariant, floor, Pareto, adversarial, counterfactual, and sealed-holdout gates.
- Default to quarantine when holdout evidence is unavailable.
- Preserve research-only scope: no network, vendor contact, procurement submission, or live execution.
- Expose a local `optimize` CLI mode.

## Acceptance checks

- `python -m pytest -q`
- `python -m ruff check src\\athena_procurement_arena tests\\procurement_arena`
- `python -m athena_procurement_arena optimize`
- Candidate results are deterministic for a fixed seed and contain zero invariant failures.
- No candidate is promoted without `holdout_available=True`.

## Output artifacts

- Completion and reviewer JSON artifacts under `.agent/artifacts/athena-optimization-loop-002/`.

## Role budgets

- Builder: bounded implementation and tests.
- Reviewer: inspect diff, artifacts, and validation output.
