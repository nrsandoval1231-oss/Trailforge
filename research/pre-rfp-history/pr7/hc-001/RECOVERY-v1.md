# HC-001: recovered archive observations

This version retains the original five projects and fixed signal policy, adds one distinct City of Memphis announcement, and recovers historical content for two complete observation pairs. The initial [input](cohort-input.json), [results](results/report.md), and source captures remain unchanged.

**The evidence supports replay observations, not a measured commercial lead-time advantage.** An archive timestamp establishes that the captured content existed by that time. It does not establish its first publication or the earliest obvious market milestone. Current publisher metadata does not prove that today's text existed at the declared historical date.

| Project | Recovered early policy observation (UTC) | Recovered target observation (UTC) | Result |
| --- | --- | --- | --- |
| Crusoe / Lancium, Abilene | 2024-07-18 15:55:07 | 2025-03-22 19:50:15 | 247.163 days between observed snapshots; market advantage UNKNOWN |
| Montauk 2021 transmission support | 2021-10-18 05:26:13 | 2021-05-07 16:48:02 | Project-page observation is 163.527 days later; late-observation control, not a demonstrated forecast miss |
| xAI Memphis, initial campus | 2024-06-08 21:56:14 | UNKNOWN | Earlier official City evidence recovered; no complete observation pair |
| Azure Sky Wind | UNKNOWN | UNKNOWN | Prior evidence retained; availability unresolved |
| East Hampton 2018 expansion | UNKNOWN | UNKNOWN | Prior same-document evidence retained; availability unresolved |

Three projects now enter the existing replay, two have supported target observations, and one has an observed policy signal before its target. The engine's `coverage: 0.5` and median of 21,354,908 seconds describe this tiny recovered observation set only. They are not forecast accuracy, false-positive rate, population coverage, or validated market lead time. No signal-family promotion follows.

## Evidence recovered

- **Crusoe:** the modern URL hid an earlier official [Lancium announcement alias](https://web.archive.org/web/20240718155507/https://lancium.com/press-release/crusoe-lancium-clean-campus/). Its July 2024 capture describes the initial phase and planned campus expansion. The [March 2025 archive](https://web.archive.org/web/20250322195015/https://lancium.com/press-release/crusoe-expands-ai-data-center-campus-in-abilene-to-1-2-gigawatts/) contains the campus-specific natural-gas backup statement. Initial and expansion phases remain distinguished. Backup generation does not establish temporary rental demand. Crusoe is named at the early observation; procurement authority, customer contact and an actual temporary-power gap remain UNKNOWN.
- **Montauk:** the [project-page snapshot](https://web.archive.org/web/20211018052613/https://www.psegliny.com/reliability/newmontauk) occurs after the [archived power document](https://web.archive.org/web/20210507164802/https://www.lipower.org/wp-content/uploads/2021/03/MTK-2021-Neg-Dec-signed.pdf). The archive PDF is byte-identical to the retained original: SHA-256 `85ffe159589ce0196a7bef719938b94d4e35da1bf601114c6e9d13b7ec3f789a`. Its March 11 issue date and the page's December 2019 displayed date remain diagnostics. The selected scope is 2021 transmission support, not earlier generator deployments.
- **xAI:** the [official City bulletin archive](https://web.archive.org/web/20240608215614/https://content.govdelivery.com/accounts/TNMEMPHIS/bulletins/3a162e2) identifies the Memphis supercomputer and xAI partnership. This is a distinct additional source; it does not backdate the Chamber permalink, whose January 2025 archive remains in the input. The Reuters target remains UNKNOWN. Its current `noarchive` metadata was respected; no Reuters archive request was made in this recovery.

The five-case input is [cohort-input-recovery-v1.json](cohort-input-recovery-v1.json). New immutable captures and full acquisition responses are in [recovery-captures](recovery-captures/); raw archive bodies and sanitized HTTP headers are bound by [the originals manifest](recovery-originals/manifest.json). The archive PDF reuses the byte-identical original file. CDX/availability queries and unsuccessful searches are retained in [recovery-searches](recovery-searches/). Research handoffs retain their original local working paths; these committed directories are the durable evidence copies.

### PDF normalization

The normal Wayback PDF page exposed its toolbar but no document text to Firecrawl, even after a render wait. The corresponding PDF response returned HTTP 200, `application/pdf`, and `Memento-Datetime: Fri, 07 May 2021 16:48:02 GMT`. Downloaded bytes matched the retained original exactly. The [compound witness](recovery-captures/montauk-pdf-archive-witness.capture.json) explicitly combines that returned URL/header receipt, binary hash, and retained Firecrawl text of the identical PDF. It is labelled as normalized compound evidence, not a raw HTML page. The [acquisition record](recovery-captures/montauk-pdf-archive-witness.acquisition.json) preserves the composition. No source timestamp was invented or copied from a document issue date.

## Reproduce

```powershell
uv run --python 3.11 python scripts/run_hc001.py research/hc-001/cohort-input-recovery-v1.json .firecrawl/hc001-recovery-new
```

Use a new empty output directory. The runner is offline. The [generated report](results-recovery-v2/report.md) separates observation intervals from market advantage; [JSON](results-recovery-v2/report.json) retains exact citations and the engine result. `lead_time_seconds` remains a compatibility field for replay observations; `market_lead_time_seconds` is null. Organization availability is separate from UNKNOWN buying chain, procurement authority and contact. Both source boundaries need independent interpretation before any commercial conclusion. The [superseded v1 output](results-recovery-v1/README.md) remains unchanged for review audit; its buyer-path label was rejected and repaired.

## What changed in the research method

Exact modern-permalink queries missed older official aliases. A bounded alias search recovered useful content for Crusoe; a separate official City source improved xAI. This is evidence for checking documented URL variants before declaring a historical case unresolved, not evidence that the signals predict rental demand. Empty results and HTTP errors remain limited attempts, not proof that no earlier record exists.

## Next bounded slice

Select a small set of temporary-power projects with a verifiable conventional milestone, preferably an official solicitation posting or procurement event, and archive-supported earlier project evidence. Retain negative/late and unresolved cases. Audit the event-time meaning before interpreting the interval as market advantage. Expand toward 20–50 only after that path produces defensible commercial measurements; do not tune live ranking from this convenience sample. No outreach, submission, deployment, merge, or GridLens promotion occurred.
