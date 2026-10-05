# PR7 reconstruction map

This bounded reconstruction uses PR7 commit `2e18980c70b209ee20fd72df0c489b84815cefd2` as a source reference on the post-PR9 base. The old PR was not merged wholesale.

- Ported the catalog-driven Firecrawl search and selected-page capture CLIs, retained capture/acquisition artifacts, local opportunity import/render workflow, and CLI entrypoints.
- Kept the existing public capture API and added rejection of private/non-public IPs and credential-bearing URLs.
- Repaired freshness qualification, same-deadline citation refresh, requirement promotion/conflict handling, citation/document metadata retention, and workspace URL validation.
- Kept PR9 `historical_cases.py`, its schema, fixed-policy offline runner, and source-bound cases as the only active cohort path. PR7 `historical_cohort.py`, bulk research captures, generated workspaces, and stale strategy/governance edits were excluded.
- The workflow is research and human review only. It does not contact buyers, submit proposals, deploy, or make commercial success claims.

See [the operator workflow](FIRECRAWL_WORKSPACE.md) for runnable local commands and an input example.
