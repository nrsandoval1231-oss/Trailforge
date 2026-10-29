# TrailForge — Canonical Product Vision
Status: Owner-approved October 29, 2026; replaces October 16 opportunity-prediction-first direction.

**TrailForge is an RFP/RFI-first procurement intelligence product**: discover early procurement signals, monitor current and ongoing solicitations with verified source status, and preserve expired/awarded/canceled records for historical research and anticipated rebids. **Discover early. Pursue intelligently. Learn from history.**

[Read the canonical PRD](PRD.md) for full requirements, statuses, data contracts, release gates and acceptance criteria. If prior research, mining, UI or architecture documents conflict, this document and PRD govern future work.

Four primary destinations: **Discover**, **Live**, **Archive**, **Intelligence**. A procurement record distinguishes document type (RFI vs RFP vs RFQ etc.), stage (market research vs bidding), and evidence-backed status (open, unknown, expired, canceled, awarded, etc.). Never infer an open tender from a search snippet. Track amendments, official deadline and timezone, changing terms, source freshness, buyer, attachments, and supplier fit. Expired notices become a searchable intelligence asset, not junk.

First commercial focus: energy, distributed/temporary/bridge power, industrial infrastructure and mining procurement. First supplier reference: 2G Energy Rental; core schema is supplier-independent. Match customer needs to supplier eligibility only after scope is grounded. Track recurring issuers and historical awards only where sources establish them. Any anticipated rebid is a forecast, never a live opportunity.

Reuse the Python modular monolith, Firecrawl-backed discovery, deterministic ranking as candidate triage, captures/provenance, append-only review, replay, historical cohort work and mining pack as supporting capability. Build source-specific official-portal verification, typed solicitation objects, change tracking, alerts and historical issuer intelligence incrementally. Keep public/licensed vs confidential access rights isolated. Do not add autonomous bid submission, speculative compliance claims, microservices or unnecessary agent systems.

**Current reality:** a local operator app and unreviewed live lead search exist; full verified status tracking, continuous monitoring and supplier-specific procurement intelligence are planned work, not shipped capabilities. Historical dossiers are research, not proven predictions.
