# Completion: arena-invariant-repair-033

Base: `24c7990149190fdb9632c5f3401f0773fc1e9b38`
Branch: `codex/arena-invariant-repair-033`

## Implemented

The decision forecast is detached and recursively frozen for supported mapping, list, tuple, set, and scalar values. Dataclass instances are rejected recursively because a mutable dataclass can retain caller-owned state and invalidate the ledger hash. Nested caller-owned dataclasses now raise `InvariantViolation` during decision construction; valid nested maps/lists/sets remain detached and immutable.

Existing packet behavior remains covered: world I-10 action enforcement, campaign failure propagation and counts, evaluator decision-chain verification, CLI nonzero status, and explicit UNKNOWN when evaluation has no verified basis.

## Review repair

Astra's `CORRECT` finding in preserved `.agent/artifacts/arena-invariant-repair-033/REVIEW-1.json` identified a mutable dataclass nested in a forecast. The audited commit was `dfbb10f203578f93e00155d8f771baa9fc195677`. This repair rejects dataclass forecast values recursively; REVIEW-1 remains unchanged.

## Validation

Focused foundation tests:
`uv run --python 3.11 --with pytest python -m pytest -q tests/procurement_arena/test_foundation.py`
Exit 0; 11 passed.

Required complete local gate:
`uv run --python 3.11 --with pytest --with ruff python scripts/validate.py`
Final artifact-inclusive run exited 0: 133 tests passed, compilation passed, Ruff passed, and GT-003/007/008 bundle validation passed with `holdout_available: false`.

The preceding attempt exited 1 after 133 tests and compilation passed because Ruff found an import-order issue in the new test; the import was corrected before the final run.

## Boundaries and unknowns

Research-only Arena mechanics remain the scope. Real-world forecast accuracy remains UNKNOWN; commercial approval is ABSENT. No policy promotion, network or GitHub validation, commit, push, merge, or deployment was performed. Independent review of the repaired candidate remains pending.
