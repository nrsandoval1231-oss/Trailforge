# Current-publisher timestamp checks

These unmodified Firecrawl response files are diagnostic acquisition evidence, not historical availability proof.

- Chamber current raw HTML declares `datePublished: 2024-06-06T08:43:58+00:00` and `dateModified: 2025-04-30T19:50:26+00:00`. The later mutable page does not prove the exact present text existed in June 2024. Do not backdate the announcement archive on this basis.
- Reuters current metadata declares `article:published_time: 2024-08-28T20:08:10Z` and modified time one second later. `robots` includes `noarchive`; no archive request was made for this page in this recovery slice. The claimed publication time is retained but is not used to turn the existing target's historical availability from UNKNOWN to supported.
- Initial PowerShell CLI call failed before acquisition because its comma-separated format argument was unquoted. Quoted `--format 'markdown,html'` and `--format 'markdown,rawHtml'` completed. An output inspection initially used Windows cp1252 and failed; explicit UTF-8 resolved it without changing source bytes.

Source URLs, scrape IDs, full captured Markdown and HTML/metadata are retained in each response. Original pilot captures remain untouched. These current checks are excluded from the recovered historical replay.
