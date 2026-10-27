param(
    [string]$Dataset = 'data/broadcast-pitch-v1',
    [string]$Output = 'artifacts/broadcast-pitch-v1'
)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$python = Join-Path $projectRoot '.venv/Scripts/python.exe'
$env:PYTHONPATH = (Join-Path $projectRoot 'src') + [IO.Path]::PathSeparator + $projectRoot
$env:PYTHONUNBUFFERED = '1'
$env:OMP_NUM_THREADS = '4'
$env:MKL_NUM_THREADS = '4'
Push-Location $projectRoot
try {
    & $python -m football_pipeline.broadcast_data $Dataset
    if ($LASTEXITCODE -ne 0) { throw 'Broadcastdata niet volledig voorbereid; zie de bewaarde voortgang.' }
    & $python -m football_pipeline.broadcast_training detector --dataset $Dataset --output $Output
    if ($LASTEXITCODE -ne 0) { throw 'Spelertraining niet voltooid; bewaar de checkpoints en logs.' }
    & $python -m football_pipeline.broadcast_training appearance --dataset $Dataset --output $Output
    if ($LASTEXITCODE -ne 0) { throw 'Rol- of teamtraining niet voltooid; zie de bewaarde voortgang.' }
    & $python -m football_pipeline.broadcast_release --dataset $Dataset --output $Output
    if ($LASTEXITCODE -ne 0) { throw 'Vergelijking of demonstratie niet voltooid; het resultaat is niet goedgekeurd.' }
} finally { Pop-Location }
