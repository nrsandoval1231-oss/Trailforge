# Discovery

Discovery finds candidate listings. It does not qualify them.

```
sources  ->  fetch  ->  parse  ->  triage  ->  REVIEW QUEUE  ->  human  ->  capture  ->  screen  ->  shortlist
                                              (AWAITING_REVIEW)         (VERIFIED)
```

Everything left of the human is a proposal. Nothing in `discovery/` can mark a
record `VERIFIED`, and a `ReviewCandidate` can never reach the shortlist. The
`capture` path — which requires a named reviewer, verification notes, and the
retrieved source text — remains the only route into verified evidence. That
boundary is structural, not advisory: `ReviewCandidate` has no verifier field to
set, and `candidate_to_capture_request` raises without one.

## Why config-driven

Broad multi-source scraping fails in practice when every site needs its own
parser module. Here a site is a `SourceConfig` entry: a URL, a `row` selector,
and a selector per field. Adding a jurisdiction is a JSON file, not code, so
breadth does not multiply the code to maintain. When a site changes its markup,
the fix is a selector, and only that source breaks — one failing source never
fails the sweep.

## Adding a site

1. Save the listing page: `curl -sL https://city.gov/bids > /tmp/city.html`
2. Write a config in `src/athena_procurement_arena/discovery/configs/`, starting
   from `example-html.json`.
3. Validate the selectors offline, with no network and no rate limiting:

   ```
   python -m athena_procurement_arena discover \
     --source my-city --dry-run /tmp/city.html
   ```

   Iterate until the rows and fields come out right.
4. Set `"enabled": true` and run the live sweep.

**A shipped config stays `"enabled": false` until its selectors have been
verified against a live response.** Both configs in this repo ship disabled for
exactly that reason — they were written from documented shapes, not from a
verified live call.

### Selector forms

| Kind | `row` | Fields |
| --- | --- | --- |
| `html_list` | CSS selector for each record | CSS selector; `sel@attr` reads an attribute |
| `json_api` | dotted path to the array | dotted path within a record |

A selector matching nothing yields an empty field. It never guesses, and the
downstream screen reports missing evidence rather than a qualification.

## Retrieval conduct

Scraping public procurement sites is a durable relationship with the agencies
publishing them. The fetcher:

- honors `robots.txt` (override per-run with `--ignore-robots`, only for sources
  you are authorized to retrieve)
- rate limits per host (`rate_limit_seconds`, default 2s, set higher for small
  municipal sites)
- sends an identifying User-Agent
- refuses non-HTTPS URLs and caps response size
- writes every response body unmodified to `--cache-dir`

That cached file is what `capture --excerpt` fingerprints, so the SHA-256 on a
verified record is the digest of bytes actually retrieved — the provenance chain
runs unbroken from retrieval to shortlist.

## Federal codes worth targeting

For SAM.gov (`ncode` for NAICS, `ccode` for PSC). Run these as separate configs
rather than one broad query:

| Code | Meaning |
| --- | --- |
| NAICS 532412 | Construction/mining heavy equipment rental — generator rental |
| NAICS 532490 | Other commercial equipment rental |
| NAICS 237130 | Power and communication line construction |
| NAICS 221118 | Other electric power generation |
| NAICS 238210 | Electrical contractors |
| PSC 6115 | Generators and generator sets |
| PSC W061 | Lease/rental of generators |
| PSC Z2xx | Construction of structures and facilities |

SAM.gov requires a free api.data.gov key in `SAM_API_KEY`. The API shape in
`federal.json` follows the documented v2 response; verify it against a live call
before enabling.

## Triage is not qualification

`triage_score` is a keyword heuristic that orders reviewer attention so the most
promising rows are read first. A `HIGH` band is not a qualification and a zero
score is not a rejection — it only decides reading order. Terms live in
`discovery/triage.py` and are weighted toward planned, schedule-driven power
(temporary generation, commissioning, bridge power, energization, interconnection
delay) and against maintenance and standby work.

## Commands

```
python -m athena_procurement_arena sources --all      # list configs
python -m athena_procurement_arena discover --source <id> --dry-run <file>
python -m athena_procurement_arena discover --min-score 4 --limit 25 --out queue.json
```
