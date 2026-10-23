# Bounded availability recovery attempts

Scope was limited to the Crusoe Abilene/Lancium and Montauk 2021 sources in the accepted HC-001 packet. The raw CDX responses, Wayback availability responses, Firecrawl outputs, replay bodies, and replay headers are retained in `.firecrawl/hc-recovery-builder/`.

The first approach queried CDX for the cohort's exact URLs. The exact Lancium announcement path had captures only from June 2025 onward in the retained filtered response; the exact Crusoe expansion URL returned only the CDX header because the archived official page used a different URL path. Exact Montauk queries intermittently returned HTTP 503; those attempts were not treated as absence evidence. The later retained exact Montauk queries and variant searches returned records.

The second approach used bounded Lancium/Crusoe URL-prefix variants, exact Montauk URL variants, the Wayback availability endpoint near each displayed source date, and direct timestamped replay verification. It recovered an official Lancium announcement alias dated July 18, 2024, a campus-specific Lancium expansion page captured March 22, 2025, PSEG's Montauk page captured October 18, 2021, and the LIPA PDF captured May 7, 2021. Every selected replay was verified with HTTP status, content type, Memento-Datetime, and retained body hash. The PDF response bytes exactly match the previously retained original.

The page's publisher dates remain source metadata. Memento-Datetime establishes that the content existed by the archive timestamp and does not establish its first publication. The PSEG capture postdates the LIPA PDF capture despite the page's displayed December 20, 2019 posted date. No snapshot difference is interpreted as a validated lead time. Crusoe's target says backup natural-gas turbines; it does not establish temporary rental procurement.

## Limited unsuccessful attempts

- Initial filtered CDX requests for the PSEG page and LIPA PDF returned HTTP 503. Their request timestamps were not captured in that initial shell output and remain `UNKNOWN`; later CDX responses and timestamped replay verification recovered usable records.
- The cohort's exact Crusoe current expansion URL returned an empty CDX record set. A domain-prefix query found the owner page under its archived `/blog/` path, while Lancium's official release alias provided the selected target excerpt at the March 22 snapshot.
- Wayback availability near the PSEG displayed date resolved to an October 18, 2021 capture. This is a closest-capture result, not proof that no earlier copy exists.
- Firecrawl's normal PDF scrape surfaced Wayback toolbar text, so the PDF content was verified from the archived PDF bytes and the existing PDF's retained hash. Both normal and `id_` raw PDF replay responses return the same bytes and Memento-Datetime. No text was synthesized from the toolbar.

The earlier retained `.firecrawl/hc-archive-crusoe.md` and `hc-archive-montauk.md` contain empty CDX results and were left untouched.
