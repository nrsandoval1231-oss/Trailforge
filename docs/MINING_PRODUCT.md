# TrailForge mining opportunity application

The root of `trailforge-ui` is the supplier-centric mining product. Its four views are Dashboard, Mining Opportunity Explorer, Supplier Matching and Project Intelligence. The previous deterministic research instrument is preserved at `/workbench`; original report URLs remain supported.

```sh
PYTHONPATH=src python -m athena_procurement_arena.local_ui --saved-only \
  --mining-input PATH_TO_REVIEWED_MANIFEST
```

Repeat `--mining-input` for more projects. `--mining-supplier PATH` loads the existing reusable supplier offering contract. Input editing remains the existing reviewed import workflow, not an unreviewed form that silently promotes facts. Restart after changing manifests. The loopback Host/Origin guard, mutation token and execution boundary are unchanged.

The read-only `/api/mining` returns each imported project, its retained claims/captures and one existing-engine qualification/match per requirement. The UI does not create a second qualification algorithm. Phase demand is never summed. Claims distinguish observed, verified, estimated, conflicting and unknown values; estimates include methods/ranges, conflicts retain alternatives, and evidence keeps publication/capture/observation/availability/event clocks and hashes. Dependency hypotheses retain falsifiers. Supplier screening is not engineering approval.

## Five-project evaluation corpus

`ui_assets/assessments.json` faithfully carries the table and source links from `research/mining-power-screen-2026-10-16.md`: Stibnite, Hermosa, Rhyolite Ridge, Thacker Pass and Eskay Creek. It is explicitly **secondary research**, dated October 16, not refreshed live data. No verified open power package was established by that screen.

The original eight requirement imports and retained captures described by the note were not recoverable in the repository or accessible artifacts. They are not reconstructed or invented. Consequently these five summaries have no engine match score, no recreated phase kW and no claim of retained primary evidence. Load the original authorized manifests to inspect their true phase requirements. The bundled synthetic fixture is optional and visibly labeled at project and source level; it exercises the real engine without masquerading as a sixth commercial lead.

## Interactive snapshot

```sh
PYTHONPATH=src python scripts/build_mining_preview.py --output /tmp/trailforge-demo \
  --mining-input scenarios/fixtures/mining/project.json
cd /tmp/trailforge-demo
python -m http.server 4173
```

This exports the actual UI, frozen engine results, evidence JSON and existing printable reports. It is a read-only snapshot, not a deployed Python backend or refreshed research service. No extra runtime service or production dependency is introduced.

## Visual authority

The October 16 approved Industrial Intelligence Board governs the product UI: Obsidian `#171E1B`, Forest `#34483C`, Brass `#D7B77B`, Limestone `#F4F0E7`, Copper `#A76C4A`, Inter. The existing October 3 Jade brand kit is retained as historical locked evidence and was not rewritten.

The mountain artwork is generated decorative imagery, not an image of an assessed project. The transparent mountain mark is a raster derivative generated from the approved board, not a new owner-approved vector master. Replace with an exact standalone master if one becomes available. Neither decorative asset is research evidence. Inter is redistributed unmodified from rsms/inter, font blob `5a8d3e72ad7ffb62af3b146e1b1f54ab5813a212`, under the bundled SIL Open Font License.

No geocoded map or fabricated match percentages, revenue, MW totals, market coverage, fleet commitment or live freshness are shown. Navigation, search, filters, requirement/project selection, source disclosures and JSON export work with the actual available contracts.

## Validation

Run `python scripts/validate.py` for the full Python, compilation, lint and fixture gate, and `node --test tests/ui/mining-product-model.test.cjs` for the UI selection regressions. The latter prove that procurement, phase and supplier filters bind to the same requirement, deep links normalize phase indices, and optional claim methods without ranges remain renderable. No Node package is needed by these tests or the production application.
