# Candidate 1 controller validation — review pending

Base 096c65345eeeba18de051cbdf73d73cab0068f33; branch codex/trailforge-v1-slice3. Frozen five implementation/docs/test hashes are in the independent review and were independently read after builder release.

- Full `uv run --python 3.11 --with pytest --with ruff python scripts/validate.py`: exit 0; 229 tests in 35.01s, compilation, Ruff, three fixture checks PASS.
- `powershell -ExecutionPolicy Bypass -File .agent/artifacts/v1-reviewed-case-045/acceptance.ps1`: exit 0; nine expected outcomes including negative rejection checks. Evidence `.firecrawl/slice3a-acceptance-111150e443654d54ac29173f36fb36ed/acceptance.json`.
- Public direct-bundle save, fresh-process inspect, original bundle moved/unavailable, replay, execution-disabled public inspect, deterministic repeat, unknown fixture rejected before target creation, protected input tamper rejected without mutation, existing directory refused.
- Decisions SHA256 964FD29F9975153B5F2C9D4DC9E7C367100E468CDB47EE3EDF918ACE61300D26.
- `uv build --quiet --out-dir .firecrawl/slice3a-wheel-candidate1`: exit 0.
- From unrelated cwd C:/Users/nrsan, `uv run --no-project --python 3.11 --with C:/Users/nrsan/Nucleus/02_Projects/Trailforge/.firecrawl/slice3a-wheel-candidate1/athena_trailforge-0.1.0-py3-none-any.whl trailforge replay --experiment-dir C:/Users/nrsan/Nucleus/02_Projects/Trailforge/.firecrawl/slice3a-acceptance-111150e443654d54ac29173f36fb36ed/run-1`: exit 0, all five checks true.
- `git diff --check`: exit 0. Protected fixture/world/policy/evaluator Git diff empty.

Builder session 01a0f81a-6861-7350-8baa-bc5819f56118, explicit gpt-6-luna low, observed startup UTC 2026-10-01T15:34:35.366161Z and terminal completion 15:46:44.083018Z; reported aggregate tokens 137285, split UNKNOWN. Builder completion's 15:41:07Z start is not the full dispatch start; controller observed timestamp governs telemetry. Original completion preserved. Candidate source frozen before controller gate; hashes unchanged through handoff. New test module used; prior test module has no Git content diff, only working-copy line-ending normalization.

Prior main release/CI acceptance is separate. No Slice 3 push/merge or real evidence approval. Green gates do not replace independent review.
