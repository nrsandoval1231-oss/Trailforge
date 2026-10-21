# Stibnite mining import

A real, public-source import of Perpetua Resources' Stibnite Gold Project (Idaho), built from the
2026-10-16 [mining power screen](../../../../research/mining-power-screen-2026-10-16.md).

- `*.json` captures: six public pages captured 2026-10-21 with Firecrawl (owner update, ATCO award, Hatch EPCM, Idaho Power contract, local notices, vendor intake). Each one keeps whole source
  paragraphs verbatim, with PDF line breaks joined, and drops site navigation and boilerplate. Rebuild
  them with `build_captures.py`.
- `project.json`: three phase-specific requirements. Each claim is tied to an exact quote.
  - **Camp power during construction** (`HYPOTHESIS`): load, timing, fuel, package owner and award
    status are all unknown. Site access is evidenced: remote site, pilot-vehicle-only traffic since
    Sept 1, 2026, and ongoing large-load deliveries. This matters for fuel logistics.
  - **Idaho Power powerline materials** (`AWARDED`): kept separate so it is never pitched as open.
  - **Operations grid supply** (`OBSERVED`): permanent power is planned from the upgraded grid line.
- **Review pending.** `reviewed_by` stays marked pending until the operator checks each quote. No MW,
  date, buyer authority or award status beyond the quotes has been added.
- **Buyer entry route:** Perpetua's public vendor-intake form lists Electrical Equipment suppliers. It is
  kept as a source only, because registering does not establish qualification or access to a live bid.
