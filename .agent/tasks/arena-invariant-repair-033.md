# Packet: arena-invariant-repair-033

Status: READY. Base: `24c7990149190fdb9632c5f3401f0773fc1e9b38` on
`codex/arena-invariant-repair-033`. Owner: one Luna builder. This is the first
`CORRECT` response to the Build Packet #0 audit in
`docs/BUILD_PACKET_0_AUDIT.md`; it does not close that audit.

## Objective

Make frozen decision contents deeply immutable and make hard invariant failures
invalidate the actual world, campaign, evaluator status, and affected CLI result.

## Allowed files

`src/athena_procurement_arena/foundation.py`, `world.py`, `campaign.py`,
`evaluation.py`, `cli.py`; directly affected tests in `tests/procurement_arena/`
(`test_foundation.py`, `test_world.py`, `test_campaign.py`, `test_evaluation.py`,
`test_cli.py`); and a completion artifact under
`.agent/artifacts/arena-invariant-repair-033/`.

## Acceptance

1. A decision forecast is detached from caller-owned nested mappings/lists/sets.
   Nested writes fail, and ledger hashes stay valid after callers mutate their
   original values. Preserve canonical hashing and existing policy read access.
2. `TemporalWorld` rejects an unapproved `ENGAGE` or
   `READY_FOR_AUTHORIZED_SUBMISSION` before recording a decision. The Arena has
   no mechanism to grant commercial approval in this packet.
3. Every campaign mode (`run_campaign`, family, regression, mutation) returns
   `FAIL` when any ledger verification fails, retaining accurate failure counts.
   Affected CLI modes propagate `FAIL` as nonzero process status; an adversarial
   run with a bad ledger cannot report `PASS`.
4. Evaluator output must not report `invariant_status: PASS` without a verified
   decision/ledger basis. Keep UNKNOWN explicit if the caller cannot verify.
5. Behavioral tests cover nested mutation, unauthorized world action, injected
   ledger failures, CLI status, and evaluator status. Preserve the current
   research-only authority and existing public contracts where possible.

## Validation and authority

Run focused affected tests while building. Freeze code and explanatory artifact,
then run the complete local gate via
`uv run --python 3.11 --with pytest --with ruff python scripts/validate.py`.
No GitHub CI, network validation, CI changes, source acquisition, protected
evidence changes, policy promotion, push, merge, or deployment. Record exact
commands/exit codes, changed files, uncertainties, and a completion claim only
for this packet. Independent Astra review follows controller rerun of the
final local gate. Default repair budget: two materially different attempts.
