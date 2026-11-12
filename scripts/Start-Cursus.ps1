param(
    [string]$Device = '0',
    [switch]$CheckOnly
)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$profilePath = Join-Path $projectRoot 'configs/models-players-base.json'
$profile = Get-Content -Raw -LiteralPath $profilePath | ConvertFrom-Json
if (@($profile.models).Count -ne 1 -or $profile.appearance) {
    throw 'Het cursusstartpad vereist precies een detector zonder extra rolclassifier.'
}
$profile.profile_name = 'Cursus: P004 speler/scheidsrechter, handmatige veldpunten'
foreach ($model in $profile.models) {
    $model.weights = [IO.Path]::GetFullPath((Join-Path (Split-Path $profilePath) $model.weights))
    if (-not (Test-Path -LiteralPath $model.weights)) { throw "Model ontbreekt: $($model.weights). Haal de Git LFS-bestanden op." }
    $hash = (Get-FileHash -LiteralPath $model.weights -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($hash -ne $model.weights_sha256) { throw 'Modelhash wijkt af. Controleer of de echte Git LFS-gewichten aanwezig zijn.' }
    $model.device = $Device
}
$profile.handoff.evaluation_record = [IO.Path]::GetFullPath((Join-Path (Split-Path $profilePath) $profile.handoff.evaluation_record))
$evaluationHash = (Get-FileHash -LiteralPath $profile.handoff.evaluation_record -Algorithm SHA256).Hash.ToLowerInvariant()
if ($evaluationHash -ne $profile.handoff.evaluation_sha256) { throw 'Het P004-evaluatiebestand wijkt af van het profiel.' }
if ($CheckOnly) {
    Write-Output "OK: een P004-detector, model- en evaluatiehash gecontroleerd; device=$Device."
    Write-Output 'Startkeuze: handmatige veldpunten. Geen extra rol-/teamclassifier of automatische veldruntime nodig.'
    Write-Output 'Dit controleert bestanden, geen GPU-inference of volledige demonstratie.'
    return
}
$runtimePython = Join-Path $projectRoot '.venv/Scripts/python.exe'
if (-not (Test-Path -LiteralPath $runtimePython)) { throw 'Voer eerst scripts/Setup-Persoon1.ps1 uit. Zie docs/Cursuscheck_En_Eenvoud.md.' }
$cachePath = Join-Path $projectRoot '.cache'
New-Item -ItemType Directory -Force -Path $cachePath | Out-Null
$localProfile = Join-Path $cachePath 'models-cursus-local.json'
$profile | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $localProfile -Encoding utf8
$oldModels = $env:FOOTBALL_MODELS
$oldMode = $env:FOOTBALL_CALIBRATION_MODE
Push-Location $projectRoot
try {
    $env:FOOTBALL_MODELS = $localProfile
    $env:FOOTBALL_CALIBRATION_MODE = 'manual'
    Write-Output 'Cursusstart: vaste camera, P004 en handmatige kalibratie. Laat tracking uit voor de basisdemo.'
    Write-Output 'Andere appkeuzes blijven beschikbaar; dit script stelt alleen het eenvoudige startprofiel in.'
    & $runtimePython -m streamlit run streamlit_app.py
    if ($LASTEXITCODE -ne 0) { throw 'Streamlit kon niet correct starten.' }
} finally {
    $env:FOOTBALL_MODELS = $oldModels
    $env:FOOTBALL_CALIBRATION_MODE = $oldMode
    Pop-Location
}
