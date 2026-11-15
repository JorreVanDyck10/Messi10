param(
    [string]$Device = '0',
    [ValidateRange(1024,65535)][int]$Port = 8501,
    [switch]$BroadcastTiles,
    [switch]$CheckOnly
)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$runtimePython = Join-Path $projectRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $runtimePython)) {
    throw 'Voer eerst scripts\Setup-Persoon1.ps1 uit.'
}

# Bewaar de instellingen van deze PowerShell-sessie voor na het afsluiten.
$previousEnvironment = @{}
foreach ($name in @('PYTHONPATH', 'FOOTBALL_SCHOOL_MODE', 'FOOTBALL_MODELS', 'FOOTBALL_RUNS')) {
    $previousEnvironment[$name] = [Environment]::GetEnvironmentVariable($name, 'Process')
}
Push-Location $projectRoot
try {
    $env:PYTHONPATH = (Join-Path $projectRoot 'src') + [IO.Path]::PathSeparator + $projectRoot
    $env:FOOTBALL_SCHOOL_MODE = '1'
    $env:FOOTBALL_RUNS = Join-Path $projectRoot 'runs\school'
    $profileName = if ($BroadcastTiles) { 'models-players-ball-broadcast-v3' } else { 'models-school' }
    $profile = Get-Content -Raw -Encoding UTF8 -LiteralPath "configs\$profileName.json" | ConvertFrom-Json
    foreach ($model in $profile.models) {
        $model.device = $Device
        $model.weights = [IO.Path]::GetFullPath((Join-Path "$projectRoot\configs" $model.weights))
    }
    foreach ($property in $profile.handoff.PSObject.Properties) {
        if ($property.Name.EndsWith('_record')) {
            $property.Value = [IO.Path]::GetFullPath((Join-Path "$projectRoot\configs" $property.Value))
        }
    }
    New-Item -ItemType Directory -Force -Path '.cache' | Out-Null
    $env:FOOTBALL_MODELS = Join-Path $projectRoot ".cache\$profileName-school-local.json"
    $profile | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $env:FOOTBALL_MODELS -Encoding utf8

    # Controleer bestanden, checksums, klassen en de gekozen CPU/GPU vóór de app start.
    & $runtimePython -c 'import sys; from football_pipeline.detection import load_model_manifest, validate_detection_devices; validate_detection_devices(load_model_manifest(sys.argv[1])); print("Schoolprofiel gecontroleerd.")' $env:FOOTBALL_MODELS
    if ($LASTEXITCODE -ne 0) { throw 'Modelcontrole mislukt; lees de fout hierboven.' }
    if (-not $CheckOnly) {
        & $runtimePython -m streamlit run streamlit_app.py --server.address 127.0.0.1 --server.port $Port
        if ($LASTEXITCODE -ne 0) { throw 'De schoolapp is niet correct afgesloten.' }
    }
} finally {
    Pop-Location
    foreach ($name in $previousEnvironment.Keys) {
        [Environment]::SetEnvironmentVariable($name, $previousEnvironment[$name], 'Process')
    }
}
