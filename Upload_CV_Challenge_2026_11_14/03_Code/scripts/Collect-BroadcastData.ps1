param(
    [string]$Dataset = 'data/broadcast-sngsr-v1',
    [int]$TrainCount = 6000,
    [int]$ValidCount = 2000,
    [ValidateRange(1, 16)][int]$Workers = 8,
    [switch]$AuditOnly
)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$python = Join-Path $projectRoot '.venv/Scripts/python.exe'
if (-not [IO.Path]::IsPathRooted($Dataset)) { $Dataset = Join-Path $projectRoot $Dataset }
$Dataset = [IO.Path]::GetFullPath($Dataset)
$env:PYTHONPATH = (Join-Path $projectRoot 'src') + [IO.Path]::PathSeparator + $projectRoot
$env:PYTHONUTF8 = '1'
$arguments = @('-m', 'football_pipeline.broadcast_dataset', '--root', $Dataset,
    '--train', $TrainCount, '--val', $ValidCount, '--workers', $Workers)
if ($AuditOnly) { $arguments += '--audit-only' }
& $python @arguments
if ($LASTEXITCODE -ne 0) { throw 'Broadcast collection or label audit failed. Read the preceding error.' }
& $python (Join-Path $PSScriptRoot 'review_broadcast_data.py') --root $Dataset
if ($LASTEXITCODE -ne 0) { throw 'Could not prepare the editable review workspace and visual samples.' }
