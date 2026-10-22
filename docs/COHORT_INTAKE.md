# Cohort intake (20-50 historical projects)

Status: 0 reviewed traces. Candidates below are leads from a web search summary, **not** captured,
dated or reviewed. None may enter a cohort, and none counts toward the 20-50 target, until it
passes the checklist.

## Checklist for one case (what `compare-signal-families` needs)
1. Capture each primary source with `capture-public` (URL, retrieval time, content SHA-256).
2. One `ProjectSignal` per dated event: exact source quote, `observed_at` the date the public
   version was available (not a printed date alone), signal type, and a `buyer_path` claim only
   where the source names the owner/EPC/EPCM/GC/electrical contractor.
3. A verified downstream target (e.g. `PROCUREMENT_SIGNAL`) with its own source.
4. A named human `verified_by`, `resolve-traces` identity review, then `build-trace-cohort`.
5. Include projects with no target signal; they stay unresolved, not negative.

## Blockers found 2026-10-22
- No Firecrawl key in this environment, and direct fetches of company sites return 403 through the
  proxy, so primary documents cannot be captured here. Run intake where `capture-public` works.
- Search summaries are not primary sources and carry no availability dates.

## Unverified leads (remote-site power with a possible rent-vs-buy or contract event)
| Lead | What to look for |
| --- | --- |
| MinRes Wodgina (WA), 2018 | Contract Power EPC variation adding 17 MW temporary diesel; earlier signals |
| Gold Fields Agnew (WA), 2019 | EDL 10-year microgrid contract; feasibility/approval signals |
| Rox Resources Youanmi (WA) | Pacific Energy 10-year PPA; study and financing signals |
| Granny Smith (WA) | Aggreko-operated gas/solar/battery microgrid |
| Gruyere (WA) | APA microgrid; construction-approval signals |
| Eramet Centenario-Ratones (Argentina), 2024 | Permanent gas plant; Wartsila O&M agreement (not temporary power) |

Most leads are Australian; the mission's first market is US/remote mining, so add US cases
(Stibnite is already imported but has no downstream milestone yet).
