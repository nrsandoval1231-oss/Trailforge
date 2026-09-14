$ErrorActionPreference = "Stop"

# Delegates to the cross-platform gate so Windows, Linux, and CI stay identical.
python (Join-Path $PSScriptRoot "validate.py")
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
