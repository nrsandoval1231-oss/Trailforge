# HC-001 — five-project historical evidence pilot

This is a source-backed convenience cohort, not proof that a signal family predicts rental opportunities. It exercises the existing trace/backtest on eligible evidence and exposes where historical availability is missing. Source-date arithmetic is deliberately separate from validated lead time.

## Fixed experiment

The frozen rule surfaces PROJECT_ANNOUNCED, PERMIT_FILED, PERMIT_APPROVED or CONSTRUCTION_STARTED and compares with a selected POWER_REQUIREMENT milestone. Cases came from prior retained research plus targeted searches, not random sampling. The rule was specified before calculating intervals. These are known power-use cases, so no false-positive rate or precision estimate is defensible. A target means power became obvious in the selected retained source; it does not prove the globally earliest procurement event or a temporary rental requirement.

| Project | Early source date | Comparison source date | Calendar-date difference (diagnostic only) | What is unresolved |
| --- | --- | --- | --- | --- |
| Crusoe Abilene / Lancium campus | 2024-07-18 announcement | 2025-03-18 owner statement of gas backup | 243 days | Archive availability; backup is not temporary rental; portfolio turbine order cannot be assigned to this campus |
| Azure Sky Wind, Throckmorton | 2021-03-03 construction release | Undated Aggreko commissioning case | UNKNOWN | Target publication/event time and availability; no solar-project merge |
| Montauk 2021 transmission support | 2019-12-20 PSEG posted date | 2021-03-11 LIPA determination issue date | 447 days | Actual historical availability and first procurement; mixed contingency scope |
| East Hampton 2018 temporary-generation expansion | 2018-05-17 approval document | Same document explicitly describes 17 MW | 0 days | No advance in captured source dates; neither historical availability nor earliest procurement established |
| xAI Memphis Colossus1 | 2024-06-06 Chamber page (event dateline June 5) | 2024-08-28 Reuters power-use report | 83 days | Original availability; recovered announcement archive is only 2025-01-29, after the power report |

Calendar differences are not elapsed-time guarantees: day precision/time zones, source edits and unavailable archive history remain explicit in the generated report. LIPA dates are document issue dates, not web-publication proof. Zero is a same-document control, not a proved negative forecast. The three positive-looking differences must not enter GridLens rankings or commercial success claims.

## Retained evidence and results

`cohort-input.json` binds 10 signals to exact text and capture hashes, with separately cited source dates. `captures/` retains original acquisition responses and PublicCapture records. `originals/` retains both LIPA PDFs plus SHA-256 manifest. `searches/` retains discovery and archive-query responses, including empty results. `results/` is the deterministic final output; inspect its case-level evidence and eligible replay denominator.

The xAI announcement archive explicitly contains the supported sentence at `20250129032510` UTC. It establishes that content was available **by January 29, 2025**, not that January 29 was the first publication or that the June date was independently verified. No captured target has independently verified historical availability in this pilot. Accordingly validated positive lead-time pairs remain 0 and validated median lead time UNKNOWN; no actual signal failure rate is inferred. The supported early trace can run through existing mechanics while unresolved cases stay in the outer report.

Buyer organizations are identifiable in source material (Crusoe, Enel, PSEG/LIPA, xAI). Procurement authority, a responsible contact and buyer-path availability at a valid early surface are not verified. The report preserves stated organizations separately from temporally supported buyer paths. No owner/contact outreach occurred.

## Important excluded evidence

- GE Vernova's 29-unit Crusoe order covers a portfolio. It does not identify Abilene; it is retained for audit but excluded from that trace.
- Prometheus/Conduit covers multiple Texas sites without a resolved project identity here. Retained as an unresolved discovery result, not counted as two projects.
- SELC's later xAI timeline recounts 2024 events. Event dates cannot backdate the 2026 article's availability; legal allegations remain attributed to the source.
- Earlier Montauk 2017/2020 and East Hampton 2017 generation are distinct periods and do not become early signals for the later scoped packages without source evidence.

## Reproduce

From repository root:

```powershell
uv run --python 3.11 python scripts/run_hc001.py research/hc-001/cohort-input.json .firecrawl/hc001-replay-new
```

Use a new empty output directory. The runner is offline; it validates captures and dates, then calls existing trace/backtest mechanics without changing them. Human-readable report and machine-readable evidence remain local. This does not seal an outcome holdout or authorize promotion.

## Next bounded work

HC-001 availability recovery: obtain contemporary archive/official posting evidence for **both ends of at least three project timelines**, retain original content, then rerun this unchanged policy. Start with Crusoe and Montauk (positive-looking source-date intervals) and the xAI archive-late control. If an archive cannot be recovered, leave the case unresolved and add a separately selected project. Expand toward 20–50 only after this measurement path yields supported pairs. Live ranking and GridLens handoff remain pending.
