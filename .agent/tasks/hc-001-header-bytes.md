# HC-001 canonical evidence recovery: HTTP headers

The two-attempt byte-packaging budget ended with one distinct uncovered raw evidence family: sanitized HTTP response headers still contain original empty values and terminating blank lines. Source/canonical intent requires preserving raw evidence and hashes; trimming these bytes would contradict the retained manifest. The controller's earlier allowlist omitted raw headers, not a code defect. No third unchanged attempt: revise the bounded scope to include this omitted raw-response family.

One Luna may change only `.gitattributes` by adding `-diff` to exactly `research/hc-001/recovery-originals/*-headers-cookie-omitted.txt`, plus a new `.agent/artifacts/hc-001-availability/HEADER-BYTE-COMPLETION.json`. Keep the existing -text/default whitespace/cr-at-eol rules, code and docs checks, and all evidence bytes unchanged. Do not stage or edit old receipts. No commit/push. No additional agents.

Parent owns final index-byte check, staged whitespace check, full gate and Sol independent review. The final review must assess these scoped raw-evidence attributes explicitly. This correction cannot alter product requirements, relax source-code validation or certify completion. Failure cause and original output are retained as a separate receipt.
