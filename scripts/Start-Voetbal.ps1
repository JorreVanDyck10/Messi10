param(
    [ValidateSet('yolo11','yolo26')][string]$Model = 'yolo26',
    [string]$Device = 'auto',
    [ValidateRange(1024,65535)][int]$Port = 8501,
    [string]$Python = '',
    [string]$FieldRuntime = '.tools/field-runtime.json',
    [switch]$CheckOnly
)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
if (-not $Python) {
    $relativePython = if ($Model -eq 'yolo26') { '.tools/yolo26-env/Scripts/python.exe' } else { '.venv/Scripts/python.exe' }
    $Python = Join-Path $projectRoot $relativePython
}
if (-not (Test-Path -LiteralPath $Python)) {
    throw "Python-omgeving ontbreekt: $Python. Gebruik Setup-Yolo26.ps1 voor de aparte YOLO26-omgeving."
}
$names = @('PYTHONPATH','FOOTBALL_MODELS','FOOTBALL_AUTO_MODELS','FOOTBALL_FIELD_RUNTIME','FOOTBALL_TEAMS','FOOTBALL_SCHOOL_MODE','YOLO_CONFIG_DIR')
$previousEnvironment = @{}
foreach ($name in $names) { $previousEnvironment[$name] = [Environment]::GetEnvironmentVariable($name, 'Process') }
Push-Location $projectRoot
try {
    $env:YOLO_CONFIG_DIR = Join-Path $projectRoot ".cache/$Model-settings"
    $env:PYTHONPATH = (Join-Path $projectRoot 'src') + [IO.Path]::PathSeparator + $projectRoot
    if ($Device -eq 'auto') {
        $Device = (& $Python -c 'import torch; print("0" if torch.cuda.is_available() else "cpu")' | Select-Object -Last 1).Trim()
        if ($LASTEXITCODE -ne 0) { throw 'CPU/GPU-keuze kon niet worden gecontroleerd.' }
    }
    $result = & $Python -m football_pipeline.model_switch prepare --model $Model --device $Device 2>&1
    if ($LASTEXITCODE -ne 0) { throw ("Modelcontrole mislukt: " + ($result -join [Environment]::NewLine)) }
    $profile = ($result | Select-Object -Last 1 | ConvertFrom-Json).profile
    $env:FOOTBALL_MODELS = $profile
    $env:FOOTBALL_AUTO_MODELS = $profile
    $env:FOOTBALL_TEAMS = Join-Path $projectRoot 'configs/teams-broadcast.json'
    $env:FOOTBALL_FIELD_RUNTIME = if ([IO.Path]::IsPathRooted($FieldRuntime)) { $FieldRuntime } else { Join-Path $projectRoot $FieldRuntime }
    $env:FOOTBALL_SCHOOL_MODE = '0'
    $env:YOLO_CONFIG_DIR = Join-Path $projectRoot ".cache/$Model-settings"
    Write-Host "Model: $Model | Device: $Device | Profiel: $profile"
    if ($CheckOnly) {
        & $Python -c 'import sys; from football_pipeline.detection import load_model_manifest, UltralyticsDetector; UltralyticsDetector(load_model_manifest(sys.argv[1])); print("Alle detectie-, rol- en shirtmodellen geladen.")' $profile
        if ($LASTEXITCODE -ne 0) { throw 'De echte modelgewichten konden niet worden geladen.' }
        if (-not (Test-Path -LiteralPath $env:FOOTBALL_FIELD_RUNTIME)) {
            Write-Warning 'Automatische veldruntime ontbreekt nog. Handmatige kalibratie is wel beschikbaar.'
        }
    } else {
        & $Python -m streamlit run streamlit_app.py --server.address=127.0.0.1 --server.port=$Port
        if ($LASTEXITCODE -ne 0) { throw 'De toepassing is niet correct afgesloten.' }
    }
} finally {
    Pop-Location
    foreach ($name in $names) { [Environment]::SetEnvironmentVariable($name, $previousEnvironment[$name], 'Process') }
}
