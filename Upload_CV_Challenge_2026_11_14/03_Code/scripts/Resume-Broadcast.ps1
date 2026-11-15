param([ValidateSet('status','training','download','prepare-data')][string]$Action = 'status')
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$env:PYTHONPATH = (Join-Path $projectRoot 'src') + [IO.Path]::PathSeparator + $projectRoot
$env:PYTHONUNBUFFERED = '1'
$env:OMP_NUM_THREADS = '4'
$env:MKL_NUM_THREADS = '4'
Push-Location $projectRoot
try {
    & (Join-Path $projectRoot '.venv/Scripts/python.exe') -m football_pipeline.broadcast_resume $Action
    if ($LASTEXITCODE -ne 0) { throw 'Hervatten gestopt; bestaande checkpoints en gedeeltelijke data blijven bewaard.' }
} finally { Pop-Location }
