# Slice 3A repair 1 — reject malformed and ambiguous input

Parent: v1-reviewed-case-045.md; same base 096c65345eeeba18de051cbdf73d73cab0068f33 and branch codex/trailforge-v1-slice3. Repair budget: attempt 1 of 2. One Luna low; no delegation. Read independent REVIEW-1.md when available and actual files, not builder reasoning. Preserve failed candidate and review artifacts.

Allowed edits only: README.md, docs/SLICE3_CASE_READINESS.md, src/athena_procurement_arena/cli.py, src/athena_procurement_arena/runner.py, tests/procurement_arena/test_fixture_experiment.py. Handoff only: .agent/artifacts/v1-reviewed-case-045/REPAIR-1-COMPLETION.json. Do not edit fixtures, world/policy/evaluator, existing tests, state/graph/review artifacts. No commit, push, merge, source acquisition or seal/promotion. Use apply_patch for file edits.

Required repairs:

- Retained input with an explicit fixture_context key must validate even when its value is null. Absent key remains backward compatible with old plain-scenario experiments. Test coherent outer manifest rehash so the context validation is actually reached.
- Malformed nested fixture bundles (including source_url:null and scenario:null) must return structured FAIL, not AttributeError traceback, both on initial CLI selection before output creation and on retained-context inspection/replay. Normalize failures at this adapter boundary; do not broaden protected fixture-loader scope. Tests must reach retained validation with coherent outer hashes and preserve artifacts.
- Legacy scenario/replay modes must reject --bundle or --fixture-id when --experiment-dir is absent rather than silently ignore them. Preserve legitimate plain-scenario legacy paths and unrelated modes using these flags. Test no output is created by rejected mixed inputs.
- README's first workflow must have quoted actual project path C:\Users\nrsan\Nucleus\02_Projects\Trailforge with a portable checkout-root note; remove/fix the orphan later $scenarioFile example. Keep direct fixture selection and unique experiment output, followed by inspect/replay, usable by copying as written. Correct fixture-id help to describe both supported uses if needed.
- Resolve any other actionable findings in REVIEW-1 within this exact scope; escalate conflicting scope, do not invent broader requirements.

Run focused new tests and Ruff, freeze the five files, report hashes and exact command outcomes. Controller will run full gate/runtime/wheel then fresh independent review. Do not self-certify. Record UTC start/finish, model/config, repair count 1; unknown tokens/durations null. Preserve UNSEALED/UNSCORED and honest GT003 negative-case limits. Full Slice3 and V1 remain incomplete.
