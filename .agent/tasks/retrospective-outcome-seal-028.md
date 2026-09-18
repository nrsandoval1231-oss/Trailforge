# Retrospective outcome seal 028

## Objective

Create explicit, evidence-bound retrospective outcome seals and a cohort
container for later evaluation.

## Exclusions

No inferred outcomes, automatic negative labels, Athena updates, model
promotion, crawling, outreach, or execution authority.

## Acceptance checks

- Support observed, not-observed-by-cutoff, and inconclusive states.
- Require trace hash, target type, cutoff, exact evidence quote, reviewer statement, reviewer, and timestamp.
- Require a target signal ID only when the target is explicitly observed by cutoff.
- Build a cohort bound to a verified trace-cohort hash with deterministic counts.
- Provide CLI modes, tests, full validation, and diff checks.
