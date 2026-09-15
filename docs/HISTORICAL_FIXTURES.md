# Historical fixtures

The built-in replay registry currently contains GT-001 through GT-006. The
checked-in source-fixture examples also include GT-007 and GT-008, but those
files are not automatically part of the replay registry or a scoreable
holdout. Every fixture begins as source evidence that is non-scoreable until an
operator independently establishes the complete timeline and verified
historical availability, then marks the fixture `SEALED_READY`.

Current discoverability is not proof of past availability. Known outcomes must
remain invisible to earlier replay points. Small fixture counts must not be
presented as statistically significant forecasting evidence.

## Prospective shadow capture

`capture_prospective_shadow` records a manually verified source URL/fingerprint,
capture time, frozen prediction manifest, and replay hash without recording an
outcome or granting execution authority. It is a local intake boundary only:
there is no network acquisition, scoring, outreach, bid preparation, or
submission path. A later outcome requires separate governed sealing before it
can affect evaluation.
