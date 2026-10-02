# HC-001 xAI availability recovery

## Result

Recovered a distinct contemporaneous official source for the early xAI/Memphis announcement. The City of Memphis GovDelivery weekly bulletin, `https://content.govdelivery.com/accounts/TNMEMPHIS/bulletins/3a162e2`, says it was sent **2024-06-07 17:10 CDT** and describes Memphis as the home of the world's largest supercomputer and the City/xAI partnership. The Internet Archive CDX response lists a 200 HTML capture at **2024-06-08 21:56:14 UTC**. The archived body fetched from that exact timestamp reproduces the send-time line and announcement text. This supports that the City bulletin's content existed by the archive capture time. It does not establish the first publication time or prove that the separate Chamber permalink was available then.

The Chamber's selected permalink was queried directly through CDX. Its returned 200 HTML records start at **2025-01-29 03:25:10 UTC**; this is after the selected target's reported August 2024 date. Current Chamber page metadata and displayed June 2024 dates were not used to backdate its content. A wildcard CDX variant returned HTTP 400 and is retained as a failed attempt.

No historical capture was attempted for Reuters: parent-provided current metadata labels it `noarchive`. Two targeted Firecrawl searches for contemporaneous government power-use/permit records (EPA, Tennessee, Shelby County, Memphis) produced no such record in the returned results. That is a limited search outcome, not evidence that no record exists. The August 28 Reuters report's current metadata/dateline does not independently prove historical online availability. Therefore the xAI target's `available_at` remains UNKNOWN and there is no validated temporal pair or lead-time value from this recovery.

## Evidence files

- `.firecrawl/hc-recovery-xai/cdx-chamber-exact.json` — exact selected Chamber permalink CDX response; returned captures begin 2025-01-29.
- `.firecrawl/hc-recovery-xai/cdx-chamber-xai-wildcard.json` — failed wildcard CDX query, HTTP 400.
- `.firecrawl/hc-recovery-xai/city-bulletin-june7.json` — direct current GovDelivery scrape, retained as a source discovery/acquisition response.
- `.firecrawl/hc-recovery-xai/cdx-city-bulletin.json` — CDX response for the City bulletin; record at `20240608215614`.
- `.firecrawl/hc-recovery-xai/city-bulletin-june8-archive.json` — Firecrawl JSON preserving both markdown and raw HTML from the exact Wayback capture. The raw HTML SHA-256 is `c069202d194e8faefa8972707848350d35eb349ca450ff22e55bd3423893d4d5`; the full Firecrawl response SHA-256 is `D465030DAE216951FE5A1BCABBCD7F50CDE615619A3B63BCF887DBAEB2B24CAD`.
- `.firecrawl/hc-recovery-xai/search-chamber-official.json`, `search-memphis-official.json`, `search-official-power.json`, and `search-official-records.json` — retained search results. The City newsletter was discovered in the second search; the two targeted government-record searches did not return a contemporaneous permit/power-use notice.

## Bounded attempts

1. Exact selected Chamber permalink via CDX — successful query, no returned captures before 2025-01-29.
2. Chamber-host wildcard `*xai*` via CDX — HTTP 400; not interpreted as an absence result.
3. Search for official Chamber/City xAI Memphis announcement — found the City bulletin titled “Memphis + xAI = More Innovation”; the page's newsletter index identifies its June 7, 2024 issue.
4. Retrieved the exact City bulletin, queried its CDX history, and fetched the `20240608215614id_` snapshot. The snapshot is the material historical evidence and contains the same City-announced supercomputer/xAI partnership content.
5. Two targeted official-domain searches for xAI Memphis turbine/power/permit records — no contemporaneous government record surfaced. Search was bounded; no Reuters archive query was made.

## Parent integration boundary

This evidence is an alternate official City source for an early `PROJECT_ANNOUNCED` signal. Parent owns whether to add it as a separate signal or use it to replace/augment the Chamber source. Do not set the Chamber source's availability to the City bulletin's timestamp. Even if the City bulletin is used as the early signal, Reuters target availability remains UNKNOWN; leave the case out of validated lead-time pairs.

## Reproduction commands

```powershell
firecrawl scrape 'https://web.archive.org/cdx/search/cdx?url=memphischamber.com/blog/press-release/velocity-meets-potency-xai-announces-memphis-as-new-home/&output=json&filter=statuscode%3A200&fl=timestamp%2Coriginal%2Cstatuscode%2Cmimetype%2Cdigest&collapse=digest' -o .firecrawl/hc-recovery-xai/cdx-chamber-exact.json --format markdown
firecrawl scrape 'https://web.archive.org/cdx/search/cdx?url=content.govdelivery.com/accounts/TNMEMPHIS/bulletins/3a162e2&output=json&filter=statuscode%3A200&fl=timestamp%2Coriginal%2Cstatuscode%2Cmimetype%2Cdigest&collapse=digest' -o .firecrawl/hc-recovery-xai/cdx-city-bulletin.json --format markdown
firecrawl scrape 'https://web.archive.org/web/20240608215614id_/https://content.govdelivery.com/accounts/TNMEMPHIS/bulletins/3a162e2' --format 'markdown,rawHtml' -o .firecrawl/hc-recovery-xai/city-bulletin-june8-archive.json --json
```

No source, policy, input, capture, or result files were changed. No tests or replay were run; this was research-only evidence acquisition.
