# Prime power threshold 010

## Objective

Restrict Trailforge target qualification to prime/temporary operating power opportunities of at least 300 kW and exclude emergency-backup-only work.

## Allowed files

- `.agent/tasks/prime-power-threshold-010.md`
- `.agent/artifacts/prime-power-threshold-010/COMPLETION.json`
- `.agent/artifacts/prime-power-threshold-010/REVIEW.json`
- `.agent/CURRENT_STATE.md`
- `.agent/DECISIONS.md`
- `src/athena_procurement_arena/policies.py`
- `src/athena_procurement_arena/scenarios.py`
- `src/athena_procurement_arena/athena_optimizer.py`
- `tests/procurement_arena/test_policies.py`
- `tests/procurement_arena/test_athena_optimizer.py`
- `tests/procurement_arena/test_robustness.py`

## Requirements

- Add explicit target qualification states for prime power, minimum 300 kW, emergency backup, below threshold, and unknown requirements.
- Make built-in policies produce no actionable output unless the target is qualified.
- Preserve maintenance-only exclusion and allow incidental maintenance within a qualified prime-power/install contract.
- Keep the threshold and scope configurable in one deterministic classifier.

## Acceptance checks

- `python -m pytest -q`
- `python -m ruff check src\\athena_procurement_arena tests\\procurement_arena`
- A 300 kW prime temporary-power case is eligible.
- A 299 kW case, an 80 kW case, and emergency-backup-only case are ignored.
- Existing 40-family corpus still validates.

## Output artifacts

- Completion and reviewer JSON under `.agent/artifacts/prime-power-threshold-010/`.

## Role budgets

- Builder: bounded policy/classifier change.
- Reviewer: inspect diff, artifact, and validation output.
