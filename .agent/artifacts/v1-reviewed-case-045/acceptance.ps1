$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '../../..')).Path
Set-Location -LiteralPath $root
$evidenceRoot = Join-Path $root ('.firecrawl/slice3a-acceptance-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $evidenceRoot | Out-Null
$bundleFile = Join-Path $evidenceRoot 'reviewed-bundle.json'
Copy-Item -LiteralPath 'scenarios/fixtures/verified/gt-003-morgan-hill.json' -Destination $bundleFile
$run1 = Join-Path $evidenceRoot 'run-1'
$run2 = Join-Path $evidenceRoot 'run-2'
$events = [System.Collections.Generic.List[object]]::new()
function Invoke-CheckedCli {
    param([string]$Label, [string[]]$Arguments, [int]$ExpectedExit = 0)
    $lines = & uv run --python 3.11 trailforge @Arguments
    $actualExit = $LASTEXITCODE
    $text = $lines -join "`n"
    if ($actualExit -ne $ExpectedExit) { throw "$Label exit $actualExit; expected $ExpectedExit : $text" }
    $payload = $text | ConvertFrom-Json
    if ($ExpectedExit -eq 0 -and $payload.status -ne 'PASS') { throw "$Label did not PASS: $text" }
    if ($ExpectedExit -ne 0 -and $payload.status -ne 'FAIL') { throw "$Label did not FAIL: $text" }
    $events.Add([pscustomobject]@{label=$Label; exit_code=$actualExit; status=$payload.status})
    return $payload
}
$null = Invoke-CheckedCli -Label 'save-direct-reviewed-fixture' -Arguments @('scenario','--bundle',$bundleFile,'--fixture-id','GT-003','--experiment-dir',$run1)
$first = Invoke-CheckedCli -Label 'fresh-process-inspect' -Arguments @('inspect','--experiment-dir',$run1)
if (($first | ConvertTo-Json -Depth 100) -notmatch 'source-review-2026-09-08') { throw 'Retained reviewer context missing' }
if ($first.evaluation.status -ne 'UNSEALED' -or $first.evaluation.scoring -ne 'UNSCORED') { throw 'Unsealed boundary changed' }
$movedBundle = Join-Path $evidenceRoot 'original-bundle-unavailable.json'
Move-Item -LiteralPath $bundleFile -Destination $movedBundle
$reopened = Invoke-CheckedCli -Label 'inspect-original-bundle-unavailable' -Arguments @('inspect','--experiment-dir',$run1)
if (($first | ConvertTo-Json -Depth 100 -Compress) -ne ($reopened | ConvertTo-Json -Depth 100 -Compress)) { throw 'Retained inspection changed' }
$null = Invoke-CheckedCli -Label 'replay-original-bundle-unavailable' -Arguments @('replay','--experiment-dir',$run1)
$probeOutput = & uv run --python 3.11 python .agent/artifacts/v1-durable-experiment-044/no_execution_inspect_probe.py $run1
if ($LASTEXITCODE -ne 0) { throw 'Execution-disabled inspect failed' }
$events.Add([pscustomobject]@{label='execution-disabled-inspect'; exit_code=0; status='PASS'})
$null = Invoke-CheckedCli -Label 'repeat-identical-fixture' -Arguments @('scenario','--bundle',$movedBundle,'--fixture-id','GT-003','--experiment-dir',$run2)
$firstHash = (Get-FileHash -LiteralPath (Join-Path $run1 'decisions.json')).Hash
if ($firstHash -ne (Get-FileHash -LiteralPath (Join-Path $run2 'decisions.json')).Hash) { throw 'Decision history did not reproduce' }
$null = Invoke-CheckedCli -Label 'unknown-fixture-id' -Arguments @('scenario','--bundle',$movedBundle,'--fixture-id','DOES-NOT-EXIST','--experiment-dir',(Join-Path $evidenceRoot 'invalid')) -ExpectedExit 1
if (Test-Path -LiteralPath (Join-Path $evidenceRoot 'invalid')) { throw 'Invalid selection created output directory' }
$tampered = Join-Path $evidenceRoot 'tampered-copy'
Copy-Item -LiteralPath $run1 -Destination $tampered -Recurse
$inputPath = Join-Path $tampered 'input.json'
[System.IO.File]::AppendAllText($inputPath, ' ', [System.Text.UTF8Encoding]::new($false))
$tamperedHash = (Get-FileHash -LiteralPath $inputPath).Hash
$null = Invoke-CheckedCli -Label 'tampered-fixture-input' -Arguments @('inspect','--experiment-dir',$tampered) -ExpectedExit 1
if ((Get-FileHash -LiteralPath $inputPath).Hash -ne $tamperedHash) { throw 'Inspection changed tampered input' }
$null = Invoke-CheckedCli -Label 'existing-directory-refused' -Arguments @('scenario','--bundle',$movedBundle,'--fixture-id','GT-003','--experiment-dir',$run1) -ExpectedExit 1
if ((Get-FileHash -LiteralPath (Join-Path $run1 'decisions.json')).Hash -ne $firstHash) { throw 'Overwrite attempt changed original' }
$report = [pscustomobject]@{status='PASS'; evidence_root=$evidenceRoot; fixture='GT-003 unchanged negative mechanics case'; decisions_sha256=$firstHash; checks=$events}
[System.IO.File]::WriteAllText((Join-Path $evidenceRoot 'acceptance.json'), ($report | ConvertTo-Json -Depth 100), [System.Text.UTF8Encoding]::new($false))
$report | ConvertTo-Json -Depth 100
