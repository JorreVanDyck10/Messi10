param(
    [string]$Dataset = 'data/joint-local-20261027-v2',
    [string]$Output = 'artifacts/joint-retrain-20261027-v2'
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
    if (-not (Test-Path -LiteralPath (Join-Path $Dataset 'inventory.json'))) {
        & $python -m football_pipeline.joint_data --output $Dataset
        if ($LASTEXITCODE -ne 0) { throw 'Data-audit mislukt; bewaar de uitvoer en herstel de oorzaak.' }
    }
    & $python -u -m football_pipeline.joint_training run --dataset $Dataset --output $Output
    if ($LASTEXITCODE -ne 0) { throw 'Trainingsronde niet voltooid; lees de bewaarde logs.' }
} finally { Pop-Location }
