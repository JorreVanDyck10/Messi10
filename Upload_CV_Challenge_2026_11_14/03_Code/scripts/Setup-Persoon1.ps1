param([string]$Python = 'python', [switch]$CpuOnly)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
Push-Location $projectRoot
try {
    $pythonVersion = & $Python -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")'
    if ($LASTEXITCODE -ne 0 -or $pythonVersion -notin @('3.11', '3.12')) {
        throw 'Gebruik Python 3.11 of 3.12. Geef zo nodig het volledige pad mee met -Python.'
    }
    New-Item -ItemType Directory -Force -Path '.cache\tmp', 'models' | Out-Null
    $env:TEMP = (Resolve-Path '.cache\tmp').Path
    $env:TMP = $env:TEMP
    if (-not (Test-Path -LiteralPath '.venv\Scripts\python.exe')) {
        & $Python -m venv .venv
        if ($LASTEXITCODE -ne 0) { throw 'Aanmaken van de projectomgeving is mislukt.' }
    }
    $runtimePython = Join-Path $projectRoot '.venv\Scripts\python.exe'
    & $runtimePython -m pip --version
    if ($LASTEXITCODE -ne 0) {
        & $runtimePython -m ensurepip --upgrade --default-pip
        if ($LASTEXITCODE -ne 0) { throw 'Installeren van pip is mislukt.' }
    }
    $torchIndex = if ($CpuOnly) { 'https://download.pytorch.org/whl/cpu' } else { 'https://download.pytorch.org/whl/cu124' }
    & $runtimePython -m pip install --only-binary=:all: torch==2.6.0 torchvision==0.21.0 --index-url $torchIndex
    if ($LASTEXITCODE -ne 0) { throw 'Installeren van PyTorch is mislukt.' }
    & $runtimePython -m pip install --only-binary=:all: -r requirements.txt
    if ($LASTEXITCODE -ne 0) { throw 'Installeren van de projectbibliotheken is mislukt.' }
    & $runtimePython -m pip install --only-binary=:all: -r requirements-app-gpu.txt
    if ($LASTEXITCODE -ne 0) { throw 'Installeren van de toepassing is mislukt.' }
    & $runtimePython -m pip install --no-deps --editable .
    if ($LASTEXITCODE -ne 0) { throw 'Registreren van de projectmodules is mislukt.' }
    if (-not $CpuOnly) {
        & $runtimePython -c "import torch; assert torch.cuda.is_available(), 'CUDA ontbreekt; controleer de NVIDIA-driver en de PyTorch-installatie'; print('GPU:', torch.cuda.get_device_name(0))"
        if ($LASTEXITCODE -ne 0) { throw 'De GPU-omgeving is niet bruikbaar; zie de controle hierboven.' }
    }
    if (-not (Test-Path -LiteralPath 'models\yolo11n.pt')) {
        Invoke-WebRequest -UseBasicParsing -Uri 'https://github.com/ultralytics/assets/releases/download/v8.3.0/yolo11n.pt' -OutFile 'models\yolo11n.pt'
    }
    $expectedModelHash = '0ebbc80d4a7680d14987a577cd21342b65ecfd94632bd9a8da63ae6417644ee1'
    if ((Get-FileHash -LiteralPath 'models\yolo11n.pt' -Algorithm SHA256).Hash.ToLowerInvariant() -ne $expectedModelHash) {
        throw 'De modelidentiteit wijkt af van de gebruikte pretrained referentie.'
    }
    & $runtimePython -m persoon1 doctor --output reports/environment-local.json
    if ($LASTEXITCODE -ne 0) { throw 'De omgevingscontrole is mislukt.' }
    Write-Host 'Klaar. Start het geleverde spelermodel met scripts\Start-Spelermodel.ps1.'
} finally {
    Pop-Location
}
