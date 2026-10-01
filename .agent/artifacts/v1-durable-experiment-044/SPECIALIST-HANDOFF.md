Recovery implemented and handed off.

- Fixed snapshot/ledger ordering validation and complete ordered timeline binding in [runner.py](C:\Users\nrsan\Nucleus\02_Projects\Trailforge\src\athena_procurement_arena\runner.py).
- Added regressions for `z,a` ordering, reordered timeline tampering, and malformed snapshot entries/CLI FAIL in [test_experiment.py](C:\Users\nrsan\Nucleus\02_Projects\Trailforge\tests\procurement_arena\test_experiment.py).
- `ordering_probe`: PASS.
- Focused tests: 27 passed; Ruff: PASS; `git diff --check`: PASS.
- Full gate passed before the final one-line source-anchor correction; the subsequent final-gate terminal status is `UNKNOWN` due to interrupted channel output. Controller must rerun it on this exact candidate.
- Handoff evidence: [SPECIALIST-COMPLETION.json](C:\Users\nrsan\Nucleus\02_Projects\Trailforge\.agent\artifacts\v1-durable-experiment-044\SPECIALIST-COMPLETION.json).

No commit, graph/state update, or external action performed.