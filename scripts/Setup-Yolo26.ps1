param([string]$BasePython='')
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
if (-not $BasePython) { $BasePython = Join-Path $projectRoot '.venv/Scripts/python.exe' }
if (-not (Test-Path -LiteralPath $BasePython)) {
    throw 'Geef -BasePython met de bestaande werkende app-Python. Deze omgeving wordt alleen gelezen.'
}
$BasePython = (Resolve-Path -LiteralPath $BasePython).Path
$destination = Join-Path $projectRoot '.tools/yolo26-env'
$previousYoloConfig = $env:YOLO_CONFIG_DIR
$env:YOLO_CONFIG_DIR = Join-Path $projectRoot '.cache/yolo26-settings'
Push-Location $projectRoot
try {
    $base = & $BasePython -c 'import sys,sysconfig,json,torch,streamlit; print(json.dumps({"python":sys.executable,"version":list(sys.version_info[:2]),"packages":sysconfig.get_paths()["purelib"]}))' | Select-Object -Last 1 | ConvertFrom-Json
    if ($LASTEXITCODE -ne 0) { throw 'De basisomgeving heeft nog geen werkende PyTorch en Streamlit.' }
    if ($base.version[0] -ne 3 -or $base.version[1] -notin @(11,12)) { throw 'Gebruik de ondersteunde Python 3.11- of 3.12-appomgeving.' }
    if (Test-Path -LiteralPath $destination) {
        throw 'De YOLO26-omgeving bestaat al en wordt niet overschreven. Gebruik die eerst met Start-Yolo26.ps1 -CheckOnly.'
    }
    & $BasePython -m venv $destination
    if ($LASTEXITCODE -ne 0) { throw 'Aparte Python-omgeving maken mislukt.' }
    $python = Join-Path $destination 'Scripts/python.exe'
    $packages = Join-Path $destination 'Lib/site-packages'
    # De eigen packages staan eerst; grote compatibele Torch/CUDA-packages worden hergebruikt.
    Set-Content -LiteralPath (Join-Path $packages 'original-app-runtime.pth') -Value $base.packages -Encoding ascii
    & $python -m pip install ultralytics==8.4.211
    if ($LASTEXITCODE -ne 0) { throw 'YOLO26-bibliotheek installeren mislukt; de oorspronkelijke appomgeving is behouden.' }
    & $python -c 'import ultralytics,torch,streamlit; assert ultralytics.__version__=="8.4.211"; print("YOLO26 klaar",ultralytics.__version__,torch.__version__)'
    if ($LASTEXITCODE -ne 0) { throw 'De nieuwe runtimecontrole is mislukt.' }
    Write-Host 'Importeer het voetbalcheckpoint met scripts/Import-Yolo26.ps1. Bewaar ook de bestaande basisomgeving.'
} finally {
    Pop-Location
    $env:YOLO_CONFIG_DIR = $previousYoloConfig
}
