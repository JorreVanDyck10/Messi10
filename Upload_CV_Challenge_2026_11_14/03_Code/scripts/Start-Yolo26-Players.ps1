param(
    [ValidateSet('current', 'yolo11s', 'yolo26s')][string]$Model = 'yolo26s',
    [string]$Experiment = 'artifacts/yolo26-players-20261113-v1',
    [int]$Port = 8502
)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$experimentRoot = if ([IO.Path]::IsPathRooted($Experiment)) { $Experiment } else { Join-Path $projectRoot $Experiment }
$profileName = if ($Model -eq 'current') { 'current-profile.json' } else { "$Model-profile.json" }
$profile = Join-Path $experimentRoot $profileName
$python = Join-Path $projectRoot '.tools/yolo26-env/Scripts/python.exe'
if (-not (Test-Path -LiteralPath $python) -or -not (Test-Path -LiteralPath $profile)) {
    throw 'De vergelijkingsomgeving of het afgeronde kandidaatprofiel ontbreekt. Zie de overdracht van het experiment.'
}
$env:PYTHONPATH = (Join-Path $projectRoot 'src') + [IO.Path]::PathSeparator + $projectRoot
$env:FOOTBALL_MODELS = $profile
$env:FOOTBALL_AUTO_MODELS = $profile
$env:FOOTBALL_FIELD_RUNTIME = Join-Path $projectRoot '.tools/field-runtime.json'
$env:YOLO_CONFIG_DIR = Join-Path $projectRoot '.cache/yolo26-settings'
Push-Location $projectRoot
try {
    & $python -m streamlit run streamlit_app.py --server.address=127.0.0.1 --server.port=$Port
} finally { Pop-Location }
