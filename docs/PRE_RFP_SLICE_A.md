# Pre-RFP Slice A: source-bound cases and baseline replay

Slice A adds a small case manifest over the existing scenario DSL, TemporalWorld,
hash-chained decision ledger, and experiment store. Each case keeps project and
procurement-family identity, power activity, facility, purchase type, fit,
outcome, buyer path, and evidence provenance together. Family IDs are checked
before cohort replay so one family's cases cannot be assigned to different
cohort groups.

Each evidence source references an immutable `public_capture-v1` file by its
capture hash, content hash, source URL, and exact reviewed quote. A scenario
event must bind to those hashes, claims, quote, and all four timestamps. An
evidence record with any timestamp `UNKNOWN` stays in the case manifest and is
excluded from scenario replay. A current capture may be replayed at capture
time when it is explicitly typed `CURRENT_SOURCE_OBSERVATION` with
`CAPTURE_TIME_ONLY`; that observation does not backdate the project event or
establish when an earlier page version was available.

These bindings prove which captured bytes and quote the analyst used; they do
not prove that the analyst's classification is semantically correct. The case
manifest retains that reviewed judgment. The loader also rejects a claimed
availability earlier than a capture unless a separate retained capture binds
the exact content version at or before the claimed availability time.

`PreRfpBaselineV1` is one simple deterministic comparison rule. It emits
`RESEARCH` only when one visible reviewed event supports a project-specific
generation need, gives a concrete reason, and identifies an organization worth
investigating. It permits unknown MW. Visible claims that the need is outside
scope, awarded, or supply-resolved suppress the alert. Existing `BaselineA`
remains available as a comparator and is not modified.

Run all retained case manifests offline:

```powershell
$cases = Get-ChildItem research/pre-rfp-corpus/cases -Filter case.json -Recurse |
  Sort-Object FullName | ForEach-Object { $_.FullName }
$run = "pre-rfp-$(Get-Date -Format yyyyMMdd-HHmmss)"
$artifactRoot = Join-Path ".agent/artifacts/pre-rfp-slice-a" $run
uv run --python 3.11 python scripts/run_pre_rfp_cohort.py `
  --mode BACKTRACE `
  --cases $cases `
  --experiment-root (Join-Path $artifactRoot "experiments") `
  --output (Join-Path $artifactRoot "cohort-replay.json")
```

Use a new run folder for each execution; the experiment store and result files
are write-once.

`DISCOVERY` is also an explicit run label, but it never earns discovery credit
in Slice A. These cases were assembled by backtracing named known projects;
no independent, prospective, name-blind acquisition/evaluation protocol is
implemented here. The output carries the mode and `discovery_credit: false`.
No holdout is claimed: all eight current cases are exposed development cases.

The initial corpus contains eight real public-source families, with eleven
retained primary-source captures. Four cases record relevant/public or private
buying events, one is a negative lookalike procurement, and three have no
observed outcome. Historical source-page versions do not have verified
historical availability in this capture set. Their reported dates remain
metadata and strict historical availability remains `UNKNOWN`. Current-source
observation replay can therefore exercise ingestion and temporal mechanics,
but all first surfaces occur at the October 2, 2026 capture time and historical
lead-time remains `UNKNOWN`.

The cohort result is descriptive plumbing evidence only. It does not establish
predictive performance, independent discovery, a holdout result, a validated
signal family, or commercial readiness. The output preserves each per-case
baseline experiment, pre-RFP ledger hash, first surface, buyer path, UNKNOWN
count, and outcome for review.
