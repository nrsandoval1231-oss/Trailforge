# Project identity review 025

## Objective

Create a reviewer-controlled, evidence-bound boundary for joining project
signals under one canonical project identity.

## Exclusions

No automatic entity resolution, fuzzy matching, web crawling, outcome
inference, Athena optimization, outreach, or promotion authority.

## Acceptance checks

- Require an explicit canonical ID, member IDs, evidence provenance, exact quote, rationale, reviewer, and timestamp.
- Merge only non-conflicting reviewed identities and retain the review hash in resolved signal claims.
- Fail closed on conflicting reviews and missing public source provenance.
- Provide a deterministic CLI and tests.
