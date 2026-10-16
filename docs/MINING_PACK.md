# Mining Intelligence Pack v1

This is a working **operator-reviewed import** over the existing public capture boundary,
with phase-specific demand, dependency hypotheses, neutral qualification, separate
supplier screening, immutable exports, and reports in the existing local workbench.
It implements [PR #17's contract](MINING_REQUIREMENT_CONTRACT.md); that specification
is carried forward verbatim. It does not autonomously extract prose or prove predictive
performance. The demonstration is entirely synthetic, not a disguised customer case.

## Run the complete demonstration

From the repository root:

```sh
uv run --python 3.11 trailforge-mining \
  --input scenarios/fixtures/mining/project.json --output local-output/mining
uv run --python 3.11 trailforge-ui --saved-only \
  --mining-input scenarios/fixtures/mining/project.json
```

Open http://127.0.0.1:8765/mining and select `synthetic-copper`. The existing workbench
home also links to mining reports. Explore three separate requirements: 250 kW early
works with a diesel-only constraint, 2 MW propane commissioning, and an operations
requirement with unknown load and an awarded package. None are summed. Inspect the
source disclosures, grid timing hypotheses, 2G fuel rejection, engineering unknowns,
and recommended next actions. Numbers are synthetic illustrative requirements.

The first command also creates a version directory containing `project.json` (including
retained source captures), `supplier.json`, `report.html`, and its stylesheet. Open the
HTML directly if a server is not desired. Identical re-imports refuse to overwrite an
existing version. Workbench inputs are read and validated at startup; restart after
editing a reviewed manifest. Multiple `--mining-input` arguments show multiple projects.

## Import an authorized source

1. Use the existing acquisition workflow, for example:

   ```sh
   uv run trailforge-discovery capture --url https://PUBLIC-SOURCE-URL \
     --capture-id mining-notice --captured-by YOUR_NAME --output-dir local-output/captures
   ```

   This uses the existing Firecrawl CLI and its configured credentials. Alternatively
   freeze already-authorized text with `public_capture.capture_markdown` and
   `write_capture`. The mining importer never calls an external AI provider.
2. Copy the shape of `scenarios/fixtures/mining/project.json` into local output and
   replace the synthetic values with reviewed source claims. Capture paths are relative
   to the manifest. Set `access` to `PUBLIC` or `LICENSED` only when justified and
   `share_allowed: true` only when sharing rights permit the resulting report and
   retained capture. Private sources are unsupported and rejected before source reads.
   This is an operator rights attestation, not automatic confidential-content detection.
3. Set `cutoff`, `reviewed_by`, source `published_at` (or null), `first_observed_at`, and
   `available_at` with timezone-aware ISO timestamps. Retained capture, publication,
   observation and availability must be no later than the cutoff. A current capture
   cannot justify backdated availability. Planned milestone dates can be in the future;
   they are not evidence-availability dates. Historical unknown publication is retained
   as null; captured-at availability is conservative, not historical discovery credit.
4. Enter one requirement for each independent phase/use. Known fields use
   `{"value": ..., "basis": "OBSERVED" or "VERIFIED", "evidence": [{"source": "source-id", "quote": "exact source span", "event_at": null}]}`.
   Verification is the named analyst's semantic judgment: quote/hash checks cannot
   establish that a source supports a value. Missing fields become explicit UNKNOWNs.
   Use `null` for unknown values, never invented zeroes. Field names encode numeric
   units (`normal_kw`, `peak_kw`, `distribution_voltage_v`, `frequency_hz`,
   `expected_months`, `altitude_m`, `temperature_c`). Estimates require basis `ESTIMATE`,
   numeric `range: [low, high]`, a `method`, and supporting evidence. Conflicting field
   values are a list of two or more claim objects; no alternative is silently selected.
5. Supply dependency observations using `GRID_DELAY`, `NO_GRID`, `EXPANSION`,
   `INSUFFICIENT_GENERATION`, `COMMISSIONING`, or `RESTART`, each with evidence.
   The engine also derives hypotheses from phase, absent-grid evidence, and a phase
   date preceding grid readiness. Hypotheses always include a falsifier; they are never
   promoted into confirmed loads or procurement availability.
6. Run the import and workbench commands above against the new manifest.

The source and requirement field lists live in `mining.py` (`PROJECT_FIELDS`, `GROUPS`)
and the example manifest. They include operator, commodity, mining method, milestones,
EPC/EPCM, decision-makers, infrastructure, operating profile, voltage/frequency,
redundancy, environment, fuel, grid, buying window, buyer and package boundary.
Fuel/technology constraint lists mean **explicitly permitted alternatives**, not fuels
merely mentioned nearby. For example `["propane"]` excludes natural-gas and diesel
supplier offerings. Use consistent canonical text labels; V1 does not interpret fuel
synonyms or compound engineering restrictions automatically.

## Supplier profiles and limits

Demand import and `qualify()` never consult a supplier. The older Aura RFP screen is
preserved for existing workflows and is not used by the mining path. No GridLens
service or Athena optimization process is required.

The default 2G profile is deliberately an unverified screening envelope (natural gas /
propane rental); it does not import the confidential reference material or assert
fleet availability, geography, certifications or generator ratings. Use `--supplier`
on `trailforge-mining`, or `--mining-supplier` on the workbench, to load a reusable
profile such as:

```json
{
  "supplier": "Synthetic Diesel Supplier",
  "offering": "Example rental offering",
  "fuels": ["diesel"],
  "technologies": ["diesel generation"],
  "geography": [],
  "commercial_models": ["rental"],
  "available_by": null,
  "nominal_kw": null
}
```

Matches are per requirement and offering, with eight distinct dimensions. Unknown
fleet size, N+1, derating, duty, transients, fuel logistics, pricing and delivery stay
research questions. Nominal rating never proves engineering compliance. AWARDED,
CANCELED and CLOSED packages are unavailable. Other statuses are not called open
unless explicitly OPEN. A fit is a research verdict, not authorization to bid.

## Validation and next improvement

```sh
uv run --python 3.11 --extra dev python scripts/validate.py
```

Acceptance coverage is in `tests/procurement_arena/test_mining.py`, including real
capture validation, immutable export and HTTP report serving without provider mocks.
No customer-private sources are present in the demonstration. Permissions cannot
prevent an operator from falsely labeling private content as public: review source
rights before import. Licensed and synthetic evidence remain visibly labeled.

Highest-priority next improvement: assisted extraction into this reviewed contract,
validated against authorized real mining sources, to reduce manual entry while
measuring citation accuracy and operator review burden. No autonomous discovery,
independent forecast accuracy, licensed-data entitlement verification, or engineered
supplier compliance is claimed in V1.
