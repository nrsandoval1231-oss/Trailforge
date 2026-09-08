# Procurement Arena Foundation 001

## Objective

Build the deterministic foundation for Athena Procurement Arena: typed temporal
evidence, scenario validation, power-gap accounting, hard-invariant checks, and
an immutable frozen-decision ledger.

## Allowed files

- `src/athena_procurement_arena/__init__.py`
- `src/athena_procurement_arena/foundation.py`
- `src/athena_procurement_arena/scenario_dsl.py`
- `src/athena_procurement_arena/world.py`
- `src/athena_procurement_arena/policies.py`
- `src/athena_procurement_arena/evaluation.py`
- `src/athena_procurement_arena/robustness.py`
- `src/athena_procurement_arena/campaign.py`
- `src/athena_procurement_arena/runner.py`
- `src/athena_procurement_arena/domain.py`
- tenant and authorization invariant checks in `foundation.py`
- `src/athena_procurement_arena/cli.py`
- `src/athena_procurement_arena/scenarios.py`
- `src/athena_procurement_arena/tournament.py`
- `src/athena_procurement_arena/mutations.py`
- `src/athena_procurement_arena/__main__.py`
- `src/athena_procurement_arena/governance.py`
- `tests/procurement_arena/test_foundation.py`
- `tests/procurement_arena/test_world.py`
- `tests/procurement_arena/test_policies.py`
- `tests/procurement_arena/test_evaluation.py`
- `tests/procurement_arena/test_robustness.py`
- `tests/procurement_arena/test_campaign.py`
- `tests/procurement_arena/test_runner.py`
- `tests/procurement_arena/test_domain.py`
- `tests/procurement_arena/test_cli.py`
- `tests/procurement_arena/test_tournament.py`
- `tests/procurement_arena/test_mutations.py`
- `tests/procurement_arena/test_governance.py`
- `docs/PROCUREMENT_ARENA_FOUNDATION.md`
- `docs/ARCHITECTURE.md`
- `docs/SCENARIO_DSL.md`
- `docs/POLICY_CONTRACT.md`
- `docs/EVALUATION.md`
- `docs/ATHENA_GOVERNANCE.md`
- `.agent/tasks/procurement-arena-foundation-001.md`
- `.agent/artifacts/procurement-arena-foundation-001/COMPLETION.json`
- `.agent/artifacts/procurement-arena-foundation-001/REVIEW.json`
- `.agent/CURRENT_STATE.md`
- `.agent/DECISIONS.md`

## Requirements

- Distinguish event, document, verified availability, and observation times.
- Expose only evidence available at the simulation cutoff.
- Reject future evidence and prediction-as-evidence.
- Preserve unknown dependable supply as unknown; never coerce it to zero.
- Prevent overlapping power scopes from double counting.
- Freeze decisions as hash-chained immutable snapshots.
- Validate a versioned, seeded scenario structure deterministically.
- Load a versioned DSL and replay it through an event-driven world clock.

## Acceptance checks

- `PYTHONPATH=src;gauntlet/src python -m pytest tests/procurement_arena/test_foundation.py -q`
- `python -m compileall -q src/athena_procurement_arena`
- Same scenario and cutoff produce the same visible evidence and hashes.

## Output artifacts

- Foundation module, tests, and concise developer documentation.
- Completion and review JSON artifacts.

## Role budgets

- Builder: Luna-equivalent bounded implementation.
- Reviewer: deterministic local diff/test review.
