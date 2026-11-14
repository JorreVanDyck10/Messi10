param([string]$RunName = '')
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
Push-Location $projectRoot
try {
    $runtimePython = Join-Path $projectRoot '.venv\Scripts\python.exe'
    if (-not (Test-Path -LiteralPath $runtimePython)) { throw 'Voer eerst scripts\Setup-Persoon1.ps1 uit.' }
    if (-not $RunName) { $RunName = 'appearance-' + (Get-Date -Format 'yyyyMMdd-HHmmss') }
    if ($RunName -notmatch '^[A-Za-z0-9_-]+$') { throw 'Gebruik een eenvoudige unieke runnaam.' }
    New-Item -ItemType Directory -Force -Path '.cache\tmp' | Out-Null
    $env:TEMP = (Resolve-Path '.cache\tmp').Path
    $env:TMP = $env:TEMP
    $env:OMP_NUM_THREADS = '4'
    $env:MKL_NUM_THREADS = '4'
    $env:PYTHONIOENCODING = 'utf-8'
    $env:PYTHONPATH = (Join-Path $projectRoot 'src') + [IO.Path]::PathSeparator + $projectRoot
    & $runtimePython -m persoon1.role_training --output "runs/appearance/$RunName" --fine-tune --encoder-checkpoint artifacts/appearance-v1/roles_seed_r004.pt
    if ($LASTEXITCODE -ne 0) { throw 'Roltraining mislukt; controleer de uitvoer.' }
    Write-Host 'De nieuwe run is bewaard. Vergelijk de validatie voordat je een modelprofiel wijzigt.'
} finally { Pop-Location }
