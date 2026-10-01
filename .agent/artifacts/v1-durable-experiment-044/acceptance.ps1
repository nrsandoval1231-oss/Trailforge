$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '../../..')).Path
Set-Location -LiteralPath $root
$evidenceRoot = Join-Path $root ('.firecrawl/slice2-acceptance-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $evidenceRoot | Out-Null
$inputFile = Join-Path $evidenceRoot 'reviewed-input.json'
$bundle = Get-Content -LiteralPath 'scenarios/fixtures/verified/gt-003-morgan-hill.json' -Raw | ConvertFrom-Json
$utf8 = [System.Text.UTF8Encoding]::new($false)
[System.IO.File]::WriteAllText($inputFile, ($bundle.fixtures[0].scenario | ConvertTo-Json -Depth 100), $utf8)
$run1 = Join-Path $evidenceRoot 'run-1'
$run2 = Join-Path $evidenceRoot 'run-2'
$events = [System.Collections.Generic.List[object]]::new()
function Invoke-CheckedCli {
    param([string]$Label, [string[]]$Arguments, [int]$ExpectedExit = 0)
    $lines = & uv run --python 3.11 python -m athena_procurement_arena @Arguments
    $actualExit = $LASTEXITCODE
    $text = $lines -join "`n"
    if ($actualExit -ne $ExpectedExit) { throw "$Label exit $actualExit; expected $ExpectedExit : $text" }
    $payload = $text | ConvertFrom-Json
    if ($ExpectedExit -eq 0 -and $payload.status -ne 'PASS') { throw "$Label did not PASS: $text" }
    if ($ExpectedExit -ne 0 -and $payload.status -ne 'FAIL') { throw "$Label did not FAIL: $text" }
    $events.Add([pscustomobject]@{label=$Label; exit_code=$actualExit; status=$payload.status})
    return $payload
}
$null = Invoke-CheckedCli -Label 'save-reviewed-case' -Arguments @('scenario','--scenario-file',$inputFile,'--experiment-dir',$run1)
$inspected = Invoke-CheckedCli -Label 'fresh-process-inspect' -Arguments @('inspect','--experiment-dir',$run1)
$savedDecisions = Get-Content -LiteralPath (Join-Path $run1 'decisions.json') -Raw
$savedEvaluation = Get-Content -LiteralPath (Join-Path $run1 'evaluation.json') -Raw
if ($savedDecisions -notmatch 'OUT_OF_SCOPE') { throw 'Expected saved GT-003 decision missing' }
if ($savedEvaluation -notmatch 'UNSCORED|UNSEALED') { throw 'Unsealed evaluation status missing' }
$hiddenInput = Join-Path $evidenceRoot 'original-input-unavailable.json'
Move-Item -LiteralPath $inputFile -Destination $hiddenInput
$reopened = Invoke-CheckedCli -Label 'reopen-with-original-input-unavailable' -Arguments @('inspect','--experiment-dir',$run1)
if (($inspected | ConvertTo-Json -Depth 100 -Compress) -ne ($reopened | ConvertTo-Json -Depth 100 -Compress)) { throw 'Reopened persisted inspection changed' }
$null = Invoke-CheckedCli -Label 'replay-with-original-input-unavailable' -Arguments @('replay','--experiment-dir',$run1)
$tampered = Join-Path $evidenceRoot 'tampered-copy'
Copy-Item -LiteralPath $run1 -Destination $tampered -Recurse
$tamperedLedger = Join-Path $tampered 'decisions.json'
[System.IO.File]::AppendAllText($tamperedLedger, ' ', $utf8)
$before = (Get-FileHash -LiteralPath $tamperedLedger -Algorithm SHA256).Hash
$null = Invoke-CheckedCli -Label 'inspect-tampered-copy' -Arguments @('inspect','--experiment-dir',$tampered) -ExpectedExit 1
$null = Invoke-CheckedCli -Label 'replay-tampered-copy' -Arguments @('replay','--experiment-dir',$tampered) -ExpectedExit 1
if ((Get-FileHash -LiteralPath $tamperedLedger -Algorithm SHA256).Hash -ne $before) { throw 'Verification mutated tampered data' }
$null = Invoke-CheckedCli -Label 'untampered-original-still-valid' -Arguments @('inspect','--experiment-dir',$run1)
$null = Invoke-CheckedCli -Label 'repeat-identical-input' -Arguments @('scenario','--scenario-file',$hiddenInput,'--experiment-dir',$run2)
$firstHash = (Get-FileHash -LiteralPath (Join-Path $run1 'decisions.json') -Algorithm SHA256).Hash
$secondHash = (Get-FileHash -LiteralPath (Join-Path $run2 'decisions.json') -Algorithm SHA256).Hash
if ($firstHash -ne $secondHash) { throw 'Substantive decision history did not reproduce' }
$null = Invoke-CheckedCli -Label 'refuse-existing-directory' -Arguments @('scenario','--scenario-file',$hiddenInput,'--experiment-dir',$run1) -ExpectedExit 1
if ((Get-FileHash -LiteralPath (Join-Path $run1 'decisions.json') -Algorithm SHA256).Hash -ne $firstHash) { throw 'Overwrite attempt changed original history' }
$report = [pscustomobject]@{status='PASS'; evidence_root=$evidenceRoot; source_fixture='GT-003 unsealed'; decisions_sha256=$firstHash; checks=$events}
[System.IO.File]::WriteAllText((Join-Path $evidenceRoot 'acceptance.json'), ($report | ConvertTo-Json -Depth 100), $utf8)
$report | ConvertTo-Json -Depth 100
