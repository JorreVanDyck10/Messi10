param([int]$Port = 8501, [string]$ModelProfile = 'configs/models-broadcast.json', [string]$FieldRuntime = '.tools/field-runtime.json')
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
Push-Location $projectRoot
try {
    $python = Join-Path $projectRoot '.venv/Scripts/python.exe'
    if (-not (Test-Path -LiteralPath $python)) { throw 'Voer eerst scripts/Setup-Laptop.ps1 uit.' }
    $env:PYTHONPATH = (Join-Path $projectRoot 'src') + [IO.Path]::PathSeparator + $projectRoot
    $env:FOOTBALL_AUTO_MODELS = if ([IO.Path]::IsPathRooted($ModelProfile)) { $ModelProfile } else { Join-Path $projectRoot $ModelProfile }
    $env:FOOTBALL_MODELS = $env:FOOTBALL_AUTO_MODELS
    $env:FOOTBALL_FIELD_RUNTIME = if ([IO.Path]::IsPathRooted($FieldRuntime)) { $FieldRuntime } else { Join-Path $projectRoot $FieldRuntime }
    & $python -m streamlit run streamlit_app.py --server.address=127.0.0.1 --server.port=$Port
} finally { Pop-Location }
