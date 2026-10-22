# TrailForge Finish Readiness

TrailForge already has a substantial deterministic engine, temporal evidence boundaries, frozen decisions, persistent experiments, inspection/replay, tamper detection, source-backed fixtures, and a local workbench. Those are infrastructure, not the finish line.

## Finished enough to use

TrailForge becomes operationally useful when it can answer:

**Which signal families would have put us in front of real power projects materially earlier than conventional discovery, and who could we have approached at that time?**

## Next acceptance milestone

Run approximately 20-50 historical real projects. For each: establish identity, reconstruct chronology, define a verified downstream milestone, replay without future leakage, record first valid surface, calculate lead-time advantage, record buyer-path availability, and keep unresolved evidence explicit.

Produce a cohort report comparing signal families by lead-time advantage, coverage and action burden. At least one signal family must demonstrate repeatable commercial usefulness before expanding architecture or optimization machinery.

## Not required now

More governance layers, autonomous outreach, hosted multiuser deployment, broad UI redesign, fuel-provider-first workflows, generic RFP scraping as the main product, or automatic GridLens promotion.

Once a signal family is validated, define the smallest GridLens live integration that can detect it and create a direct-buyer pursuit.

## Cohort report tooling

`python -m athena_procurement_arena compare-signal-families --cohort COHORT.json --target-type TYPE --output REPORT.json`
treats each signal type as a one-family policy and reports, per family: coverage, median lead
time (days), surfaces with no verified target (unresolved, not counted as false alarms), signals per surfaced project (action burden), and buyer-path
availability (a `buyer_path` claim on a signal at or before first surface). The report states
whether the cohort is inside the 20-50 target and whether any family is repeatable (at least
5 matched projects with positive median lead). The tooling is complete; the cohort itself is
not: building 20-50 source-verified historical traces requires reviewed external research, and
the repository's current corpus (8 pre-RFP families) is below target. Do not read a report on
fewer than 20 projects as evidence of a validated signal family.
