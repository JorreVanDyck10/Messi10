param(
    [ValidateSet('school', 'broadcast')][string]$Mode = 'school',
    [string]$Device = 'cpu',
    [ValidateRange(1024,65535)][int]$Port = 8501,
    [switch]$BroadcastTiles,
    [switch]$CheckOnly
)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
if ($Mode -eq 'school') {
    & (Join-Path $PSScriptRoot 'Start-School.ps1') -Device $Device -Port $Port -BroadcastTiles:$BroadcastTiles -CheckOnly:$CheckOnly
    return
}
if ($BroadcastTiles) { throw 'Gebruik -BroadcastTiles met -Mode school.' }
$runtimePython = Join-Path $projectRoot '.venv/Scripts/python.exe'
if (-not (Test-Path -LiteralPath $runtimePython)) { throw 'Voer eerst scripts/Setup-Final.ps1 uit.' }
$previousEnvironment = @{}
foreach ($name in @('PYTHONPATH', 'FOOTBALL_SCHOOL_MODE', 'FOOTBALL_MODELS', 'FOOTBALL_AUTO_MODELS', 'FOOTBALL_TEAMS', 'FOOTBALL_RUNS', 'FOOTBALL_CALIBRATION_MODE')) {
    $previousEnvironment[$name] = [Environment]::GetEnvironmentVariable($name, 'Process')
}
Push-Location $projectRoot
try {
    $env:PYTHONPATH = (Join-Path $projectRoot 'src') + [IO.Path]::PathSeparator + $projectRoot
    $env:FOOTBALL_SCHOOL_MODE = '0'
    $env:FOOTBALL_TEAMS = Join-Path $projectRoot 'configs/teams-broadcast.json'
    $env:FOOTBALL_RUNS = Join-Path $projectRoot 'runs/broadcast'
    $env:FOOTBALL_CALIBRATION_MODE = 'automatic'
    $profile = Get-Content -Raw -Encoding UTF8 -LiteralPath 'configs/models-broadcast.json' | ConvertFrom-Json
    foreach ($model in $profile.models) {
        $model.device = $Device
        $model.weights = [IO.Path]::GetFullPath((Join-Path "$projectRoot/configs" $model.weights))
    }
    foreach ($head in @('appearance', 'kit_embedding', 'role_context')) {
        if ($head -ne 'role_context') { $profile.$head.device = $Device }
        $profile.$head.weights = [IO.Path]::GetFullPath((Join-Path "$projectRoot/configs" $profile.$head.weights))
    }
    $profile.handoff.evaluation_record = [IO.Path]::GetFullPath((Join-Path "$projectRoot/configs" $profile.handoff.evaluation_record))
    New-Item -ItemType Directory -Force -Path '.cache' | Out-Null
    $env:FOOTBALL_MODELS = Join-Path $projectRoot '.cache/models-broadcast-local.json'
    $env:FOOTBALL_AUTO_MODELS = $env:FOOTBALL_MODELS
    $profile | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $env:FOOTBALL_MODELS -Encoding utf8
    & $runtimePython -c 'import sys; from football_pipeline.detection import load_model_manifest, validate_detection_devices; validate_detection_devices(load_model_manifest(sys.argv[1])); print("Broadcastprofiel gecontroleerd.")' $env:FOOTBALL_MODELS
    if ($LASTEXITCODE -ne 0) { throw 'Modelcontrole mislukt.' }
    if (-not $CheckOnly) {
        $fieldRuntime = if ($env:FOOTBALL_FIELD_RUNTIME) { $env:FOOTBALL_FIELD_RUNTIME } else { Join-Path $projectRoot '.tools/field-runtime.json' }
        if (-not (Test-Path -LiteralPath $fieldRuntime)) {
            throw 'Installeer eerst het veldmodel: python scripts/setup_field_model.py --device cpu (of --device cuda:0).'
        }
        & $runtimePython -m streamlit run streamlit_app.py --server.address 127.0.0.1 --server.port $Port
        if ($LASTEXITCODE -ne 0) { throw 'De app is niet correct afgesloten.' }
    }
} finally {
    Pop-Location
    foreach ($name in $previousEnvironment.Keys) {
        [Environment]::SetEnvironmentVariable($name, $previousEnvironment[$name], 'Process')
    }
}
