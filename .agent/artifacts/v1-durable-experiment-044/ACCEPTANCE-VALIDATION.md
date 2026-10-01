# Latest exact-candidate validation

This supersedes FINAL-VALIDATION.md's candidate without deleting that evidence. Its independent REVIEW-FINAL.md found redundant summary fields unbound; those findings were repaired by the summary-binding packet. Independent REVIEW-ACCEPTANCE.md returned PASS for the exact six hashes below, with 52 focused tests independently passed. REVIEW.json binds this bounded acceptance; full V1 remains incomplete.

Final six SHA-256 values:

- README.md: D7E3C95A2D2223B234797551016C104D37D71FDAB6A3296583C02351E4F6E9DA
- src/athena_procurement_arena/cli.py: A07D0BAB9A9D4B20ECD2715870EBDE579B1271FA6E55384E039A813E276B4914
- src/athena_procurement_arena/runner.py: 379C163845697B2F84FBE7EB755431344F25AB615E71F394BE18C0705D20AAA5
- src/athena_procurement_arena/world.py: 415349B228998C6A46D2A75332A3D35438B7125676A81102AC85BF1193C35036
- tests/procurement_arena/test_cli.py: 4BD1A61961C5C19EB8ACA4224959611CB59CCD33B0804CD0ADF87C3EF970D2EF
- tests/procurement_arena/test_experiment.py: 2FF1F3C797000745B75ED256B9AF7A4A0FE869CC38A8B3A8DFE32E0B7B9017C0

Controller results (all commands exit 0):

1. `uv run --python 3.11 --with pytest --with ruff python scripts/validate.py`: 223 tests passed in 30.76s; compilation, Ruff and GT-003/GT-007/GT-008 fixture validations PASS.
2. `powershell -ExecutionPolicy Bypass -File .agent/artifacts/v1-durable-experiment-044/acceptance.ps1`: all nine CLI outcomes correct. Evidence `.firecrawl/slice2-acceptance-d24444d82fe34284ab14727ce14c9529/acceptance.json`; includes saved input, run-1, run-2 and tampered-copy. Decisions SHA256 322F3199D4557DDBD311F6ACCFD0DC42BFBE844705EA8E8AA11C1038ACF5A5E2.
3. `uv run --python 3.11 python .agent/artifacts/v1-durable-experiment-044/ordering_probe.py`: valid unsorted evidence PASS.
4. `uv run --python 3.11 python .agent/artifacts/v1-durable-experiment-044/no_execution_inspect_probe.py .firecrawl/slice2-acceptance-d24444d82fe34284ab14727ce14c9529/run-1`: fresh-process public CLI inspect PASS with world/policy execution disabled; evaluation UNSEALED.
5. `uv build --quiet --out-dir .firecrawl/slice2-wheel-accepted-candidate`: sdist and wheel built.
6. From cwd `C:/Users/nrsan`: `uv run --no-project --python 3.11 --with C:/Users/nrsan/Nucleus/02_Projects/Trailforge/.firecrawl/slice2-wheel-accepted-candidate/athena_trailforge-0.1.0-py3-none-any.whl trailforge replay --experiment-dir C:/Users/nrsan/Nucleus/02_Projects/Trailforge/.firecrawl/slice2-acceptance-d24444d82fe34284ab14727ce14c9529/run-1`: all five checks true, PASS.
7. `git diff --check`: PASS, ordinary line-ending warnings only.

Research-only. No source evidence was fabricated or sealed. No push, main merge or deployment. Windows live symlink test privilege remains unavailable; portable rejection tests are not a live-platform proof. Git and normalized implementation-content identity are separate; dirty source runs are honestly labeled. Hashes check local integrity, not signatures against coordinated rewriting.
