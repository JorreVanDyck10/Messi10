param(
    [ValidateSet('app','evaluate','annotate','validate','train')][string]$Mode = 'app',
    [string]$Device = '0',
    [string]$RunName = '',
    [string]$Weights = 'artifacts/players-v2/players_best.pt',
    [string]$TrainingConfig = 'configs/train-players-unfrozen.json'
)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
Push-Location $projectRoot
try {
    $runtimePython = Join-Path $projectRoot '.venv\Scripts\python.exe'
    if (-not (Test-Path -LiteralPath $runtimePython)) { throw 'Voer eerst scripts\Setup-Persoon1.ps1 uit.' }
    New-Item -ItemType Directory -Force -Path '.cache\tmp' | Out-Null
    $env:TEMP = (Resolve-Path '.cache\tmp').Path
    $env:TMP = $env:TEMP
    $env:PYTHONIOENCODING = 'utf-8'
    $env:OMP_NUM_THREADS = '4'
    $env:MKL_NUM_THREADS = '4'
    $env:PYTHONPATH = (Join-Path $projectRoot 'src') + [IO.Path]::PathSeparator + $projectRoot
    $manifest = 'datasets/teamtrack-players-v2/manifest.json'
    $attestation = 'datasets/teamtrack-players-v2/ai-attestation.json'
    if ($Mode -eq 'annotate') {
        & $runtimePython -m persoon1 annotate --manifest $manifest --split all --port 8765
    } elseif ($Mode -eq 'validate') {
        & $runtimePython -m persoon1 validate --manifest $manifest --output reports/players-validation-local.json
    } elseif ($Mode -eq 'app') {
        $profile = Get-Content -Raw -LiteralPath 'configs/models-players.json' | ConvertFrom-Json
        foreach ($model in $profile.models) {
            $model.device = $Device
            $model.weights = [IO.Path]::GetFullPath((Join-Path "$projectRoot\configs" $model.weights))
        }
        if ($profile.appearance) {
            $profile.appearance.device = $Device
            $profile.appearance.weights = [IO.Path]::GetFullPath((Join-Path "$projectRoot\configs" $profile.appearance.weights))
        }
        if ($profile.handoff) {
            $profile.handoff.evaluation_record = [IO.Path]::GetFullPath((Join-Path "$projectRoot\configs" $profile.handoff.evaluation_record))
        }
        $localProfile = Join-Path $projectRoot '.cache\models-players-local.json'
        $profile | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $localProfile -Encoding utf8
        $env:FOOTBALL_MODELS = $localProfile
        & $runtimePython -m streamlit run streamlit_app.py
    } else {
        if (-not $RunName) { $RunName = 'players-' + (Get-Date -Format 'yyyyMMdd-HHmmss') }
        if ($RunName -notmatch '^[A-Za-z0-9_-]+$') { throw 'Gebruik een eenvoudige unieke runnaam.' }
        $runRoot = "runs/$RunName"
        if (Test-Path -LiteralPath $runRoot) { throw 'Deze run bestaat al; kies een nieuwe naam.' }
        if ($Mode -eq 'train') {
            & $runtimePython -m persoon1 train --manifest $manifest --approvals $attestation --weights models/yolo11n.pt --config $TrainingConfig --output "$runRoot/train" --device $Device --provisional-ai-labels
            if ($LASTEXITCODE -ne 0) { throw 'Training mislukt; lees de logs.' }
            $status = Get-Content -Raw -LiteralPath "$runRoot/train/status.json" | ConvertFrom-Json
            $Weights = $status.attempts[-1].best
        }
        & $runtimePython -m persoon1 predict --manifest $manifest --weights $Weights --mapping configs/mapping-players.json --output "$runRoot/validation-inference" --split val --imgsz 1920 --device $Device --confidence 0.001
        if ($LASTEXITCODE -ne 0) { throw 'Voorspellen mislukt. Controleer ook of git lfs pull is uitgevoerd.' }
        & $runtimePython -m persoon1 evaluate --manifest $manifest --predictions "$runRoot/validation-inference" --output "$runRoot/validation-metrics" --approvals $attestation --provisional-ai-labels
        if ($LASTEXITCODE -ne 0) { throw 'Evalueren mislukt.' }
        & $runtimePython -m persoon1.participant_baseline --manifest $manifest --attestation $attestation --baseline-weights models/yolo11n.pt --candidate-predictions "$runRoot/validation-inference" --output "$runRoot/baseline-comparison" --device $Device
    }
    if ($LASTEXITCODE -ne 0) { throw 'De gekozen stap is niet geslaagd.' }
} finally { Pop-Location }
