# TrailForge

**Procurement intelligence for early detection, active RFPs/RFIs, and historical research.** Discover early. Pursue intelligently. Learn from history.

**Canonical direction (October 29, 2026):** [Product Requirements Document](docs/PRD.md) · [Canonical Vision](docs/CANONICAL_VISION.md). These supersede older mining-first predictive-opportunity descriptions where they conflict.

## Product
- **Discover:** RFIs, sources-sought, advance notices and upcoming bids, clearly distinguishing research from solicitations.
- **Live:** authoritative, currently open RFP/RFQ/RFI/tender notices with deadline, timezone, amendments and documents.
- **Archive:** expired, canceled, awarded and withdrawn solicitations retained for research.
- **Intelligence:** recurring issuers, historical procurement, buyer patterns and estimated rebid windows.

First vertical: energy and temporary/bridge power, industrial infrastructure and mining; first reference supplier 2G Energy Rental. Underlying engine stays supplier-independent.

## What actually exists
Today the repo has a Python research lab, temporal evidence/replay, local operator interface, Firecrawl-backed **manual** Find searches, heuristic lead ranking and a mining intelligence pack. Candidate labels and snippet dates do **not** verify a live RFP, status, deadline or compliance. Scheduled source monitoring, authoritative lifecycle verification, full procurement records, amendments and archive intelligence are **new requirements**, not shipped features.

- Start local operator: `uv run --python 3.11 trailforge-ui --saved-only`, open http://127.0.0.1:8765/app.
- Current Find tab: http://127.0.0.1:8765/app#/find, see [existing behavior](docs/FIND_LEADS.md).
- Existing research replay: http://127.0.0.1:8765/.
- Tests: `uv run --python 3.11 --extra dev python scripts/validate.py`.
- Earlier mining work: [Mining Pack](docs/MINING_PACK.md); earlier predictive research: [Historical methodology](docs/PRE_RFP_DISCOVERY_STRATEGY.md).
- [New UI direction](docs/UI_VISION.md) · [Delivery gates](docs/FINISH_READINESS.md).

## Non-negotiables
Document type ≠ procurement stage ≠ verified lifecycle status. RFI does not imply purchase. No "open" from a snippet, no invented contacts or deadlines, no deleted expired leads, no lost amendment history, no unlicensed redistribution. Separate observation, inference and prediction; favor source-backed actions and supplier fit over alert volume. Keep existing working components until migrated and tested.
