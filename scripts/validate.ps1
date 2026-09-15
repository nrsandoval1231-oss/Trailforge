$ErrorActionPreference = "Stop"

$uv = Get-Command uv -ErrorAction Stop
& $uv.Source run --python 3.11 --with pytest --with ruff python -m pytest -q
if ($LASTEXITCODE -ne 0) {
    throw "pytest failed with exit code $LASTEXITCODE"
}

& $uv.Source run --python 3.11 --with pytest --with ruff python -m compileall -q src
if ($LASTEXITCODE -ne 0) {
    throw "compileall failed with exit code $LASTEXITCODE"
}

& $uv.Source run --python 3.11 --with pytest --with ruff python -m ruff check src tests
if ($LASTEXITCODE -ne 0) {
    throw "ruff failed with exit code $LASTEXITCODE"
}

Get-ChildItem scenarios\fixtures\verified -Filter *.json | ForEach-Object {
    & $uv.Source run --python 3.11 --with pytest --with ruff python -m athena_procurement_arena validate-bundle --bundle $_.FullName
    if ($LASTEXITCODE -ne 0) {
        throw "fixture validation failed for $($_.FullName) with exit code $LASTEXITCODE"
    }
}

Write-Output "Validation passed."
