# Real public-web vertical slice — 2026-10-01

This retained run exercises Firecrawl acquisition through TrailForge's new adapter, followed by transparent manual exact-span extraction, identity, strict rental-fit screening and local response preparation. It is not an automated extractor or proof of predictive signal quality.

## Operator outputs

Open `operator/index.html` after recreating the workspace with the commands below. The shipped snapshot is time-bound; rerender to recompute status and recapture sources before a real pursuit.

### Early project: Plaza 500 South (Phase 1), Fairfax County, Virginia

- Public building record **BLDC-2026-00118**, submitted July 16, 2026, says **New Data Center Core/Shell (Phase 1)**, **In Review**, at **6299 Edsall Road**. It says the contractor will be selected later.
- County parcel record names **PLAZA 500 PROPERTY OWNER LP** at 6295 Edsall Road; this is the parent parcel address, not a reason to change the building address. The permit includes address-correction comments. Site plan revision SP-2024-00003-1 is listed May 21, 2026.
- Dominion's Edsall project describes a substation supporting new data-center development, with **Q2 2028 energization**. The September 24 county agenda moves Edsall application **2232-2025-MA-00007** to **December 2, 2026**. A retained local news report links the utility project to Plaza 500/Starwood; the substation remains a related project, not a deduplicated building record.
- Hypothesis: construction or commissioning might precede permanent power. **No temporary MW, actual energization gap, fuel requirement, budget, procurement authority or named buyer contact is verified.**
- Next action: identify the owner's project-power decision maker, confirm project viability/construction timing and permanent-service commitment, then verify load/duration/fuel. Planning opposition is a material risk.
- No temporary-power RFP for this project was found in the retained scoped search. Existence of a private or undiscovered RFP remains UNKNOWN. May 21 is only the earliest project signal in this limited capture set; it is not proven earliest availability or lead-time advantage.

Primary sources: [county permit](https://plus.fairfaxcounty.gov/CitizenAccess/Cap/CapDetail.aspx?Module=Building&TabName=Building&capID1=REC26&capID2=00000&capID3=01M8T&agencyCode=FFX&IsToShowInspection=), [county parcel](https://www.fairfaxcounty.gov/gisapps/ParcelInfoReportJade/ParcelInfoReport.aspx?ParcelID=0812010007), [Dominion Edsall](https://www.dominionenergy.com/about/delivering-energy/electric-projects/power-line-projects/edsall), [county agenda](https://www.fairfaxcounty.gov/planningcommission/sites/planningcommission/files/Assets/calendar/2026/9.24.26.pdf).

### Active solicitation: LIPA 2026 Temporary Generation RFP, PowerAdvocate 238662

[PSEG's official landing page](https://www.psegliny.com/aboutpseglongisland/proposalsandbids/2026tempgenrfp) and the public original RFP are captured, along with the referenced public transmission-interconnection requirements.

| Requirement | Captured result |
| --- | --- |
| Buyer | LIPA; administered by PSEG Long Island |
| Proposal deadline | October 30, 2026, 5:00 p.m. Eastern Prevailing Time (21:00 UTC) |
| Intent / questions | Intent October 16 at 5 p.m. EPT; question window through October 16 |
| Capacity | **5 MW minimum per project**; **up to 400 MW aggregate**, not one site's requirement |
| Service | Start May 1, 2028–May 1, 2030; 3-year base; optional extension through October 31, 2039 |
| Contract | PPA with site control, development/interconnection, operations and removal obligations |
| Voltage | Distribution at 13 kV or transmission at 23 kV and above |
| Duty | Dispatchable capacity and hourly energy as scheduled |
| Fuel | Natural-gas infrastructure addressed; fuel supply options permitted; project-specific selection UNKNOWN |
| Emissions | Project environmental description and pollutant metrics required; permits/project-specific limits unresolved |
| Insurance | Appendix E: employer $1M; auto $5M; CGL $10M; applicable pollution/professional $5M and builders risk terms |
| Security | Section 5.3.13.4: seller security 30% of Notional Value; not a stated bid bond |
| Forms | Procurement certifications, respondent Excel workbook, PPA and applicable vendor/ISNETworld requirements; originals on portal not captured |
| Submission | PowerAdvocate; human only |
| Runtime / generation redundancy / bid bond | UNKNOWN from this extraction; do not substitute relay exceptions for generator redundancy |

**Qualification: NOT FIT under the retained direct-rental screen (`PERMANENT_CAPACITY_OR_PPA_SCOPE`).** The screen does not decide whether a developer partnership could use 2G equipment. That is a human commercial/technical go/no-go question, not a qualification claim. The workspace includes a 22-section response outline matching RFP section 5.2.2, internal draft text, missing requirements and source citations; it is not bid-ready.

Active status means the deadline in the freshly requested public source is future as of capture. Firecrawl's provider cache timestamps were absent and remain UNKNOWN; the max-age-zero request and local completion are retained. Portal amendments, private forms and site data were not accessed. A human must verify current portal terms before pursuing.

## Acquisition and files

- `config/discovery.catalog.json`: broad configurable families and optional official-domain searches.
- `searches/`, `searches-broad/`: real runs through `trailforge-discovery`; initial official-domain query then unrestricted broad runs.
- `discovery-raw/`: 13 preliminary Firecrawl searches, retained exactly, including negative/rejected/stale leads. Broad phrases included temporary power, generator rental, temporary generation RFP, data-center construction/utility/substation, and targeted Plaza/official-source followups. Closed rentals and unrelated results were not promoted.
- `captures/`: immutable PublicCapture JSON and raw Firecrawl sidecars with URL, source type, query, metadata, retrieval time and hashes.
- `originals/`: three original public PDFs plus digest manifest. Original-byte hashes differ from parsed-content hashes by design.
- `inputs/lipa-2026-tempgen-v3.json` and `inputs/plaza500-south-v2.json`: final manual source-cited extraction inputs. Earlier inputs/captures are retained; v2 binds the final Windows-safe acquisition path and fresh RFP landing page.
- `operator/`: final inspectable local snapshot with preserved captures/documents and editable drafts.

## Reproduce offline

From repository root, use a NEW destination, never overwrite source captures:

```powershell
uv run --python 3.11 trailforge-opportunity import --workspace .trailforge-operator --input research/firecrawl-2026-10-01/inputs/lipa-2026-tempgen-v3.json
uv run --python 3.11 trailforge-opportunity import --workspace .trailforge-operator --input research/firecrawl-2026-10-01/inputs/plaza500-south-v2.json
uv run --python 3.11 trailforge-opportunity render --workspace .trailforge-operator --output .trailforge-operator/index.html
```

Copy the shipped `operator/drafts/lipa-tempgen-2026.json` into the new workspace's drafts folder to reuse the editable internal draft, then rerender. It is separate from immutable source facts. Re-import after new source capture into a new workspace when freshness expires. See `docs/FIRECRAWL_WORKSPACE.md` for live commands.

## Gaps and next slice

Initial extraction is manual, not general NLP/OCR automation. No qualified direct-rental bid or verified early-project power requirement is claimed. No RFP forms were submitted, no buyer contacted, no portal controls bypassed. No historical lead-time result or validated ranking is produced here.

Next: **HC-001** — run a small real historical cohort through existing trace/replay mechanics, retain dated availability and comparison-milestone evidence, report unresolved cases and buyer-path availability, then expand toward 20–50. Live ranking and GridLens handoff follow repeated signal evidence.

Review correction: LIPA input v3 extends the fuel citation through section 2.3.1, supporting both fuel-supply options. v1/v2 inputs remain historical extraction attempts, not the final operator facts.
