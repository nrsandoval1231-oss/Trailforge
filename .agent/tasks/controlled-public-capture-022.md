# Controlled public capture 022

## Objective

Add an explicit public URL capture boundary using the installed Firecrawl CLI.
Persist returned markdown locally with source URL, capture time, provider, job
identifier, content fingerprint, and stable capture hash.

## Allowed files

- `src/athena_procurement_arena/public_capture.py`
- `src/athena_procurement_arena/__init__.py`
- `src/athena_procurement_arena/cli.py`
- `tests/procurement_arena/test_public_capture.py`
- `docs/PROJECT_SIGNAL_TRACING.md`
- `README.md`
- `.agent/artifacts/controlled-public-capture-022/COMPLETION.json`
- `.agent/artifacts/controlled-public-capture-022/REVIEW.json`
- `.agent/CURRENT_STATE.md`
- `.agent/DECISIONS.md`

## Exclusions

No automatic crawling, domain discovery, signal extraction, contact enrichment,
outreach, qualification bypass, Athena promotion, or confidential-source upload.
The capture command is explicit and one URL at a time.

## Acceptance checks

- Public capture requires HTTP(S), rejects obvious local/private targets, and
  records provider and content SHA-256.
- Capture JSON is tamper-detecting and refuses silent overwrite.
- `capture-public` invokes Firecrawl only through the explicit CLI mode and
  outputs machine-readable provenance.
- Scraped content remains raw capture evidence; no claims are auto-promoted.
- Tests, Ruff, compilation, fixture validation, and diff checks pass.
