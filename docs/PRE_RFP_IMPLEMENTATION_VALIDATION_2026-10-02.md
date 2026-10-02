# Pre-RFP implementation validation — 2026-10-02

## Scope and identity

Slice A extends the existing engine with source-bound case import and offline
cohort replay. It does not satisfy the full pre-RFP lab finish contract.

Base remote-main commit: `6a9ffa332f6dd0b89a14acfcbaed2a99cc7f06cb`.
Branch: `codex/trailforge-pre-rfp-lab`. Exact reviewed file identities, final
validation and independent verdict are retained under
`.agent/artifacts/pre-rfp-slice-a/`; the PR records the final implementation
commit. A report cannot contain its own eventual Git commit hash.

## Real cohort

Eight real families, zero synthetic cases in the cohort; eleven retained public
source captures. Synthetic cases remain in behavioral tests only.

- Four observed procurement/delivered-generation cases: PRF-001, 005, 006, 007.
- One negative generation-scope look-alike: PRF-008 (forecast consultancy).
- Three unresolved cases: PRF-002, 003, 004.
- Vertical distribution: utility 5; data center 1; institutional 1; fixed oil
  and gas 1. Mining and water/wastewater are not represented yet.

The [corpus record](../research/pre-rfp-corpus/README.md) identifies every family,
source, commercial qualification limitation, and current-procurement example.
Sources include PSEG Long Island, LIPA, IESO Nova Scotia, City of Morgan Hill,
Prometheus Hyperscale, Conduit Power, and Aggreko. Supplier reports are attributed
claims. They do not establish independent technical performance.

## Temporal and replay evidence

Eleven historical source entries retain UNKNOWN verified availability and are
excluded from strict replay. Eleven distinct capture-observation events describe
the statements observed on October 2; they cannot appear at earlier cutoffs.
The original source-reported dates remain separate. Neither a printed date nor
an acquisition timestamp is relabeled as historical publication proof.

The workflow binds capture hashes, source quotes, scenario claims and timestamps,
preserves family membership, and runs the existing TemporalWorld and frozen
ledger. BASELINE_A experiments use the existing persistence/verification path;
the small PRE_RFP_BASELINE_V1 callback has separately retained hashed decisions.
Replay requires no network. Source binding verifies identity and declared review
consistency; it does not automatically prove semantic truth of annotations.

## Baselines and limitations

The initial real-corpus replay yielded three PRE_RFP_BASELINE_V1 research surfaces
and zero BASELINE_A surfaces. These are **current-source research decisions**,
not historical successful predictions. The new callback requires a real project,
supported generation need, concrete reason, and organization; MW may be UNKNOWN.
It suppresses supported already-awarded, resolved-supply and out-of-scope claims.

Supported historical lead-time results: **0**. Historical median, useful lead
time and prospective lead time: **UNKNOWN**. Discovery credit: **false**.
No evidence establishes a materially earlier unseen/prospective signal. Small,
deliberately selected development cases cannot estimate generalization,
false-positive rate, miss rate, or statistical confidence. Alert counts are not
an equal-attention-budget candidate comparison.

## Athena, holdout and Jev

All eight families were exposed during development. Sealed holdout: **NOT RUN**;
none of these cases may be represented as untouched. Athena candidate lessons,
promotion, research-order experiments, source-value ranking and real-world
feedback learning: **not implemented in this slice**. No policy self-promoted.
Jev: **not used**. Research/model cost and token usage: **UNKNOWN**.

## Validation evidence

Builder validation after the bounded UNKNOWN/family-identity repair: **318
passed, 1 skipped**; focused case tests: **21 passed**. Compilation, Ruff, and
three existing fixture-bundle checks passed. Controller confirmation and the
independent verdict are retained separately in the agent evidence bundle; only
the final candidate logs count as release evidence. The mandatory gate is:

```powershell
uv run --python 3.11 --with pytest --with ruff python scripts/validate.py
```

The relevant direct procurement-arena suite is also required. Final validation
must be rerun if implementation or corpus bytes change. A passing test gate
establishes mechanics and boundary behavior, not commercial signal quality.

The controller runtime probe executes the real corpus twice with Python network
connections and Firecrawl capture disabled. It compares per-case input,
experiment-manifest and decision hashes. The only excluded result field is the
output experiment directory, which necessarily differs between two fresh runs;
there is no claim that directory-bound aggregate JSON is byte-identical.

## Deferred

Independent historical version-availability proof; earlier precursor timelines;
20–50 deep families; deterministic document relevance classifier and broad
candidate scanner; actual active-monitor execution; unseen family holdout;
Athena candidate and research-order experiments; equal attention budget;
prospective name-blind acquisition; commercial feedback path. These remain
explicit graph nodes, not implied completion claims.
