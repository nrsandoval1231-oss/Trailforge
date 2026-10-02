# TrailForge Current State — 2026-10-01

## Product reset

The owner reset TrailForge around one commercial objective:

**Prove which early signals can identify real power projects before conventional market discovery, so the direct customer/project team can be contacted first; fuel providers are selected afterward.**

This supersedes older next-step language prioritizing completion of the generic Procurement Arena, additional governance machinery, or RFP-first discovery.

## Current implementation

Main includes the deterministic research engine and merged local experiment workbench from PR #5. Existing evidence/replay/provenance infrastructure is retained. Historical agent packets/review artifacts remain evidence of prior work and must not be rewritten to match this reset.

## Current gap

The engine has not yet demonstrated repeatable lead-time advantage on a meaningful cohort of real power projects. Synthetic mechanics, test counts, already-obvious RFPs, and UI completion do not answer that question.

## Active frontier: HISTORICAL-COHORT-001

Assemble and run approximately 20-50 real historical power projects through the temporal replay engine.

Per project: source-backed chronology; first valid policy surface; verified conventional downstream milestone; lead-time advantage where supported; buyer-path evidence at first surface; unresolved evidence; signal family.

Cohort: lead-time distribution by signal family, coverage, action burden, unresolved cases, buyer-path availability.

## Build priority

1. Adapt existing trace/experiment path to cohort execution.
2. Collect/review first historical cohort.
3. Evaluate candidate signal families.
4. Identify at least one repeatably useful early signal.
5. Define minimal GridLens live integration.

Do not start another architecture initiative before this experiment is runnable.

`SIGNAL -> PROJECT -> POWER-GAP HYPOTHESIS -> DIRECT BUYING CHAIN -> CUSTOMER CONVERSATION -> VERIFIED REQUIREMENT -> FUEL STRATEGY`

Fuel-provider-first discovery is not the product direction.
