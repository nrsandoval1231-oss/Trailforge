# Pre-RFP seed corpus — 2026-10-02

Eight real procurement/project families, eleven public-source captures. This is an
exposed **development corpus**, not a sealed holdout or discovery-success sample.
The source-review classifications are human-style analyst annotations, not an
automated relevance classifier. No Jev calls were used.

| Case | Family | Vertical | Evidence state |
| --- | --- | --- | --- |
| PRF-001 | PSEG 2026 temporary generation | Utility | Relevant procurement observed |
| PRF-002 | Montauk 2021–2024 generation plan | Utility | Planned scope; actual outcome unresolved |
| PRF-003 | Prometheus/Conduit Texas partnership | Data center | Partnership announced; buying contract and individual sites unresolved |
| PRF-004 | Morgan Hill UD-RFP-2027-51 | Institutional | Maintenance-led contract with as-needed rental; rental outcome unresolved |
| PRF-005 | Sunbridge Tarzan CNG plant | Fixed oil and gas | Supplier reports delivered 5 MW generation under services agreement |
| PRF-006 | IESO fast-acting generation | Utility | Relevant procurement and amendment observed |
| PRF-007 | Azure Sky commissioning | Utility | Supplier reports completed generation/commissioning service |
| PRF-008 | IESO market-pricing forecasts | Utility | Negative look-alike: consultancy, not generation procurement |

PRF-003 contains two unnamed proposed sites but is counted as **one unresolved
family**. PRF-004 is not labeled generation-not-in-scope: its full RFP includes
Task 4 as-needed rental. Neither rental volume nor award is established.
PRF-008 is a separate consultancy procurement, not another document in PRF-006.

## Evidence and date semantics

Every capture is the unchanged `trailforge-public-capture-v1` output of the
existing explicit `capture-public` command. Captures retain URL, retrieval time,
provider, content SHA-256 and capture hash. The retained raw acquisition output
is Firecrawl markdown, **not the original PDF binary or an archival snapshot**.
Original source URLs are preserved. Source documents and their amendments stay
in one case family. No login, submission or external communication occurred.

Each source has two distinct records:

1. A historical record preserves source-reported dates separately, with
   `verified_available_at=UNKNOWN`. Printed dates and URL directories do not
   prove when this exact version became publicly available. These records are
   excluded from strict replay.
2. A `CURRENT_SOURCE_OBSERVATION` records the captured statement at retrieval
   time. Its four timestamps describe the observation document, not the original
   historical project event. It is visible only from capture time onward.

This permits genuine source-backed, nonempty offline replay without backdating
today's content. It provides **no historical early-warning credit**. The captures
were selected with known identities, so they also provide **no prospective or
independent discovery credit**. Conventional historical milestone timestamps
remain UNKNOWN where their exact boundary is unsupported.

Buyer paths identify organizations supported by source text. They do not prove
that an individual is the buyer or that a package remains available. Supplier
claims remain attributed; they are not independent performance verification.
Azure Sky's 4.5 MW versus 3 MW plus 1 MW BESS descriptions remain unreconciled.

## Acquisition and repeatability

Example (use a fresh versioned output filename for another capture):

```powershell
uv run --python 3.11 python -m athena_procurement_arena capture-public --url 'https://www.psegliny.com/aboutpseglongisland/proposalsandbids/2026tempgenrfp' --capture-id 'pseg-tempgen-NEW-VERSION' --captured-by 'SOURCE_REVIEWER' --output 'research/pre-rfp-corpus/captures/pseg-tempgen-NEW-VERSION.json'
```

Review captured text before creating metadata. Use a new case/scenario version
for corrections after freezing; do not overwrite old source content. The case
loader binds quotes, claims, timestamps, scenario events and source hashes.
Replay and evaluation use retained files and never fetch the network.

## Procurement status observed on October 2, 2026

- **PSEG PRF-001:** official page lists intent October 16 and proposal deadline
  October 30, both 5 PM EPT. Full RFP states minimum 5 MW per project. Total
  program maximum is 400 MW; it is not the size of one rental package. Entry,
  technical fit and remaining scope require review.
- **IESO PRF-006:** Addendum 1 lists January 21, 2027 at 3 PM AST proposal
  submission and August 21, 2026 registration deadline. An extended submission
  deadline does not establish eligibility for a new proponent. Temporary
  construction/rental demand remains UNKNOWN.
- **Morgan Hill PRF-004:** official page says Closed. Its rental attachment does
  not establish an active rental order or expected volume.

These observations are source-backed acquisition outputs, not an active scanner
or pre-RFP performance claim. Recheck before commercial use.

## Missing evidence and next research

Recover immutable historical precursor versions with independently supported
availability; reconstruct the complete buying-event timeline; establish exact
package commitment dates and buyer responsibility at each cutoff. Add mining,
water/wastewater, canceled, rebid and supply-resolved cases. Freeze a genuinely
unexposed family holdout before evaluating any learned candidate. Do not promote
lessons from this development corpus alone.
