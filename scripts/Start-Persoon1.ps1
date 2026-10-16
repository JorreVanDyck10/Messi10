param(
    [ValidateSet('prepare','baseline','annotate','validate','train','doctor')][string]$Mode = 'annotate',
    [ValidateSet('train','val','test')][string]$Split = 'train',
    [string]$Device = '0',
    [string]$RunName = '',
    [ValidateSet(640,960,1920)][int]$InferenceSize = 640,
    [int]$Port = 8765
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
    $manifest = 'data/panoris/manifest.json'
    if ($Mode -eq 'doctor') {
        & $runtimePython -m persoon1 doctor --output reports/environment-local.json
    } else {
        $video = 'assets/videos/HBTFZwMdcCw.mp4'
        if (-not (Test-Path -LiteralPath $video) -or (Get-Item -LiteralPath $video).Length -lt 1024) {
            throw 'De MP4 ontbreekt of is nog een LFS-pointer. Voer git lfs pull uit.'
        }
        $sourceRecord = Get-Content -Raw -LiteralPath 'assets/videos/HBTFZwMdcCw.source.json' | ConvertFrom-Json
        if ((Get-FileHash -LiteralPath $video -Algorithm SHA256).Hash.ToLowerInvariant() -ne $sourceRecord.sha256) {
            throw 'De MP4 wijkt af van de geregistreerde bronidentiteit.'
        }
        if (-not (Test-Path -LiteralPath $manifest)) {
            & $runtimePython -m persoon1 extract --video $video --plan configs/HBTFZwMdcCw-selection.json --output data/panoris
            if ($LASTEXITCODE -ne 0) { throw 'Voorbereiden van de frames is mislukt.' }
        }
        switch ($Mode) {
            'prepare' { Write-Host 'De kandidaatframes en het manifest staan in data/panoris.' }
            'baseline' {
                if ($Split -eq 'test') { throw 'Gebruik voor de eindtest de aparte freeze-workflow in README.md.' }
                if (-not $RunName) { $RunName = "baseline-$Split-$InferenceSize" }
                & $runtimePython -m persoon1 predict --manifest $manifest --weights models/yolo11n.pt --mapping configs/mapping-pretrained-example.json --output "runs/$RunName" --split $Split --device $Device --imgsz $InferenceSize
            }
            'annotate' {
                $proposalDir = "runs/baseline-$Split-$InferenceSize/proposals"
                Write-Host "Open http://127.0.0.1:$Port in je browser. Stoppen: Ctrl+C."
                if (Test-Path -LiteralPath $proposalDir) {
                    & $runtimePython -m persoon1 annotate --manifest $manifest --proposals $proposalDir --split $Split --port $Port
                } else {
                    & $runtimePython -m persoon1 annotate --manifest $manifest --split $Split --port $Port
                }
            }
            'validate' { & $runtimePython -m persoon1 validate --manifest $manifest --output reports/dataset-validation-local.json --require-review }
            'train' {
                if (-not (Test-Path -LiteralPath 'configs/approvals.json')) { throw 'Leg eerst de echte gezamenlijke datasetgoedkeuring vast; zie README.md.' }
                if (-not $RunName) { $RunName = 'ft-' + (Get-Date -Format 'yyyyMMdd-HHmmss') }
                & $runtimePython -m persoon1 train --manifest $manifest --approvals configs/approvals.json --weights models/yolo11n.pt --output "runs/$RunName" --device $Device
            }
        }
    }
    if ($Mode -ne 'prepare' -and $LASTEXITCODE -ne 0) { throw 'De gekozen stap is niet geslaagd. Lees de melding hierboven.' }
} finally {
    Pop-Location
}
