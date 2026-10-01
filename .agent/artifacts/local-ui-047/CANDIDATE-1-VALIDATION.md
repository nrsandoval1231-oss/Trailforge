# Candidate 1 controller evidence — not accepted

2026-10-01. Base3cedc8711ceec0ac411f04911fa24186a0d6ceb1; builder hashes retained in COMPLETION.json.

- Full gate `uv run --python 3.11 --with pytest --with ruff python scripts/validate.py`: exit1, 1 failed / 288 passed / 1 skipped in53.78s. Failure `test_request_guards[headers10-400]`, Transfer-Encoding chunked: http.client.getresponse raised Windows ConnectionAbortedError10053 instead of received expected400. Remaining gates not reached. Do not treat this as a pass.
- Controller runtime_probe.py source candidate: exit0, six lifecycle/boundary checks PASS, evidence `.firecrawl/ui047-source-runtime`; real repeat/restart/source-unavailable/corruption checks.
- `uv build --wheel --out-dir .firecrawl/ui047-wheel`: exit0, includes index.html/app.js/style.css.
- Isolated installed wheel from C:/Windows/System32, runtime_probe.py: exit0, six checks PASS, `.firecrawl/ui047-wheel-runtime`.
- Initial browser run at127.0.0.1:8765: saved run2bb80b6d83ad4e8c827e7a4db986d01c, integrityPASS, replayNOT_RUN, correct GT003 OUT_OF_SCOPE_MAINTENANCE_ONLY and IGNORE, visible evidence times, source/reviewer context, UNSEALED/UNSCORED. Browser proof is interim, not final candidate acceptance.

Direction: CORRECT request rejection/test transport reliability without weakening protocol assertions. Preserve this attempt and re-run gates on repaired candidate.
