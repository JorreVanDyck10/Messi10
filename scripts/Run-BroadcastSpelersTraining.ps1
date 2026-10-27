param(
    [string]$Dataset = 'data/broadcast-pitch-v1',
    [string]$Output = 'artifacts/broadcast-pitch-v1',
    [string]$Refined = 'artifacts/broadcast-refine-v2'
)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$python = Join-Path $projectRoot '.venv/Scripts/python.exe'
$env:PYTHONPATH = (Join-Path $projectRoot 'src') + [IO.Path]::PathSeparator + $projectRoot
$env:PYTHONUNBUFFERED = '1'
$env:OMP_NUM_THREADS = '4'
$env:MKL_NUM_THREADS = '4'
Push-Location $projectRoot
try {
    & $python -m football_pipeline.broadcast_data $Dataset
    if ($LASTEXITCODE -ne 0) { throw 'Broadcastdata niet volledig voorbereid; zie de bewaarde voortgang.' }
    # Keep ten minutes of margin below the authorized four-hour GPU ceiling.
    $budgetWatch = [Diagnostics.Stopwatch]::StartNew()
    function Remaining-Minutes([double]$stageCap) {
        $remaining = 230 - $budgetWatch.Elapsed.TotalMinutes
        if ($remaining -le 0) { throw 'Het totale trainingsbudget is verbruikt.' }
        return [Math]::Min($stageCap, $remaining)
    }
    & $python -m football_pipeline.broadcast_training detector --dataset $Dataset --output $Output --minutes (Remaining-Minutes 100)
    if ($LASTEXITCODE -ne 0) { throw 'Spelertraining niet voltooid; bewaar de checkpoints en logs.' }
    & $python -m football_pipeline.broadcast_training appearance --dataset $Dataset --output $Output --minutes (Remaining-Minutes 15)
    if ($LASTEXITCODE -ne 0) { throw 'Rol- of teamtraining niet voltooid; zie de bewaarde voortgang.' }
    foreach ($stage in @('roles', 'teams', 'detector')) {
        $cap = if ($stage -eq 'detector') { 90 } else { 15 }
        & $python -m football_pipeline.broadcast_refine $stage --dataset $Dataset --base-output $Output --output $Refined --minutes (Remaining-Minutes $cap)
        if ($LASTEXITCODE -ne 0) { throw "Verfijning $stage niet voltooid; checkpoints blijven bewaard." }
    }
    & $python -m football_pipeline.broadcast_release --dataset $Dataset --output $Output --refined $Refined
    if ($LASTEXITCODE -ne 0) { throw 'Vergelijking of demonstratie niet voltooid; het resultaat is niet goedgekeurd.' }
} finally { Pop-Location }
