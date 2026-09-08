# Temporary power scope 007

## Objective

Align Trailforge with the commercial scope: temporary power, generator installation/replacement, and related procurement are in scope; maintenance-only opportunities are excluded.

## Allowed files

- `.agent/tasks/temporary-power-scope-007.md`
- `.agent/artifacts/temporary-power-scope-007/COMPLETION.json`
- `.agent/artifacts/temporary-power-scope-007/REVIEW.json`
- `.agent/CURRENT_STATE.md`
- `.agent/DECISIONS.md`
- `src/athena_procurement_arena/policies.py`
- `tests/procurement_arena/test_policies.py`

## Requirements

- Add a deterministic scope classifier for maintenance-only, installation/replacement/temporary-power, and unknown evidence.
- Make every built-in policy ignore maintenance-only opportunities.
- Allow maintenance terms when installation, replacement, rental, or temporary-power scope is also present.
- Preserve research-only and human-approval boundaries.

## Acceptance checks

- `python -m pytest -q`
- `python -m ruff check src\\athena_procurement_arena tests\\procurement_arena`
- Maintenance-only evidence produces `IGNORE` across built-in policies.
- Installation-plus-maintenance evidence remains eligible.

## Output artifacts

- Completion and reviewer JSON under `.agent/artifacts/temporary-power-scope-007/`.

## Role budgets

- Builder: bounded policy and test change.
- Reviewer: inspect diff, artifact, and validation output.
