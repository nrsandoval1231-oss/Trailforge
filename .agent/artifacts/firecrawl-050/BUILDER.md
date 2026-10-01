# FC-050 builder handoff

**Status:** implementation candidate ready for parent validation and independent Sol review. No commit, PR, merge, deployment, outreach, or proposal submission performed.

**Scope:** added bounded Firecrawl CLI search/capture, configurable broad and host-targeted catalog, evidence-bound local opportunity import, immutable capture/original retention, deterministic identity/deduplication, strict screen mapping, and static operator workspace. Kept simulation/replay code and the existing experiment-only UI unchanged. Windows `.cmd` is resolved to the installed Node/Firecrawl JavaScript entry point before argument dispatch so selected URLs containing `&` stay intact. Capture sidecars preserve raw provider JSON and the requested max-age/cache fields; missing provider cache timestamps remain `UNKNOWN`.

**Builder-owned changes:**

- `src/athena_procurement_arena/firecrawl_discovery.py`
- `src/athena_procurement_arena/opportunity_workspace.py`
- `src/athena_procurement_arena/discovery_cli.py`
- `src/athena_procurement_arena/opportunity_cli.py`
- `src/athena_procurement_arena/public_capture.py` (public literal target checks)
- `config/discovery.catalog.json`
- `docs/FIRECRAWL_WORKSPACE.md`
- `pyproject.toml` (entry points)
- `tests/procurement_arena/test_firecrawl_discovery.py`
- `tests/procurement_arena/test_opportunity_workspace.py`
- `tests/procurement_arena/test_public_capture.py`

**Commands:** `trailforge-discovery search --catalog config/discovery.catalog.json --query-id temporary-generation-rfp --output-dir PATH`; `trailforge-discovery capture --url URL --capture-id ID --captured-by OPERATOR --source-type TYPE --query QUERY --max-age-ms 0 --output-dir PATH`; `trailforge-opportunity import --workspace PATH --input FILE`; `trailforge-opportunity render --workspace PATH --output PATH/index.html`.

**Validation on the current uncommitted candidate:**

- `uv run --python 3.11 --with pytest --with ruff pytest -q tests/procurement_arena/test_firecrawl_discovery.py tests/procurement_arena/test_opportunity_workspace.py tests/procurement_arena/test_public_capture.py` — 21 passed.
- Targeted `ruff check` across builder modules and affected tests — passed.
- `git diff --check` — passed (Git emitted line-ending normalization notices for concurrently edited tracked files).
- Parent-owned real records were imported during integration and one two-record workspace render was inspected. That render preceded the final display/currentness corrections; parent should rerender its final `workspace-v2` after review.

**Known boundary:** lifecycle `OPEN_AS_OF_PUBLIC_SOURCE` is supported only when the exact cited deadline capture has a recent acquisition sidecar with max-age zero. Amendment state remains `UNKNOWN`; `NOT_FIT` reflects the existing 2G strict screen. A mechanical `QUALIFIED` maps to `POTENTIAL_FIT_PENDING_HUMAN_REVIEW`. A general search result never becomes an active RFP by keyword alone.

**Run record:** base `fd772eb2475b24e65ab2221aeeaf8cfe6f1d14e3`; branch `codex/trailforge-firecrawl-vertical-slice`; lane single Luna; model `gpt-6-luna` per dispatch; exact planning/build/validation durations and token counts `UNKNOWN`; implementation correction count 1 (transient syntax indentation found by compile check, corrected before focused validation). No candidate commit SHA exists because the work is uncommitted.
