param(
    [string]$Output = 'artifacts/course-improvement-20261019',
    [int]$PlayerEpochs = 60,
    [int]$FieldEpochs = 6,
    [int]$FieldHeadEpochs = 8,
    [int]$FieldConservativeEpochs = 6,
    [string]$FieldBaseline = '.tools/field-runtime.json',
    [switch]$AllowFieldErrorReduction
)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$dataset = Join-Path $projectRoot 'data\course-multimatch-v1'
$destination = [IO.Path]::GetFullPath((Join-Path $projectRoot $Output))
New-Item -ItemType Directory -Force -Path $destination | Out-Null
$env:PYTHONPATH = (Join-Path $projectRoot 'src') + [IO.Path]::PathSeparator + $projectRoot
$env:PYTHONUTF8 = '1'
$env:PYTHONIOENCODING = 'utf-8'
$env:PYTHONUNBUFFERED = '1'
$env:OMP_NUM_THREADS = '4'
$env:MKL_NUM_THREADS = '4'
$env:CUBLAS_WORKSPACE_CONFIG = ':4096:8'
$job = @{ pid=$PID; status='running'; started_at=[DateTime]::UtcNow.ToString('o'); automatic_promotion=$false }
function Invoke-TrainingPhase([string]$phase, [string]$python, [string[]]$arguments) {
    <#
    .SYNOPSIS
    Voert één cursusproeffase uit met de opgegeven Python-omgeving en argumenten.
    .DESCRIPTION
    Bewaart de fasenaam in job.json, wacht op het verborgen subprocess en schrijft
    stdout en stderr naar afzonderlijke logs. Een mislukte fase stopt de keten.
    #>
    $job.phase = $phase
    $job.updated_at = [DateTime]::UtcNow.ToString('o')
    $job | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $destination 'job.json') -Encoding utf8
    $child = Start-Process -FilePath $python -ArgumentList $arguments -WorkingDirectory $projectRoot -WindowStyle Hidden -Wait -PassThru -RedirectStandardOutput (Join-Path $destination "$phase.stdout.log") -RedirectStandardError (Join-Path $destination "$phase.stderr.log")
    if ($child.ExitCode -ne 0) { throw "$phase failed with exit code $($child.ExitCode). Read its saved logs." }
}
try {
    $appPython = Join-Path $projectRoot '.venv\Scripts\python.exe'
    $fieldPython = Join-Path $projectRoot '.tools\field-training-env\Scripts\python.exe'
    $quotedDataset = '"' + $dataset + '"'
    $baselineSnapshot = Join-Path $destination 'baseline-field-runtime.json'
    if (-not (Test-Path -LiteralPath $baselineSnapshot)) {
        Copy-Item -LiteralPath (Join-Path $projectRoot $FieldBaseline) -Destination $baselineSnapshot
    }
    $quotedBaseline = '"' + $baselineSnapshot + '"'
    Invoke-TrainingPhase 'prepare' $appPython @('-m', 'football_pipeline.course_dataset', $quotedDataset)
    Invoke-TrainingPhase 'players' $appPython @('-m', 'football_pipeline.course_experiments', '--dataset', $quotedDataset, '--output', ('"' + (Join-Path $destination 'players') + '"'), '--epochs', $PlayerEpochs)
    $quotedFieldData = '"' + (Join-Path $dataset 'field') + '"'
    Invoke-TrainingPhase 'field' $fieldPython @('-m', 'football_pipeline.field_learning', 'train', '--runtime', $quotedBaseline, '--dataset', $quotedFieldData, '--output', ('"' + (Join-Path $destination 'field') + '"'), '--epochs', $FieldEpochs, '--lr', '0.00003', '--patience', '4', '--weight-decay', '0.0001')
    Invoke-TrainingPhase 'field-head' $fieldPython @('-m', 'football_pipeline.field_learning', 'train', '--runtime', $quotedBaseline, '--dataset', $quotedFieldData, '--output', ('"' + (Join-Path $destination 'field-head') + '"'), '--epochs', $FieldHeadEpochs, '--lr', '0.0001', '--patience', '4', '--weight-decay', '0.0001', '--head-only')
    Invoke-TrainingPhase 'field-head-conservative' $fieldPython @('-m', 'football_pipeline.field_learning', 'train', '--runtime', $quotedBaseline, '--dataset', $quotedFieldData, '--output', ('"' + (Join-Path $destination 'field-head-conservative') + '"'), '--epochs', $FieldConservativeEpochs, '--lr', '0.00001', '--patience', '3', '--weight-decay', '0', '--head-only')
    foreach ($experiment in @('field', 'field-head', 'field-head-conservative')) {
        $training = Join-Path $destination $experiment
        $lastCandidate = Join-Path $destination "$experiment-last-candidate"
        Invoke-TrainingPhase "$experiment-extract-last" $fieldPython @('scripts/field_last_checkpoint_candidate.py', '--training', ('"' + $training + '"'), '--baseline', $quotedBaseline, '--output', ('"' + $lastCandidate + '"'))
        foreach ($candidate in @($training, $lastCandidate)) {
            $phase = (Split-Path -Leaf $candidate) + '-policy'
            $comparisonArguments = @('-m', 'football_pipeline.course_field_evaluation', '--dataset', $quotedFieldData, '--baseline', $quotedBaseline, '--candidate', ('"' + (Join-Path $candidate 'field-runtime.json') + '"'), '--output', ('"' + (Join-Path $destination $phase) + '"'))
            if ($AllowFieldErrorReduction) { $comparisonArguments += '--allow-error-reduction' }
            Invoke-TrainingPhase $phase $fieldPython $comparisonArguments
        }
    }
    $job.status = 'complete'
} catch {
    $job.status = 'failed'
    $job.error = $_.Exception.Message
    throw
} finally {
    $job.updated_at = [DateTime]::UtcNow.ToString('o')
    $job | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $destination 'job.json') -Encoding utf8
}
