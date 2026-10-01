# v1-cli-replay-043: make the local scenario/replay entry point real

- Node: V1-S1, READY after the 2026-10-01 audit. One Luna builder; no fan-out.
- Repository/worktree: C:/Users/nrsan/Nucleus/02_Projects/Trailforge
- Branch: codex/trailforge-v1-audit-slice1
- Base: c216b5efbc1daeae5e62f28276f5d35f3d7b04c9 (182 tests and complete local gate PASS).
- Allowed implementation files: src/athena_procurement_arena/cli.py, tests/procurement_arena/test_cli.py, README.md, .gitignore.
- Allowed handoff: .agent/artifacts/v1-cli-replay-043/COMPLETION.json.
- References: runner.py, scenario_dsl.py, world.py; reports/TRAILFORGE_AUDIT_2026-10-01.md.
- Exclusions: policy/evaluator/runner semantics, fixture or seal changes, canonical requirements, external capture, UI, providers, source identity redesign, git commits/push/merge/deploy, other agent state, Slice 2.
- Authority: user explicitly authorized audit and Slice 1 only. Local reversible CLI wiring; existing invariant boundaries remain authoritative.
- Retry budget: two materially different repairs; stop on authority conflict.

## Implementation

1. Add --scenario-file JSON input to scenario mode and --manifest saved-manifest input to replay mode. Scenario requires --scenario-file and --output; replay requires --scenario-file and --manifest. Do not silently synthesize either mode. Keep smoke as the explicit synthetic mechanics entry point.
2. Load ScenarioDsl JSON and use existing run_with_manifest, manifest_dict, load_manifest, verify_replay. Persist the scenario-mode manifest using exclusive creation, creating its parent as needed. Never overwrite an input or existing result, including races. No new persistence architecture.
3. Replay supports BASELINE_A with empty config only; reject other policy IDs/configs rather than silently running another policy. Return verifier checks and nonzero on mismatch. Require saved ledger invariant true, not absent/false. Source-tree/config completeness remains a documented limitation of the existing verifier; do not claim exact build identity beyond checked fields.
4. Catch expected input/JSON/IO/invariant errors for these two modes; emit machine-readable FAIL and nonzero. Preserve unrelated commands. Scenario/smoke status must not claim PASS if manifest ledger validation is false or absent.
5. Refuse new scenario/manifest flags on irrelevant modes; replay output, if unsupported, must not be silently ignored. Preserve prior smoke behavior.
6. Document a runnable scenario-file -> manifest -> separate-process replay quickstart using the scenario nested in an existing source-backed bundle. State unsealed input is mechanics-only, not historical accuracy. Mention intentional removal of seed-only pseudo-replay.
7. Ignore conventional build/ and dist/ output directories. Preserve every tracked file and existing local output.

## Acceptance

- File-input execution persists a loadable manifest and subsequent replay passes using the same input.
- Tampered manifest, changed scenario, missing files/flags, malformed JSON, unsupported policy/config, false/missing ledger result fail nonzero without fake success.
- Existing output bytes survive an attempted overwrite unchanged.
- A subprocess restart test demonstrates persisted files, not in-memory state, drive replay. Tests may use synthetic inputs explicitly as mechanics proof.
- Focused check: uv run --python 3.11 --with pytest --with ruff python -m pytest tests/procurement_arena/test_cli.py -q
- Final controller gate: uv run --python 3.11 --with pytest --with ruff python scripts/validate.py; git diff --check; source-backed input run/replay in distinct processes.
- Builder hands off claims; controller reruns gates and Sol independently reviews the frozen file hashes. Do not grade yourself or run a strategic Astra audit.

## Timing and handoff

Record UTC start/finish, model gpt-6-luna, requested low reasoning, changed paths, commands/exit codes/results, remaining limitations, repair count. Unknown tokens, config identity, and uninstrumented durations are null/UNKNOWN. No invented speedup. Do not spawn other agents. Use apply_patch for edits. Existing large CURRENT_STATE is historical reference; do not rewrite it.
