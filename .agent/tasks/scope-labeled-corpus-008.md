# Scope-labeled corpus 008

## Objective

Label the synthetic scenario-family corpus with commercial scope so maintenance-only cases cannot be mistaken for temporary-power or installation opportunities.

## Allowed files

- `.agent/tasks/scope-labeled-corpus-008.md`
- `.agent/artifacts/scope-labeled-corpus-008/COMPLETION.json`
- `.agent/artifacts/scope-labeled-corpus-008/REVIEW.json`
- `.agent/CURRENT_STATE.md`
- `.agent/DECISIONS.md`
- `src/athena_procurement_arena/scenarios.py`
- `src/athena_procurement_arena/__init__.py`
- `tests/procurement_arena/test_policies.py`
- `tests/procurement_arena/test_campaign.py`

## Requirements

- Add explicit family scope labels for maintenance-only, in-scope, and unknown families.
- Ensure family scenarios carry scope evidence through the normal temporal DSL.
- Preserve maintenance exclusion and installation/temporary-power eligibility.
- Do not infer real-world accuracy from synthetic scope labels.

## Acceptance checks

- `python -m pytest -q`
- `python -m ruff check src\\athena_procurement_arena tests\\procurement_arena`
- Maintenance-only family is excluded by built-in policies.
- Temporary-power/installation family remains eligible.
- All 40 family templates still validate.

## Output artifacts

- Completion and reviewer JSON under `.agent/artifacts/scope-labeled-corpus-008/`.

## Role budgets

- Builder: bounded corpus labeling and tests.
- Reviewer: inspect diff, artifacts, and validation output.
