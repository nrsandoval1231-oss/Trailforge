# Mining Intelligence Pack — Requirement Contract v1
Status: implementation specification; not yet a working parser or matching service.
Authority: [Canonical Vision](CANONICAL_VISION.md).

## First vertical slice
Take a public/licensed mining-project source, identify the project and distinct phases, record evidence-backed power requirements, and generate a neutral research brief before applying a supplier profile. Existing capture/replay code remains the temporal and provenance foundation.

## Minimal record
```json
{
  "schema_version": "mining-power-requirement-v1",
  "requirement_id": "project-id:phase-id:power-use",
  "project_id": "stable-project-id",
  "phase": "CONSTRUCTION",
  "use_case": "COMMISSIONING",
  "status": "HYPOTHESIS",
  "demand": {
    "normal_kw": null,
    "peak_kw": null,
    "duty": "UNKNOWN",
    "redundancy": "UNKNOWN",
    "distribution_voltage_v": null
  },
  "delivery": {
    "needed_by": null,
    "expected_months": null,
    "grid_available": "UNKNOWN",
    "fuel_constraints": []
  },
  "procurement": {
    "model": "UNKNOWN",
    "package_status": "UNKNOWN",
    "buyer_entity_id": null
  },
  "evidence": [],
  "unknowns": ["load", "schedule", "buyer"],
  "review": {"state": "UNREVIEWED"}
}
```

All numeric values must carry units and evidence bindings in the eventual persisted implementation; the compact example uses explicit unit-bearing keys. Every non-null field derived from a source must point to a capture hash, exact quote/span, and timestamp. Estimates must carry method and range. Conflicts remain unresolved until reviewed. No LLM-generated estimate is promoted to VERIFIED.

## Controlled vocabularies
Phase: EXPLORATION, EARLY_WORKS, CONSTRUCTION, COMMISSIONING, INITIAL_OPERATION, EXPANSION, OPERATIONS, RESTART, CLOSURE, UNKNOWN.
Use case: CAMP, DEWATERING, CRUSHING, PROCESSING, COMMISSIONING, BRIDGE, PRIME, BACKUP, SUPPLEMENTAL, ELECTRIFICATION, OTHER.
Requirement status: OBSERVED, HYPOTHESIS, VERIFIED, DISPROVEN, SUPERSEDED.
Procurement package: UNKNOWN, NOT_STARTED, PLANNED, SOURCING, OPEN, AWARDED, CANCELED, CLOSED.
Technology is **not** a required discovery field. Fuel and technology restrictions belong to explicitly evidenced constraints.

## Invariants / acceptance tests
1. One mine may contain three different power requirements with different loads, stages, and dates; never overwrite or sum them without an explicit scenario.
2. A 7 MW peak must not become 7 MW firm capacity without temperature/altitude derating, parasitic loads, reserve and N+1 analysis.
3. UNKNOWN load remains eligible for research, not an automatic rejection.
4. A source saying 'propane only' excludes diesel and natural-gas bids for that procurement; do not exclude discovery of the project.
5. A supplier match is scoped to one offering and one requirement, with distinct technical, commercial, procurement and evidence verdicts.
6. A known project name discovered retrospectively never earns independent pre-RFP discovery credit.
7. Private RFQ attachments are not copied into shared source corpora or committed to Git.
8. An awarded package is not presented as OPEN merely because the parent mine is under construction.
9. Different observation and event timestamps are retained; replay cannot use future evidence.
10. An extraction produces an evidence-linked brief and an actionable unanswered question, not a fabricated probability.

## Engineering sequence
Implement a typed schema and validation in the existing Python package; add fixtures and tests for the invariants above; wire an operator-reviewed import to the existing public capture flow; render the neutral requirement brief; then introduce supplier profiles and matching as a separate subsequent slice.

## Scope exclusions
No broad worldwide crawler, no autonomous outreach, no trained forecasting model, no customer-private document ingestion, and no new microservice in this slice.
