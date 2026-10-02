# Local generated output

Keep new disposable cohort runs, replay result files, and operator workspace
exports under `.trailforge-experiments/`, `.trailforge-runs/`, `local-output/`,
or `workspace-output/`. These narrow repository-root output folders are ignored
so local runs do not enter source changes by accident.

Legacy files already retained under `.agent/artifacts/`, `research/`, and case
directories remain untouched. Treat those files as retained evidence or inputs
according to their accompanying packet; do not bulk-delete or regenerate them.
