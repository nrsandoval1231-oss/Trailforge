# TrailForge

**Supplier-centric opportunity intelligence.** TrailForge identifies emerging commercial requirements before buyers publicly procure them, then matches those requirements to suppliers with evidence-backed technical and commercial qualification.

**First market:** remote mining power — technology-neutral discovery across diesel, gas, LNG, propane, solar, wind, battery, hybrid, grid, and power-as-a-service. **First reference supplier:** 2G Energy Rental, without restricting the underlying discovery engine to 2G's fleet.

Read **[Canonical Product Vision](docs/CANONICAL_VISION.md)** for the governing product intent, mining requirements, architecture, data contracts, confidentiality rules, milestones, and validation criteria.

## What exists today
The repository contains a Python deterministic research laboratory with temporal evidence controls, replay, decision ledger, experiment persistence, local workbench, and public-source discovery/opportunity intake. These are foundations, **not** proof of production-ready mining intelligence or autonomous opportunity prediction.

- Workbench: `uv run --python 3.11 trailforge-ui`
- Validation: `uv run --python 3.11 --with pytest --with ruff python scripts/validate.py`
- Existing public-source workflow: [Firecrawl workspace](docs/FIRECRAWL_WORKSPACE.md)
- Historical research methodology: [Pre-RFP strategy](docs/PRE_RFP_DISCOVERY_STRATEGY.md) and [Slice A](docs/PRE_RFP_SLICE_A.md)

## Current priority
Preserve the verified replay/evidence foundation. Add phase-specific mining power requirements, infrastructure dependencies, technology-neutral qualification, supplier-specific matching, buying-chain research, and outcome tracking. Validate against real historical cases and prospective discovery before expanding to other industries.

## Non-negotiables
Separate facts, inference, forecasts and unknowns; prevent future-data leakage; retain source permissions and timestamps; isolate confidential supplier/customer records; do not claim engineering compliance without proof; keep architecture lean; measure commercial usefulness, not alert volume.
