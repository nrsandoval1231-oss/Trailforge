# Canonical PRD alignment

## Current product direction — 2026-10-01

The owner's latest request extends TrailForge with a customer-first power-project
application. [Customer-first V1](CUSTOMER_FIRST_V1.md) governs that extension:
project -> evidenced need -> buyer -> customer conversation -> fuel coordination.
The Arena specification below continues to govern research mechanics and claims;
its original no-UI/product-scope exclusions do not override the owner's explicit
new application request. No external outreach, purchase or deployment is authorized.

## Authority

The controlling specification is **Athena Procurement Arena — Build Packet #0**,
version 1.0 (2026-09-08), retained outside this repository. Its verified
SHA-256 is
`7abb4c4aeb6ab049ea1f2f8888f76bc4f9e96daa3217797b07706bf7858236d8`.

This repository implements the research-only Arena, not the future production
Procurement Intelligence Engine. The packet's no-UI, no-production-scraper,
no-autofill, no-submission, and no-runtime-authority boundaries remain binding.
The owner authorized one narrow exception to the no-UI exclusion on 2026-10-01:
the optional [local experiment workbench](LOCAL_UI_SCOPE.md). It does not
replace or certify Build Packet #0 and grants no production execution authority.

## Current assessment

The repository contains implementation and tests for the packet's DSL, temporal
world and evidence gates, `BASELINE_A` contract and standalone controls, frozen ledger,
separate evaluation dimensions, invariant checks, seeded mutations, power-scope
accounting, adversarial/counterfactual cases, Athena candidate artifacts,
tournament gates, negative knowledge, fixture registry, manifests, and local
validation. The retained [Campaign 001 report](../reports/ARENA_CAMPAIGN_001_REPORT.md)
records the 40-family regression, 10,000-run campaign, and a 100,000-run
benchmark. The 1,000-variant mutation check is in
`tests/procurement_arena/test_campaign.py`. These are repository and historical
campaign claims,
not an independent acceptance verdict for the current candidate.

See [Finish readiness](FINISH_READINESS.md) and the
[independent 20-item re-audit](BUILD_PACKET_0_REAUDIT.md) for the current
requirement evidence map, the local acceptance gaps, the historical GitHub
CI blocker, and the missing
real-world holdout evidence. The campaign report's `66 passed` is its historical
snapshot, not the current test count.

## Evidence boundary

The checked-in source-backed bundles are `VERIFIED`, with no `SEALED_READY`
fixtures or holdout IDs. The built-in GT-001 through GT-006 replay registry is
`UNVERIFIED`. Local prospective capture and sealing mechanisms do not establish
that a real outcome cohort has been independently sealed. Synthetic mechanics
and comparative tests do not prove real-world forecasting accuracy. A governed
challenger-versus-baseline holdout comparison and resulting policy-promotion
decision remain unproven. Missing evidence stays `UNKNOWN`; Athena has no
authority to promote itself or execute commercial actions.
