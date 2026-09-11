$ErrorActionPreference = "Stop"

python -m pytest -q
python -m compileall -q src
ruff check src tests

Write-Output "Validation passed."
