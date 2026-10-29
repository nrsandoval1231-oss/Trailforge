# TrailForge — Procurement Intelligence UI
Status: Canonical design intent, October 29, 2026. Supersedes the October 21 mining requirement queue and retired Jade visual plan where inconsistent. See [PRD](PRD.md).

**Navigation:** four top-level pages across the top, no left sidebar, no background photography, no large marketing hero. Clear dense tables and dedicated record pages; responsive mobile reading.

1. **Discover:** new and early signals; RFI, advance notice, sources-sought, procurement plan, presolicitation; indicate explicitly whether open for information vs currently accepting bids.
2. **Live:** source-confirmed open notices, deadlines with timezone, issuer, solicitation type, fit, last checked, amendments, next action; sort by urgency without hiding uncertainty.
3. **Archive:** expired, awarded, withdrawn and canceled, each a distinct state, with historic versions, documents and related tenders; search by buyer/category/site.
4. **Intelligence:** repeat buyer patterns, issuer histories, disclosed awards/incumbents, expected rebid windows labeled forecast, source evidence and confidence.

**Solicitation page:** title/type/status and verification stamp; official portal; deadlines/prebid events; scope; lots; original and amended documents; changes timeline; issuer and source-backed contact; requirements and supplier fit; uncertainty; brief/watch/notes. Explicit empty/loading/stale/error states. Every factual claim links to source. An RFI is not displayed as an RFP, expired is not awarded, and unknown does not appear as open.

**Current UI:** the existing operator app and Find tab are real implementations of earlier workflows, not evidence this new navigation is delivered. Preserve functional operator review and mining/replay screens as secondary research tools during migration; do not relabel old routes and claim launch. Prefer simple incremental updates over a total rewrite. Validation: desktop and mobile, keyboard access, no duplicate solicitation cards, empty datasets and no fake seeded data.
