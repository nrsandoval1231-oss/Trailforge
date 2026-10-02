# TrailForge

TrailForge is a commercial intelligence and RFP tool for temporary and distributed power, backed by a deterministic early-signal laboratory.

## Two connected operating lanes

**Early projects:** public signal -> project -> possible power gap -> direct buying chain -> customer verification -> solution/fuel strategy.

**Active RFPs:** public solicitation -> original documents -> cited requirements -> strict 2G-fit screening -> response workspace -> human review and submission. TrailForge does not contact buyers or submit bids.

Firecrawl is the broad public-web acquisition layer. TrailForge owns identity, evidence, classification, qualification and operator presentation. Weak evidence remains useful research material; it is not automatically a qualified pursuit.

## Local operator slice

See [Firecrawl workspace commands](docs/FIRECRAWL_WORKSPACE.md) and [real-source evidence](research/firecrawl-2026-10-01/README.md). The initial workflow supports configurable search, selected-source capture, manually extracted exact citations, deterministic deduplication and a generated local operator workspace. It is not a fully automated requirements extractor.

## Signal laboratory

The existing temporal engine, frozen ledger, experiment persistence, provenance and workbench remain unchanged. Run `uv run --python 3.11 trailforge-ui` for the experiment workbench.

Primary research metric: **lead-time advantage**, measured only from source-backed temporal evidence. Live project discovery does not prove historical predictive quality. The [HC-001 five-project pilot](research/hc-001/README.md) reuses existing trace/backtest mechanics. [Availability recovery](research/hc-001/RECOVERY-v1.md) adds archived content: one before-target observation pair, one late-observation control and an earlier official xAI signal. Snapshot intervals are not measured market advantage; that remains UNKNOWN. See [offline cohort commands](docs/HISTORICAL_COHORT.md). Next: independently interpretable procurement milestones before expanding toward 20–50 projects.

Run the full gate: `uv run --python 3.11 --with pytest --with ruff python scripts/validate.py`.

## Guardrails

Never fabricate contact authority, requirements, deadlines or historical availability. Keep UNKNOWN visible. Fuel providers are downstream solution partners. Respect public access restrictions. Preserve prior evidence and source versions. GridLens receives validated signal policies only after historical support; there is no automatic handoff in this slice.
