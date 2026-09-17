# Decisions

## 2026-09-08 — Procurement Arena foundation

- Keep Procurement Arena in its own package because the existing
  `athena_arena` package is a separate market-replay Arena.
- Reuse only the existing canonical hashing primitive; do not create a second
  product database or execution interface.
- Treat unknown dependable supply as an explicit unknown result rather than a
  zero-supply estimate.
- Use a small mapping-based DSL loader with JSON required and YAML optional;
  keep scenario persistence separate from the existing market Arena storage.
- Make the world engine callback-based until the policy contract is defined;
  every timeline point still receives a frozen ledger record.
- Synthetic throughput is recorded as a mechanics result only; it is not
  evidence of production forecasting quality.
## Athena optimization loop 002

- Use a deterministic local adapter as Athena's first optimizer integration.
- Evaluate candidates on the full 40-family corpus and report discovery, action
  burden, and cost-proxy metrics separately.
- Preserve the existing six-gate tournament and default to quarantine/rejection
  until verified sealed holdout evidence exists.
- Keep Athena advisory and research-only; it cannot self-promote or perform live
  procurement actions.

## Athena threshold search 003

- Make optimization concrete with a small bounded weighted-score threshold
  search rather than comparing only fixed policy implementations.
- Keep threshold results subordinate to the existing governance gates; a lower
  alert count alone is not an accuracy improvement.
- Continue treating the synthetic family corpus as mechanics evidence, not as a
 substitute for verified historical holdout evidence.

## Verified fixture boundary 004

- Require provenance and a content fingerprint before accepting a source-backed
  fixture into a local bundle.
- Treat train/holdout allocation as separate from evidence verification.
- Require explicit `SEALED_READY` status for holdout scoring; parsing alone never
 makes a fixture scoreable.

## Source-backed fixture 006

- Add only source facts directly supported by an official public page.
- Convert source-local times to timezone-aware timestamps and preserve the
  source's point-in-time availability boundary.
- Keep a verified solicitation without a verified outcome out of sealed holdout
scoring.

## Opportunity lifecycle 011

- Require a current lifecycle status in addition to source verification and target
  qualification before displaying a lead.
- Treat unknown lifecycle as non-current rather than guessing from publication
  dates or stale search results.
- Preserve historical records for training and audit, but keep them out of current
  opportunity output.

## Temporary power scope 007

- Treat maintenance-only solicitations as `OUT_OF_SCOPE_MAINTENANCE_ONLY` and
  return `IGNORE` across built-in policies.
- Permit maintenance language when paired with installation, replacement, rental,
  or temporary-power scope because it may be incidental to the target contract.
- Do not position Trailforge as a maintenance-services lead engine; the target is
  temporary power and generator installation/replacement procurement.

## Scope-labeled corpus 008

- Carry commercial scope as explicit evidence claims rather than relying only on
  family names or keyword coincidence.
- Keep maintenance-only cases in the corpus as negative controls while excluding
  them from actionable policy output.
- Keep synthetic scope labels separate from verified real-world evidence claims.

## Verified outcome scoring 005

- Measure source-backed performance using exact final procurement-state matches,
  separately from synthetic evidence-visibility metrics.
- Require `SEALED_READY` for holdout scoring and fail closed otherwise.
- Attach verified scores to Athena candidates without allowing the score path to
 bypass existing governance gates.

## Prime power threshold 010

- Set the commercial target at prime/continuous operating power of at least 300
  kW, with temporary-power or installation scope.
- Exclude emergency-backup-only opportunities even when their generator rating is
  300 kW or higher.
- Treat missing capacity or prime-rating evidence as non-actionable until verified;
  do not infer qualification from the word generator alone.

## Source-backed target fixtures 009

- Prioritize official records whose scope is generator installation, replacement,
  procurement, or temporary-power readiness.
- Exclude maintenance-only opportunities from training and lead generation.
- Keep solicitation-only records as verified training evidence until a separate
  source establishes the award or completion outcome.

## Current target shortlist 012

- Require lifecycle, source verification, and 300 kW prime-power qualification
  together before producing a current lead.
- Preserve qualified historical records for audit while excluding them from current
  lead output.

## Current shortlist CLI 013

- Make result production explicit through a local bundle path rather than silently
  treating a directory or live feed as verified input.
- Emit compact provenance-bearing records and reuse the existing fail-closed gate;
  do not create a second qualification implementation in the CLI.

## Current opportunity screen 014

- Do not promote a discovery result when lifecycle, capacity, or prime-rating
  evidence is missing.
- Record a screened no-result explicitly so an empty shortlist is explainable and
  does not pressure the system into inventing qualification.
- Treat a 150 kW stationary emergency generator as excluded even when installation
  and transfer-switch work are included.

## Current opportunity screen 015

- Aggregate capacity is not a substitute for per-project capacity evidence.
- Keep a current temporary-generation RFP held until its primary requirements state
  both a qualifying capacity and an acceptable prime/operating-power rating.

## Canonical PRD alignment 016

- Treat the retained Athena Procurement Arena Build Packet #0 as the controlling
  Trailforge product specification, with its hash recorded in `docs/PRD_ALIGNMENT.md`.
- Expand deterministic mutations without changing GroundTruth or making synthetic
  mechanics evidence appear historical.
- A CLI `unit` mode must execute and propagate the domain/invariant suite status;
  a descriptive unconditional `PASS` is not valid execution evidence.
- Report zero model calls and zero storage bytes explicitly for the current local,
  in-memory Arena rather than omitting those observability dimensions.

## Prospective shadow hook 017

- Capture prospective evidence manually and locally with a source fingerprint,
  supplied capture timestamp, frozen prediction manifest, and no outcome.
- A prospective capture remains non-scoreable and execution-authority-free until
  a separate governed outcome-sealing process exists.
## Prospective outcome seal 018

- Bind a ProspectiveShadowRecord to a verified outcome only through an explicit, named reviewer and a local immutable seal.
- Preserve execution authority ABSENT on every seal and cohort; verified prospective outcomes do not grant promotion.
- Store seals and cohorts as versioned JSON with stable hashes; round-trip loading must reproduce the original hash.
- Apply the existing tournament governance floors and Pareto comparison to cohort metrics, not to individual seals.
- Keep the entire pipeline local and network-free; outcomes are supplied, never inferred or scraped.
## Repository audit infrastructure 019

- Pin the Ruff ruleset and line length so upstream default changes cannot silently move the gate.
- Provide one cross-platform validation script (`scripts/validate.py`) that Windows, Linux, and CI all invoke.
- Run CI on hosted `ubuntu-latest` instead of an unreproducible self-hosted Windows runner.
- Expand compressed one-line statements to satisfy the pinned E7 rules on all project-owned code.
- Do not port PR #1's discovery or capture-acquisition modules; keep the repository network-free.

## Explainable bundle screen 020

- Make the local bundle an operator-usable screening queue by emitting every
  fixture, not only shortlist survivors.
- Preserve qualification semantics and expose non-current, held, and rejected
  states with explicit reason codes and deterministic next actions.
- Keep current qualified records at human review and keep all external action,
  discovery, and execution authority absent.

## Project signal ledger 021

- Represent project chronology separately from current opportunity output so
  historical cases can improve the system without being presented as leads.
- Keep public and confidential evidence classes structurally separate; public
  signals require an HTTP(S) source and confidential signals require a local
  source reference.
- Make earliest-signal selection deterministic from observed timestamps and
  exact signal IDs; never infer missing project events from later evidence.
- Defer live acquisition and Athena optimization until the signal contract is
  validated against retained, independently reviewed outcomes.

## Controlled public capture 022

- Make acquisition explicit and one URL per invocation; raw capture is evidence
  collection, not a qualified lead or training label.
- Resolve the Firecrawl executable through the Windows `.cmd` launcher or PATH
  so local and CI environments do not silently diverge.
- Preserve raw content, source URL, provider job ID, capture time, content hash,
  and capture hash; refuse silent overwrite and reject obvious private targets.
- Keep public capture separate from signal extraction, identity resolution,
  Athena optimization, and outreach.
