# xAI archive handoff addendum

Use the **normal Wayback replay** as the canonical archive content:

- Original current source URL: `https://memphischamber.com/blog/press-release/velocity-meets-potency-xai-announces-memphis-as-new-home/`.
- Current Chamber scrape was parent-retained at `.firecrawl/hc-recovery-parent/xai-chamber-raw.json`; Firecrawl scrape ID `01a0fa2f-1818-73eb-a974-97acabbe36e0`, status 200. Its local file write/retrieval record is `2026-10-02T01:16:27.4078770Z` (Windows file timestamp; Firecrawl metadata itself does not expose a retrieval timestamp).
- Current HTML has JSON-LD `datePublished=2024-06-06T08:43:58+00:00` and `dateModified=2025-04-30T19:50:26+00:00`, plus `<meta property="article:modified_time" content="2025-04-30T19:50:26+00:00">`. Firecrawl parsed `modifiedTime=04/30/2025 14:50:26` in metadata with `timezone=America/New_York`. These are current mutable-page metadata, not historical capture proof.
- Chamber exact-permalink CDX response is `.firecrawl/hc-recovery-xai/cdx-chamber-exact.json`; returned capture rows begin `20250129032510` (the existing archive-late control).
- City bulletin CDX response is `.firecrawl/hc-recovery-xai/cdx-city-bulletin.json`. It has `["20240608215614","https://content.govdelivery.com/accounts/TNMEMPHIS/bulletins/3a162e2","200","text/html","6YWUY7M5WZQ6UPCMS65QVG5ACEJDM66I"]`.
- Canonical replay URL: `https://web.archive.org/web/20240608215614/https://content.govdelivery.com/accounts/TNMEMPHIS/bulletins/3a162e2`.
- Normal toolbar-plus-body response: `.firecrawl/hc-recovery-xai/city-bulletin-june8-wayback-normal.json`, Firecrawl scrape ID `01a0fa3a-74c6-77c8-a6e1-c3045ffa2d7e`, status 200; request interval recorded as `2026-10-02T01:28:50.3545853Z` to `2026-10-02T01:28:53.9891959Z`. Its HTML SHA-256 is `de100e7e53ae8d9772abb7e9528f75dcd918988ecaea9d017653d8cb180d85c4`; full response SHA-256 is `0DB6AD43164616F15CBA18A0CECF3D1AB2246CCD0CE501F04E75DD8C0E3F3993`. The retained `id_` response remains at `city-bulletin-june8-archive.json`.

Exact retained body excerpts:

> Memphis sent this bulletin at 06/07/2024 05:10 PM CDT

> Unless you have been totally off the grid, you probably know that this was a big week for Memphis. We announced that our city will be the home of the world's largest supercomputer, or as Elon Musk likes to call it, the Gigafactory of Compute.

> I am confident that the partnership between the city of Memphis and xAI will produce great things.

The standard Wayback response includes its toolbar/timeline `08 Jun 2024 - 17 Jan 2026`, and the selected 14-digit capture timestamp appears in the canonical replay URL and raw HTML. The bulletin says it was sent June 7; the archive capture conservatively supports content existence by `2024-06-08T21:56:14Z`. It is a distinct City source and does not date the Chamber page. Reuters remains unprobed due parent-provided noarchive metadata; the selected target stays UNKNOWN.
