# Packet: counterfactual-sensitivity-034

Status: READY. Base: `e62df7a73f31fc41329bdeffdc985e32d5940d03` on
`codex/counterfactual-sensitivity-034`. Owner: one Luna builder. This is the
next `CONTINUE` node after accepted packet 033, targeting Build Packet #0 audit
item 10. The Arena remains research-only.

## Objective

Make counterfactual results measure meaningful policy response to the decisive
fact rather than merely a changed replay hash or evidence ID. Preserve failures
as evidence; do not alter `BASELINE_A` or fixtures to force all cases green.

## Current deterministic finding

For `synthetic_scenario(9)` and `BASELINE_A`, replay hashes and full forecast
objects change in all five pairs because evidence IDs and pattern text change.
Comparing procurement state, power status/gap, and action changes only for
contract extension and private procurement. Duplicate procurement, unknown
supply, and cancellation currently leave those material outputs unchanged.

## Allowed files

`src/athena_procurement_arena/robustness.py`,
`src/athena_procurement_arena/athena_optimizer.py` only if gate consumption must
use a new `passed` field, directly affected
`tests/procurement_arena/test_robustness.py` and
`test_athena_optimizer.py`, plus completion artifacts under
`.agent/artifacts/counterfactual-sensitivity-034/`.

## Acceptance

1. A constant `IGNORE` policy with constant forecast fails sensitivity for the
   extension pair and does not report five changed cases merely because replay
   hashes differ. Retain replay hashes as provenance if useful.
2. Compare material forecast/action fields, not evidence IDs, entity count,
   raw pattern text, or truth labels. Define and document case-specific
   expectations: change where a decisive fact should alter the policy answer;
   stability where duplicate or unknown evidence should not inflate certainty.
3. Each case reports observed material change and an honest pass/fail against
   its expectation. Athena robustness gating consumes that pass/fail result and
   cannot treat a changed hash as a passing counterfactual.
4. Tests prove a constant policy fails the required-change case and exercise
   current `BASELINE_A` successes/failures without manufacturing a pass.
   Existing command behavior remains deterministic and machine-readable.

## Validation and authority

Run focused affected tests, then freeze implementation and completion artifact
and run `uv run --python 3.11 --with pytest --with ruff python scripts/validate.py`.
Controller independently reruns the complete local gate and commissions Astra
audit on the exact local commit. No GitHub CI or network validation. Do not
change policy logic, canonical packet, truth fixtures, real-world evidence,
CI, submission/outreach authority, or promotion rules beyond consuming the
honest counterfactual result. Do not commit, push, merge, or deploy. Preserve
others' work. Default repair budget: two materially different attempts.
