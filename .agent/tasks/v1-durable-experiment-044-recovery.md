# Bounded integration recovery after two Luna repairs

Controller direction: CORRECT using optional Terra specialist, one pass, then independent Sol. This is not a third unchanged Luna retry or new product work.

Evidence and return to intent: owner requires complete ordered actual decisions inspectable after restart; docs/PRD_ALIGNMENT.md retains deterministic research-only Arena and no expansion. TemporalWorld sorts visible_evidence_ids but preserves scenario order in visible_evidence. Both are existing valid contracts. The second repair wrongly equates these orders; actual saved inputs must not be sorted/reconstructed to appease a verifier. Controller `uv run --python 3.11 python .agent/artifacts/v1-durable-experiment-044/ordering_probe.py` returned exit 1 ValueError on a legitimate two-evidence z,a scenario. Candidate runner SHA256 BCDEE754B9B6D4EA3E038F4CD1038FFD1F20E6B8006EC1CD7D59BF891B836F59; all prior claims/evidence preserved.

Small alternative: identity-aware verification of the existing snapshot representation, with explicit timeline completeness. No engine redesign, no framework. Terra selected only after Luna repair budget exhausted for this integration mismatch.

Allowed edits only src/athena_procurement_arena/runner.py and tests/procurement_arena/test_experiment.py (plus new SPECIALIST-COMPLETION.json). Base/branch same parent. No prior artifacts, docs, graph, policy, world changes, commits/push/merge/deploy or Slice3.

Requirements:
1. Fix ordering mismatch by validating all visible snapshot entries are objects with unique IDs, matching ledger IDs without imposing the ledger's sorted order on the actual captured evidence sequence. Also check actual snapshot evidence sequence matches the engine's scenario order, not a regenerated explanation. Preserve stored snapshots exactly. Add regression with two visible items z,a; create, inspect and replay PASS while saved order remains z,a and ledger IDs a,z.
2. Finish parent-required ordered timeline check: ledger record count/timestamps equal scenario.timeline exactly before snapshot checks. Reject truncated/reordered/missing decisions even when hash chain and artifact hashes have been consistently recalculated. Valid duplicate timestamps if permitted by existing scenario semantics should not be newly prohibited.
3. Every malformed visible snapshot element must raise ValueError, not AttributeError; test null mixed into visible evidence with recalculated hashes. CLI must provide structured FAIL.
4. Source ownership check covers both package __init__ paths (athena_procurement_arena and athena_arena) before Git attribution, still whole-tree dirty. Do not broaden source provenance further. Existing wheel/editable version/digest logic retained.

Read parent, owner brief, REVIEW-2, actual runner/world and focused tests; do not read builder reasoning. Use apply_patch. Reproduce first, focused tests+Ruff before full final frozen validate.py once. Controller performs real fresh-process/wheel acceptance and independent Sol review. Store actual UTC start/finish, exact six implementation hashes, failed and passed commands, model/config/tokens UNKNOWN where unmeasured in SPECIALIST-COMPLETION.json. Do not self certify. On unresolved failure, hand back evidence; do not silently widen scope.
