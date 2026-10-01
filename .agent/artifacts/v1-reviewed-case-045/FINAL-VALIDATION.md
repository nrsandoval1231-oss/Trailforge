# Frozen repaired candidate — controller validation

Base 096c65345eeeba18de051cbdf73d73cab0068f33, branch codex/trailforge-v1-slice3. Two repair dispatches after independent FIX; prior attempts retained. Five candidate file hashes independently checked against repair handoff after builder terminal; unchanged throughout gates. Independent review remains required.

- `uv run --python 3.11 --with pytest --with ruff python scripts/validate.py`: exit 0, **239 tests passed in 29.32s**, compilation, Ruff, all three checked-in bundles PASS and holdout unavailable.
- `powershell -ExecutionPolicy Bypass -File .agent/artifacts/v1-reviewed-case-045/acceptance.ps1`: exit 0. Nine expected outcomes: direct bundle save, fresh-process inspect, original bundle unavailable inspect/replay, execution-disabled inspect, identical decision repeat, unknown ID rejected before creation, tampered input rejected unchanged, existing experiment refused unchanged. Evidence `.firecrawl/slice3a-acceptance-4746276a28874d9c8184ce7dd7cd5622/acceptance.json`. Decisions SHA256 964FD29F9975153B5F2C9D4DC9E7C367100E468CDB47EE3EDF918ACE61300D26.
- `uv build --quiet --out-dir .firecrawl/slice3a-wheel-candidate2`: exit 0.
- From unrelated cwd C:/Users/nrsan, `uv run --no-project --python 3.11 --with C:/Users/nrsan/Nucleus/02_Projects/Trailforge/.firecrawl/slice3a-wheel-candidate2/athena_trailforge-0.1.0-py3-none-any.whl trailforge replay --experiment-dir C:/Users/nrsan/Nucleus/02_Projects/Trailforge/.firecrawl/slice3a-acceptance-4746276a28874d9c8184ce7dd7cd5622/run-1`: exit 0, all five checks true.
- `git diff --check`: exit 0. Protected fixtures/world/policy and existing test module content unchanged. New tests cover explicit null, nested malformed initial and retained bundle, both saved operations, unchanged artifacts, legacy mixed flags and direct selected-scenario binding.

| File | SHA256 |
| --- | --- |
| README.md | c76899066dc189396eb565e4198ee4d61cc959772b7a64a8536aa78164405e22 |
| docs/SLICE3_CASE_READINESS.md | 6a36757634c284f3fe3bb263650d22e6e5112e5627296f33f1d417e7fd00816d |
| src/athena_procurement_arena/cli.py | 46be6c89e2bb368b9fd2ce351a03559ef445283deb09a2e19531bb82e8bc4181 |
| src/athena_procurement_arena/runner.py | 5013e28111c971221dd454f7af173aa5f071c6f1bf7281b512c6596afa1098eb |
| tests/procurement_arena/test_fixture_experiment.py | a94727890db2feaa1b95a839a8a503c2239b183e4bf25d6482c329ecd3ea2ac0 |

Telemetry correction: repair2 session 01a0f830-e2a2-74e2-9e19-e6275c40436a was observed starting 2026-10-01T15:59:08.453311Z, terminal by 16:02:11.679830Z, gpt-6-luna low via --ignore-user-config/explicit CLI model, reported aggregate tokens 66856; split UNKNOWN. Builder handoff's claimed 15:56 start and 5.6 minutes are unsupported, not accepted telemetry. Original handoff retained verbatim. No speedup claim. Runtime header confirms effective model/effort for these workers, not global configuration load. Agent-harness governs bounded repair and independent acceptance.

This is only Slice3A mechanics validation, not real chronological evidence acceptance or sealing. No new Slice3 push/merge/deployment. Prior PR3 release and GitHub CI are separate.
