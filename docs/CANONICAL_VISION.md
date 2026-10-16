# TrailForge — Canonical Product Vision
Status: Owner-approved direction, 2026-10-16. This is product intent, not a claim of implemented functionality.

## Mission
TrailForge is a supplier-centric universal opportunity prediction engine. It learns what a supplier can deliver, observes changes in the world, identifies unmet commercial requirements before procurement becomes obvious, tests those hypotheses, and recommends evidence-backed actions. **Remote mining power is the first intelligence pack**, but the core must remain industry-independent.

## Product boundaries
1. Discover the customer's need independently of supplier technology. For remote mining, include diesel, natural gas, propane, LNG, renewables, BESS, hybrid, grid extension, and power-as-a-service. Never filter discovery through 2G's fleet.
2. Model each mine/site and each phase-specific power requirement separately. Distinguish exploration, early works, construction, commissioning, bridge, expansion, permanent off-grid, backup, and replacement.
3. Match supplier offerings only *after* a need hypothesis exists. A supplier profile specifies geography, equipment, fuel, voltage, duty, reliability, logistics, economics, delivery, ownership and commercial exclusions.
4. Separate technical compatibility, commercial viability, procurement accessibility, timing, and evidence strength. Unknown is not a failure or a fact.
5. Retain active RFQ/RFP discovery alongside pre-procurement forecasting. Distinguish package still available from package already awarded or delegated.
6. Produce an actionable brief: what changed, verified evidence, estimated demand, dependency, buying chain, supplier fit, unresolved questions, best next research/contact action.
7. Record forecast versions and outcomes immutably. Historical reconstruction is not independent discovery. Compare against simple baseline policies, include negatives and unresolved cases, and measure qualified conversations and useful lead time rather than alert counts.

## Mining Intelligence Pack v1
Discover remote mining and mineral-processing operations, including lithium brine extraction and associated industrial facilities. Track project stage, owner/operator, location, development schedule, mine/plant loads by phase, normal and peak demand, load profile, duty, redundancy, grid availability, fuel supply and storage, site access, emissions, environmental derating, voltage/frequency, black start, contract model, package boundaries, EPC/EPCM and buying decision path. Represent source-backed observations, estimates, conflicts and unknowns explicitly.

**Dependency engine:** connect construction/commissioning milestones to required-by dates for power, fuel, access, permits, and grid delivery. Research the missing condition most likely to change an actionable decision.

**Solution neutrality:** compare feasible solution classes without assuming all are interchangeable. Hard exclusions (e.g. specified fuel-only RFQ) must be respected; alternate solutions may be considered only where permitted.

**Supplier matching:** rank supplier-specific opportunities by fit, accessible buyer, procurement openness, expected value, urgency, and research cost. Never label a supplier as compliant without supporting engineering evidence.

## Core data contracts
Supplier; Offering; Entity (company, project, site, asset); Evidence (provenance, permissions, content hash); Event (event time, publication time, first observed time); PowerRequirement (project phase, loads, operating envelope, requirement status); Dependency (needed-by, state, evidence); DemandHypothesis (falsifiable claim); Forecast (immutable issue time, horizon, policy version, evidence snapshot); Opportunity (supplier-scoped, buyer, package, fit); Outcome (qualified, disqualified, won, lost, unresolved, independently observed). These are logical concepts, not a mandate for separate services or tables.

Source access is scoped: public/licensed shared observations may feed shared intelligence; private customer documents and annotations must remain tenant-isolated and cannot be published, used for cross-customer matching, or used to train shared models without explicit rights. Redacted reference documents are not automatically public evidence.

## Implementation principles
Keep the existing Python temporal replay, immutable captures, decision ledger, provenance and workbench. Build an incremental modular monolith with PostgreSQL and durable background jobs only when operational requirements justify them. No microservice or agent proliferation. LLMs may extract, propose hypotheses and plan research; deterministic validation and reviewed evidence control factual promotion. Athena methods are optional validated forecasting policies, not a runtime dependency. GridLens is an optional downstream/upstream integration, not the product's owner.

## Delivery sequence
1. Audit existing code/contracts and map reusable components against the above concepts; do not pretend documentation means implementation.
2. Implement one mining project + multi-phase power requirement extraction and evidence review using public/licensed sources.
3. Implement technology-neutral requirement qualification, then one supplier profile (2G as first reference) with hard constraints and explicit unknowns.
4. Implement buying-chain, package availability and next-action brief.
5. Reconstruct 20–50 historical mining power cases, including negatives, and run date-safe baselines. Prospectively test discovery without future-name seeding.
6. Add second supplier type before second industry to prove supplier portability. Expand geography/industry only after measurable commercial value.

## Success and falsification
Measure useful lead-time advantage, verified power requirements, supplier-accepted qualified opportunities, attributable customer conversations, cost per accepted opportunity, evidence completeness, false positives and missed projects. If the engine does not outperform basic alerts/manual research, do not add sophistication to conceal failure.

## Canonical authority and legacy
This document governs forward-looking product direction. docs/PRE_RFP_DISCOVERY_STRATEGY.md and docs/PRE_RFP_SLICE_A.md describe earlier power-specific research methods and remain historical implementation references, not competing product visions. Existing CLI, fixtures and validation remain supported until explicitly migrated. Never import confidential customer RFQs or engineering drawings into public corpora.
