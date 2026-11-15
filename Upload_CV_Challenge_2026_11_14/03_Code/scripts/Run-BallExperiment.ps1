param(
    [ValidateSet(640,1920)][int]$Resolution = 1920,
    [string]$Device = '0',
    [string]$RunName = '',
    [string]$CandidateWeights = ''
)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
Push-Location $projectRoot
try {
    $runtimePython = Join-Path $projectRoot '.venv\Scripts\python.exe'
    if (-not (Test-Path -LiteralPath $runtimePython)) { throw 'Voer eerst Setup-Persoon1.ps1 uit.' }
    if (-not $RunName) { $RunName = 'ball-' + (Get-Date -Format 'yyyyMMdd-HHmmss') }
    if ($RunName -notmatch '^[A-Za-z0-9_-]+$') { throw 'Gebruik een eenvoudige, unieke runnaam.' }
    New-Item -ItemType Directory -Force -Path '.cache\tmp' | Out-Null
    $env:TEMP = (Resolve-Path '.cache\tmp').Path
    $env:TMP = $env:TEMP
    $env:PYTHONIOENCODING = 'utf-8'
    $manifest = 'data/panoris-ball-ai-v1/manifest.json'
    $attestation = 'data/panoris-ball-ai-v1/ai-attestation.json'
    if (-not (Test-Path -LiteralPath $manifest)) {
        & $runtimePython -m persoon1.project_dataset --video assets/videos/HBTFZwMdcCw.mp4
        if ($LASTEXITCODE -ne 0) { throw 'Dataset opbouwen mislukt.' }
    }
    $runRoot = "runs/$RunName"
    if (Test-Path -LiteralPath $runRoot) { throw 'Deze run bestaat al; kies een nieuwe naam.' }
    if (-not $CandidateWeights) {
        $config = if ($Resolution -eq 1920) { 'configs/train-ball-1920.json' } else { 'configs/train-reference.json' }
        & $runtimePython -m persoon1 train --manifest $manifest --approvals $attestation --weights models/yolo11n.pt --config $config --output "$runRoot/train" --device $Device --provisional-ai-labels
        if ($LASTEXITCODE -ne 0) { throw 'Training mislukt; lees status en logs.' }
        $status = Get-Content -Raw -LiteralPath "$runRoot/train/status.json" | ConvertFrom-Json
        $CandidateWeights = $status.attempts[-1].best
    }
    foreach ($modelRole in @('baseline','candidate')) {
        $weights = if ($modelRole -eq 'baseline') { 'models/yolo11n.pt' } else { $CandidateWeights }
        $mapping = if ($modelRole -eq 'baseline') { 'configs/mapping-pretrained-ball.json' } else { 'configs/mapping-specialist-example.json' }
        & $runtimePython -m persoon1 predict --manifest $manifest --weights $weights --mapping $mapping --output "$runRoot/$modelRole" --split val --imgsz $Resolution --device $Device --confidence 0.001
        if ($LASTEXITCODE -ne 0) { throw 'Voorspellen mislukt.' }
        & $runtimePython -m persoon1 evaluate --manifest $manifest --predictions "$runRoot/$modelRole" --output "$runRoot/$modelRole-metrics" --approvals $attestation --provisional-ai-labels
        if ($LASTEXITCODE -ne 0) { throw 'Evalueren mislukt.' }
    }
    & $runtimePython -m persoon1 compare --baseline "$runRoot/baseline-metrics/metrics.json" --candidate "$runRoot/candidate-metrics/metrics.json" --output "$runRoot/comparison.json"
    if ($LASTEXITCODE -ne 0) { throw 'Vergelijken mislukt.' }
    Write-Host "Echte ontwikkelmetingen staan in $runRoot. AI-labels zijn nog niet door het team gereviewd."
} finally {
    Pop-Location
}
