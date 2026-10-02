# Pre-RFP Slice A packet

- Node: HC-001 / Pre-RFP Slice A
- Repository: `C:\Users\nrsan\.codex\worktrees\trailforge-pre-rfp-lab\TrailForge`
- Branch: `codex/trailforge-pre-rfp-lab`
- Base/candidate start: `6a9ffa332f6dd0b89a14acfcbaed2a99cc7f06cb` (clean)
- Builder: primary Luna; start UTC: 2026-10-02 (clock time not captured)
- Objective: add a reusable, inspectable case model and import/replay path over existing scenario-v1 / TemporalWorld / baseline / experiment storage; validate procurement-family boundaries and timestamp integrity; run supplied real cases as they arrive.
- Allowed ownership: `src/athena_procurement_arena/`, affected tests, `schemas/`, `scripts/`, explanatory docs, `.agent/tasks/pre-rfp-slice-a.md`, `.agent/artifacts/pre-rfp-slice-a/`.
- Excluded: `research/pre-rfp-corpus/` evidence acquisition, `.agent/CURRENT_STATE.md`, `.agent/WORK_GRAPH_V1.md`, provider/crawler platform, network during replay, Athena lesson promotion, holdout/predictive claims, push/merge/deploy.
- Dependencies: controller-provided source-backed real case artifacts; existing scenario contract, `TemporalWorld`, `BaselineA`, frozen ledger and experiment persistence.
- Invariants: exact project/procurement family kept whole; explicit UNKNOWN; only `verified_available_at` gates visibility; unsupported availability gets no strict timing credit; immutable document hashes/versions; replay is offline; outputs identify BACKTRACE or DISCOVERY explicitly; Slice A awards neither discovery nor historical performance credit.
- Acceptance: typed/validated case manifest with capture/evidence references; family split rejection; deterministic scenario mapping/replay; machine-readable first surface and baseline evidence; useful focused regression tests; run direct affected suite and mandatory `uv run --python 3.11 --with pytest --with ruff python scripts/validate.py`; exact candidate diff and results recorded in completion artifact.
- Retry budget: two materially distinct bounded repairs. No changed governance/canonical intent.
- Completion handoff: `.agent/artifacts/pre-rfp-slice-a/COMPLETION.json`, focused validation evidence and limitations. Sol review required from controller.
