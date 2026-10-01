# TrailForge

TrailForge is a deterministic early-project signal laboratory for temporary and distributed power.

Its job is to discover which public signals would have identified a real power project early enough to create a commercial lead-time advantage. TrailForge replays historical project timelines using only evidence available at each point in time, measures when a policy would have surfaced the project, and compares that date with later obvious procurement or construction milestones.

## Commercial objective

Reach the customer before the opportunity becomes obvious to the broader temporary-power market.

`EARLY SIGNAL -> PROJECT -> POWER-GAP HYPOTHESIS -> DIRECT BUYING CHAIN -> CUSTOMER CONTACT -> VERIFIED POWER NEED -> FUEL STRATEGY`

Fuel providers are downstream solution partners, not the primary discovery channel.

## Primary metric

**Lead-time advantage**: how much earlier a source-backed signal could have surfaced a project before a conventional procurement, RFP, permit, commissioning, energization, or other obvious market signal.

Supporting metrics: project identification rate, action burden, buyer-path availability at signal time, and evidence quality.

## Current product

The deterministic engine, temporal evidence controls, frozen decision ledger, experiment persistence, inspection, replay, provenance, outcome sealing, and local workbench remain useful infrastructure.

Run the workbench: `uv run --python 3.11 trailforge-ui`

Run validation: `uv run --python 3.11 --with pytest --with ruff python scripts/validate.py`

The workbench proves experiment mechanics. It does not yet prove commercial signal quality.

## Next milestone

Do not add another architecture or governance layer. Build a historical cohort of approximately 20-50 real power projects with known downstream milestones. Reconstruct their source-backed timelines, replay candidate signals without future leakage, record the first valid surfaced date and buyer path, and measure lead-time advantage.

The milestone succeeds when at least one repeatable signal family surfaces commercially relevant projects materially earlier than conventional discovery without unacceptable noise.

Winning signal policies then move into GridLens/live discovery. TrailForge is the proving ground; GridLens is the operational discovery surface.

## Guardrails

Never use future evidence, invent facts, or convert UNKNOWN into certainty. Keep direct-customer discovery upstream of fuel-provider selection. Preserve prior experiment/review artifacts as historical evidence.
