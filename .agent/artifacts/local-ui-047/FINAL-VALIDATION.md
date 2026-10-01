# LOCAL-UI-047 candidate 2 — controller validation

Base:3cedc8711ceec0ac411f04911fa24186a0d6ceb1. Uncommitted candidate on codex/trailforge-local-ui, exact file identities in CANDIDATE.json. Independent review pending when this record was written. Prior failure retained in CANDIDATE-1-VALIDATION.md; one bounded transport repair.

## Deterministic gate

`uv run --python 3.11 --with pytest --with ruff python scripts/validate.py`: exit0, 297 passed / 1 skipped in58.58s, compilationPASS, RuffPASS, three fixture validationPASS, all holdout_available=false. Skipped live symlink test requires Windows privilege; mocked link/reparse checks remain. `git diff --check`: exit0 (CRLF warnings only). `git diff --exit-code -- src/athena_procurement_arena/runner.py src/athena_procurement_arena/cli.py src/athena_procurement_arena/fixtures.py src/athena_procurement_arena/policies.py src/athena_procurement_arena/world.py scenarios/fixtures`: exit0.

## Process and package proof

`uv run --python 3.11 python .agent/artifacts/local-ui-047/runtime_probe.py --bundle scenarios/fixtures/verified/gt-003-morgan-hill.json --evidence-root .firecrawl/ui047-candidate2-runtime`: exit0; six check groups PASS. Run0e9ba4a2de2e4465bbf1e90425dcd092, decisionsSHA256964fd29f9975153b5f2c9d4dc9e7c367100e468cdb47ee3edf918ace61300d26.

`uv build --wheel --out-dir .firecrawl/ui047-candidate2-wheel`: exit0. Packaged index.html/app.js/style.css included.

From C:/Windows/System32: `uv run --no-project --python 3.11 --with C:/Users/nrsan/Nucleus/02_Projects/Trailforge/.firecrawl/ui047-candidate2-wheel/athena_trailforge-0.1.0-py3-none-any.whl python C:/Users/nrsan/Nucleus/02_Projects/Trailforge/.agent/artifacts/local-ui-047/runtime_probe.py --bundle C:/Users/nrsan/Nucleus/02_Projects/Trailforge/scenarios/fixtures/verified/gt-003-morgan-hill.json --evidence-root C:/Users/nrsan/Nucleus/02_Projects/Trailforge/.firecrawl/ui047-candidate2-wheel-runtime`: exit0, six check groupsPASS; run7f5dab095a474048ab7359d9f0cdc046, same decisionsSHA256.

Probe groups: assets served, actual save/inspect/replay with no artifact mutation, identical decisions in separately named runs, Host/Origin/token/traversal/GET-mutation refusals, fresh-process replay without original bundle, corrupted-copy listing/inspect/replay fail without healing. Script and retained artifacts permit reproduction. Runtime outputs are ignored local data, not source approval.

## Browser proof

Actual local launcher on127.0.0.1:8765, no mocked API. Current source candidate restarted before final flow. Browser runf4fb0c9dd81041bf9f625758197819fd: integrityPASS, initial replayNOT_RUN, UNSEALED/UNSCORED. Verify replay returned PASS with source_content/scenario_hash/result_hash/ledger/input_binding alltrue. Server was then stopped/restarted; browser reloaded, reopened that saved run with replayNOT_RUN, explicitly replayed again toPASS. Correct source reviewer and maintenance-only caveat visible. Decision-time strip exposes one then two evidence records at their retained times; actionIGNORE, OUT_OF_SCOPE_MAINTENANCE_ONLY, unknown quantified power retained.

Disposable copied run00000000000000000000000000000000 had input intentionally changed; UI visibly listsFAIL, explains artifact hash mismatch, offers no replay, original remains intact. Screenshot retained at .firecrawl/ui047-browser-failure.jpg. Mobile390px viewport showed no horizontal overflow (document content/client width375); keyboard focus visibly outlined. Viewport reset afterward. Console error/warn logs empty during flow. UI assets unchanged between pre-repair layout/failure checks and candidate2.

Limits: local trusted-user workbench only; no authenticity or forecast-quality claims, no source/availability attestations, no S3B admission. UI controls only configured GT003 fixture; BASELINE_A/seed fixed. Historical experiments made under different source contents can correctly fail replay identity. No parent V1/Build Packet completion. No commit/push/merge/deploy.
