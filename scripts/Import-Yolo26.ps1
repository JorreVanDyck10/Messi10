param([Parameter(Mandatory=$true)][string]$Weights, [string]$Python='')
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
if (-not $Python) { $Python = Join-Path $projectRoot '.tools/yolo26-env/Scripts/python.exe' }
if (-not (Test-Path -LiteralPath $Python)) { throw 'Maak eerst de aparte omgeving met scripts/Setup-Yolo26.ps1.' }
$checkpoint = (Resolve-Path -LiteralPath $Weights).Path
$previousPythonPath = [Environment]::GetEnvironmentVariable('PYTHONPATH','Process')
$previousYoloConfig = $env:YOLO_CONFIG_DIR
Push-Location $projectRoot
try {
    $env:YOLO_CONFIG_DIR = Join-Path $projectRoot '.cache/yolo26-settings'
    $env:PYTHONPATH = (Join-Path $projectRoot 'src') + [IO.Path]::PathSeparator + $projectRoot
    $result = & $Python -m football_pipeline.model_switch import $checkpoint 2>&1
    if ($LASTEXITCODE -ne 0) { throw ("YOLO26-import mislukt: " + ($result -join [Environment]::NewLine)) }
    $result | Write-Output
} finally {
    Pop-Location
    [Environment]::SetEnvironmentVariable('PYTHONPATH',$previousPythonPath,'Process')
    $env:YOLO_CONFIG_DIR = $previousYoloConfig
}
