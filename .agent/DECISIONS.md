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

## Repository audit 016

- Capacity evidence is typed by role, not just by unit: requirement fields
  (`required_*`, `temporary_*`, `commissioning_*`, `construction_*`, `bridge_*`)
  can satisfy the minimum-capacity gate; rating and aggregate fields
  (`generator_*`, `prime_*`, `nameplate_*`, `standby_*`, `facility_capacity_mw`,
  `aggregate_mw`, `program_mw`, `total_mw`) never can.
- Report the distinction explicitly with
  `CAPACITY_EVIDENCE_IS_RATING_OR_AGGREGATE_ONLY` so a held record is
  explainable rather than silently absent.
- Keep one implementation of the validation gate (`scripts/validate.py`) that
  Windows, Linux, and CI all invoke, so a passing local run means a passing
  remote run.
- Pin the Ruff ruleset in `pyproject.toml` so an upstream default change cannot
  silently alter the gate.
- Run CI on a hosted runner. A gate bound to one personal machine is not a gate.

## Candidate capture 017

- Treat capture cost as a first-class constraint: a screen with no usable intake
  path produces an empty shortlist regardless of how correct it is.
- Derive the source fingerprint from a saved excerpt file rather than a
  hand-entered digest, so a record cannot exist without the evidence text it
  claims to rest on. This strengthens provenance rather than relaxing it.
- Emit ordinary fixture bundles and reuse the existing gate and screen; capture
  adds no second qualification implementation and no privileged path.
- Never infer an omitted field. An uncaptured requirement returns NEEDS_REVIEW
  with the missing-evidence reason, exactly as a hand-authored bundle would.
- Keep capture offline. Discovery (finding listings) remains out of scope and is
  a separate decision, not an implicit consequence of this one.

## Multi-source discovery 018

- Discovery proposes; a human disposes. Nothing in `discovery/` can mark evidence
  verified, and a `ReviewCandidate` carries no verifier field to set. Promotion
  runs through `capture`, which requires a named reviewer and the source text.
- Make the boundary structural rather than advisory: the review queue is a
  different type from a fixture, so there is no path that accidentally promotes.
- Site coverage is configuration, not code. A jurisdiction is a `SourceConfig`
  entry with selectors, so breadth does not multiply parsers to maintain and a
  markup change is a selector fix scoped to one source.
- A shipped source config stays disabled until its selectors are verified against
  a live response. Writing a config from documented shapes is not verification.
- One failing source never fails the sweep, and an erroring source contributes no
  rows rather than stale or inferred ones.
- Triage ranks reviewer attention and qualifies nothing. Keep it separate from the
  fail-closed screen: a HIGH band is not a qualification, a zero is not a
  rejection.
- Retrieval conduct is part of the contract: honor robots.txt, rate limit per
  host, identify the agent, refuse non-HTTPS, and cache raw bytes so the capture
  fingerprint covers bytes actually retrieved.
- Accepted trade-off: HTML scraping across many jurisdictions is fragile by
  nature. The mitigation is config isolation and offline selector validation, not
  a claim of robustness.
