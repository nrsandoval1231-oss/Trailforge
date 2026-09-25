# Scenario DSL

The required root field is `schema_version: procurement-arena-scenario-v1`.
The machine-readable schema is `schemas/procurement-arena-scenario-v1.schema.json`.
Each scenario contains `scenario_id`, `version`, integer `seed`, ordered
timezone-aware `timeline`, `evidence`, and `truth`. Evidence must carry
`event_date`, `document_date`, `verified_available_at`, and `observed_at`.

Load JSON with `ScenarioDsl.loads(text)`. YAML is optional and requires
PyYAML. Use `validate_scenario` before replay. Never put future outcomes or
predictions into evidence; truth is evaluator-only.

Replay currently grants only the exact `PUBLIC` permission scope. `TENANT`,
unknown, blank, and malformed scopes are rejected before policy execution;
matching tenant identifiers do not grant access. Non-public replay requires a
separate governed authorization contract.

Named seeded templates are available through `scenarios.family_scenario`; the
registry contains 40 families and rejects unknown names.
