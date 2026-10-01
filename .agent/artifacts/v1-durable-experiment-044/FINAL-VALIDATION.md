# Frozen candidate controller validation

Base 15247421e00303e36436961a91096efa55194ade. Source/docs/tests frozen and independently hashed after specialist release. Scope is Slice 2, not full V1. Prior failed candidates/reviews remain retained.

## Exact implementation SHA-256

| File | SHA-256 |
| --- | --- |
| README.md | D7E3C95A2D2223B234797551016C104D37D71FDAB6A3296583C02351E4F6E9DA |
| src/athena_procurement_arena/cli.py | A07D0BAB9A9D4B20ECD2715870EBDE579B1271FA6E55384E039A813E276B4914 |
| src/athena_procurement_arena/runner.py | BC1D179376610888D4DF4D860CF40E5C5A6A6F84FA861C39A43A9AEB19C457C7 |
| src/athena_procurement_arena/world.py | 415349B228998C6A46D2A75332A3D35438B7125676A81102AC85BF1193C35036 |
| tests/procurement_arena/test_cli.py | 4BD1A61961C5C19EB8ACA4224959611CB59CCD33B0804CD0ADF87C3EF970D2EF |
| tests/procurement_arena/test_experiment.py | D25FD671C10CE928278EA604B41D3C1D03B33F12E171D523BC6EA7EFFF345223 |

## Controller commands and outcomes

- `uv run --python 3.11 --with pytest --with ruff python scripts/validate.py`: exit 0, **217 passed in 33.59s**, compilation, Ruff, GT-003/GT-007/GT-008 validations PASS. This independently resolves the specialist's UNKNOWN final-gate terminal status; no inference from its earlier passing candidate.
- `uv run --python 3.11 python .agent/artifacts/v1-durable-experiment-044/ordering_probe.py`: exit 0. Valid unsorted evidence z,a stays in its actual captured order while ledger IDs are a,z.
- `powershell -ExecutionPolicy Bypass -File .agent/artifacts/v1-durable-experiment-044/acceptance.ps1`: exit 0. Nine separate-process command outcomes match expectations, including three deliberate FAIL outcomes (tampered inspect/replay and existing-directory save).
- `uv run --python 3.11 python .agent/artifacts/v1-durable-experiment-044/no_execution_inspect_probe.py .firecrawl/slice2-acceptance-ab93bee1b9034fe9bfdea5276fab9a6c/run-1`: exit 0; actual CLI inspection succeeds in another process with world construction and policy execution patched to raise. Evaluation stays UNSEALED.
- `uv build --quiet --out-dir .firecrawl/slice2-wheel-final`: exit 0.
- From unrelated cwd `C:/Users/nrsan`, `uv run --no-project --python 3.11 --with C:/Users/nrsan/Nucleus/02_Projects/Trailforge/.firecrawl/slice2-wheel-final/athena_trailforge-0.1.0-py3-none-any.whl trailforge replay --experiment-dir C:/Users/nrsan/Nucleus/02_Projects/Trailforge/.firecrawl/slice2-acceptance-ab93bee1b9034fe9bfdea5276fab9a6c/run-1`: exit 0; input_binding, ledger, result_hash, scenario_hash, source_content all true.
- Isolated wheel import probe confirms actual module beneath uv cache site-packages, not checkout; version 0.1.0, Git commit/dirty null, normalized source-content SHA256 `f4380e5781098d65bfdd3ed7418450900810fa3c3e44a652d1a7abf4144b9d15`.

Generated evidence: `.firecrawl/slice2-acceptance-ab93bee1b9034fe9bfdea5276fab9a6c/acceptance.json`. Contains retained untampered run-1, deterministic run-2 and tampered-copy, with the original input moved to an unavailable filename. Decisions SHA256 `322F3199D4557DDBD311F6ACCFD0DC42BFBE844705EA8E8AA11C1038ACF5A5E2`. These generated data are ignored locally; reproducible scripts and exact evidence pointers are committed.

Limits: Windows symlink creation requires an unavailable privilege; local tests use mock rejection checks and live symlink behavior remains unproven here. Hashes are not signatures against coordinated malicious rewriting. Ordinary scenario outcomes remain unsealed/unscored. No network capture, sealing, policy promotion, push, main merge, or deployment occurred.
