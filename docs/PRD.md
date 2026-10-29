# TrailForge — Product Requirements Document
Status: CANONICAL product direction approved October 29, 2026. Product intent, not an implementation claim.
Authority: This PRD supersedes the former supplier-centric opportunity-prediction vision where inconsistent. See CANONICAL_VISION.md.

## Mission
TrailForge is a procurement intelligence engine: discover relevant RFPs, RFIs, RFQs, tenders, IFBs, sources-sought notices and pre-solicitations as early as possible; verify and monitor current opportunities; preserve expired and awarded notices as searchable intelligence to anticipate future procurement. **Discover early. Pursue intelligently. Learn from history.**

## Users and beachhead
First user: commercial business development and bid teams supplying energy, temporary/bridge power, generation, infrastructure and mining projects. First reference supplier: 2G Energy Rental, not an exclusive filter. General-purpose procurement records and supplier matching must remain extensible. Prioritize quality and primary sources over coverage claims.

## Primary lifecycle and navigation
1. **Discover — early:** Advance procurement notices, procurement plans, RFI/market soundings, sources-sought, upcoming tenders, buyer forecasts and newly discovered solicitations. Clearly distinguish preliminary market research from a formal bid invitation.
2. **Live — actionable:** Source-confirmed open RFP/RFQ/RFI/IFB/tender records with submission dates, timezone, issue and amend history, scope, official portal and response instructions. Unknown/ambiguous status is not Live-confirmed.
3. **Archive — historical:** Deadline-expired, canceled, withdrawn, awarded and closed notices (with separate reason/status); documents and versions retained subject to rights, including award/renewal and issuer history. Archive never implies a new opportunity is currently open.
4. **Intelligence — learn:** Repeat issuers, seasonal cycles, prior awards/incumbents where public, category budgets and contract term, next plausible rebid windows (labelled forecast), sourcing patterns and supplier fit.
Navigation is top horizontal, no left sidebar, no background photography, dense useful data and a dedicated full-page solicitation detail. Avoid unrelated dashboards.

## Solicitation record
Canonical logical entity: stable issuer + procurement identifier + procurement package, with alias/URL deduplication; child records for revisions, addenda, lots, sites, submission milestones, awards and related earlier RFIs. Fields: original and normalized title; solicitation type; issuer/buyer, jurisdiction, sector/location; scope and technical requirements; publishing/source-observed timestamps; deadline with timezone; questions/pre-bid/site-visit dates; portal URL and submission channel; contact role/email/phone only when source-backed; attachments/hash/provenance/permissions; amount/term if published; current state, state source and last checked; source quotes; matching suppliers and gaps; next actions. Preserve unknowns; never invent a due date, buyer, tender status, engineering compliance, award, or renewal.

## State model
Separate **document type** (RFI vs RFP etc.), **procurement stage** (planning, market research, soliciting, evaluation, awarded) and **status** (not yet open, verified open, deadline passed, canceled, withdrawn, awarded, closed, unknown). An RFI can be open for information yet not represent a purchase. Deadline inference from snippet is unverified. Confirm open/extension/award from authoritative source or dated official document; stale confirmation expires to needs-recheck, not silently "open". A past date alone is not evidence of an award or cancellation. Every status transition keeps timestamp, provenance and prior values. Amendments can extend deadlines and supersede earlier requirements.

## Discovery and monitoring
Start with source-specific adapters for official government/utility/agency portals and public vendor portals, feeds, procurement calendars, official notices; use Firecrawl/search as discovery assistance, not the canonical truth. Record coverage, scan time, errors, freshness and crawl costs. Search continuously on a controlled schedule once operationally configured; incremental fetch and conditional updates avoid repeated full crawls. Detect new notices, stage transitions, amendments, deadline changes, cancellations, awards and related reissues. Deduplicate without losing lots or document versions. Alert only on material changes and matching opportunities; do not promise coverage where a portal is unavailable. Respect terms, robots, credentials, rate limits and access rights.

## Supplier fit and ranking
First establish what the solicitation requests; then evaluate supplier profile (equipment/services, capacity, geography, response eligibility, mandatory requirements, lead time, contract size and exclusions). Rank by verified deadline/actionability, hard eligibility, supplier fit, potential value, evidence confidence, and time-to-respond. Display disqualifying requirements and unknowns. Never label a supplier compliant without documentation. Keep 2G as reference profile; no re-renter bias hardcoded into generic engine.

## Operator workflows
One-click access to authoritative source and attachments; save/track/dismiss/snooze; watch issuers; compare amendments; capture decision notes and follow-ups; export/copy a pursuit brief with source links, requirements, contact, deadline, risk and next action. No autonomous submission, outreach, bid generation, or purchases in MVP. Alerts should name the actual change and link to proof. Preserve review state across rediscovery.

## Historical research
Expired and completed procurement notices are a first-class product data asset, not discarded leads. Analyze repeating procurement, contract terms, award history, recurring buyers, vendor incumbency where disclosed and potential rebid windows. Historical forecasting must be labelled estimate with methodology and confidence, not a current tender. Preserve hindsight-safe temporal evidence and do not leak subsequently known results into historical "early detection" evaluations.

## MVP delivery / acceptance
**M0 — baseline:** Audit and keep working lead search/classifier, local operator app, evidence and temporal controls; map existing contracts, tests, docs and any old PRDs to this PRD.
**M1 — real records:** Ingest real notices from 3–5 selected official sources across energy/infrastructure; dedupe; capture authoritative attachments, types, issuer, dates, source and unknowns. Show Discover/Live/Archive with source-backed status and timezones.
**M2 — change detection:** Incremental rechecks, amendments, deadline changes, expiry and disposition transitions with immutable history; show last checked and source availability.
**M3 — actionability:** Supplier filters, hard exclusions, alerts/briefs, watchlist and next-step workflow. At least one real user can move a source-backed solicitation from detection to decision.
**M4 — archive intelligence:** Historical issuer/tender relationships, recurring procurement and explicitly estimated rebid predictions, tested on out-of-sample past cases.
Acceptance: no false "verified open" based on snippets; no conflating RFI and RFP; no lost records on expiry; document versions retained; every cited fact traceable; duplicate same tender suppressed while distinct lots preserved; tests cover timezone, extensions, errors, archive status, cancelled/awarded and stale sources. Measure actionable relevant notices, lead-time vs baseline portals, missed opportunities, false-positive rate, amendment detection latency, source freshness, alert-to-decision time and cost per qualified lead. Do not treat alert volume as value.

## Scope boundaries / legacy
This PRD supersedes mining-first opportunity prediction as the default workflow. Mining Intelligence Pack, pre-RFP historical cohorts, replay, Athena experimentation, vendor-neutral power qualification and the Oct 27 historical workbench remain useful optional research/components, not the home screen or launch gate. Keep working code/API/tests and honest documentation; migrate incrementally. No microservices, autonomous outbound bids, broad CRM, or production claims without evidence. Shared/public source rights and private tenant confidentiality remain mandatory.
