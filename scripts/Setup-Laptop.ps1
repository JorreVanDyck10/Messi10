param([string]$Python = 'py', [switch]$SkipField)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
Push-Location $projectRoot
try {
    if (-not (Get-Command git -ErrorAction SilentlyContinue)) { throw 'Installeer Git voor Windows en open daarna een nieuwe PowerShell.' }
    # New laptops use Python 3.11 for both app and PnLCalib compatibility.
    $pythonArgs = if ($Python -eq 'py') { @('-3.11') } else { @() }
    $version = & $Python @pythonArgs -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")'
    if ($LASTEXITCODE -ne 0 -or $version -ne '3.11') { throw 'Installeer Python 3.11 of geef -Python met het volledige pad naar python.exe.' }
    if (Test-Path -LiteralPath '.venv/Scripts/python.exe') {
        $markerPath = '.venv/sportsvision-laptop-setup.json'
        if (-not (Test-Path -LiteralPath $markerPath) -or (Get-Content -LiteralPath $markerPath -Raw | ConvertFrom-Json).setup -ne 'sportsvision-cu128') {
            throw 'Er bestaat al een andere .venv. Gebruik een nieuwe checkout; een bestaande omgeving wordt niet overschreven.'
        }
    } else {
        & $Python @pythonArgs -m venv .venv
        if ($LASTEXITCODE -ne 0) { throw 'Aanmaken van de omgeving mislukt.' }
        '{"setup":"sportsvision-cu128","python":"3.11"}' | Set-Content -LiteralPath '.venv/sportsvision-laptop-setup.json' -Encoding utf8
    }
    $runtimePython = Join-Path $projectRoot '.venv/Scripts/python.exe'
    & $runtimePython -m pip install torch==2.7.1 torchvision==0.22.1 --index-url https://download.pytorch.org/whl/cu128
    if ($LASTEXITCODE -ne 0) { throw 'PyTorch/CUDA installeren mislukt.' }
    & $runtimePython -m pip install -r requirements-laptop.txt
    if ($LASTEXITCODE -ne 0) { throw 'Applicatiebibliotheken installeren mislukt.' }
    & $runtimePython -m pip install --no-deps --editable .
    if ($LASTEXITCODE -ne 0) { throw 'Project registreren mislukt.' }
    $env:PYTHONPATH = (Join-Path $projectRoot 'src') + [IO.Path]::PathSeparator + $projectRoot
    if (Test-Path -LiteralPath 'datasets/training-runtime-v1/manifest.json') {
        & git lfs version
        if ($LASTEXITCODE -ne 0) { throw 'Installeer Git LFS en voer daarna deze installatie opnieuw uit.' }
        & git lfs install --local
        if ($LASTEXITCODE -ne 0) { throw 'Git LFS activeren mislukt.' }
        & git lfs pull --include='data/**,datasets/**,assets/annotations/**,artifacts/broadcast-players-v1/**,artifacts/broadcast-ball-v3/**,artifacts/broadcast-pitch-v1/appearance/features.pt'
        if ($LASTEXITCODE -ne 0) { throw 'Trainingsdata ophalen via Git LFS mislukt.' }
        & $runtimePython -m football_pipeline.repository_training prepare
        if ($LASTEXITCODE -ne 0) { throw 'De gedeelde trainingsdata zijn nog niet volledig; lees de bestandscontrole hierboven.' }
    }
    & $runtimePython -m football_pipeline.training_hardware
    if ($LASTEXITCODE -ne 0) { throw 'De GPU kan de trainingscontrole niet uitvoeren. Controleer de NVIDIA-driver.' }
    if (-not (Test-Path -LiteralPath '.tools/ffmpeg-master-latest-win64-gpl/bin/ffprobe.exe')) {
        & (Join-Path $PSScriptRoot 'setup_tools.ps1')
        if ($LASTEXITCODE -ne 0) { throw 'FFmpeg/ffprobe installeren mislukt.' }
    }
    if (-not $SkipField) {
        & $runtimePython scripts/setup_field_model.py --cuda128
        if ($LASTEXITCODE -ne 0) { throw 'Veldruntime voorbereiden mislukt.' }
        & $runtimePython scripts/setup_field_training.py
        if ($LASTEXITCODE -ne 0) { throw 'Veldtraining voorbereiden mislukt.' }
    }
    Write-Host 'Installatie klaar. Start scripts/Start-Laptop.ps1 en open Modellen trainen.'
} finally { Pop-Location }
