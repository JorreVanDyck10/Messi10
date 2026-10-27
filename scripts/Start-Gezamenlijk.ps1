param(
    [string]$TrainingRun = 'artifacts/joint-retrain-20261027-v2',
    [int]$Port = 8501
)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$profile = Join-Path $projectRoot 'configs/models-integrated-20261027.json'
$teams = Join-Path $projectRoot 'configs/teams.json'
$broadcastProfile = Join-Path $projectRoot 'configs/models-broadcast.json'
if (Test-Path -LiteralPath $broadcastProfile) {
    $profile = $broadcastProfile
    $teams = Join-Path $projectRoot 'configs/teams-broadcast.json'
}
$trainingPath = [IO.Path]::GetFullPath((Join-Path $projectRoot $TrainingRun))
$runtime = Join-Path $trainingPath 'selected-field-runtime.json'
if (-not (Test-Path -LiteralPath $profile) -or -not (Test-Path -LiteralPath $runtime)) {
    throw 'De gezamenlijke modelselectie is nog niet klaar. Zie het trainingsrapport.'
}
$env:FOOTBALL_MODELS = $profile
$env:FOOTBALL_AUTO_MODELS = $profile
$env:FOOTBALL_FIELD_RUNTIME = $runtime
$env:FOOTBALL_CALIBRATION_MODE = 'automatic'
$env:FOOTBALL_TEAMS = $teams
$env:OMP_NUM_THREADS = '4'
$env:MKL_NUM_THREADS = '4'
Push-Location $projectRoot
try {
    & (Join-Path $projectRoot '.venv/Scripts/python.exe') -m streamlit run streamlit_app.py --server.address=127.0.0.1 --server.port=$Port
} finally { Pop-Location }
