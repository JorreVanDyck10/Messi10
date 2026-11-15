param([int]$Port=8501,[string]$Device='cpu',[switch]$Manual)
$ErrorActionPreference='Stop'
Set-Location -LiteralPath $PSScriptRoot
$python=Join-Path $PSScriptRoot '.venv/Scripts/python.exe'
if (-not (Test-Path -LiteralPath $python)) { throw 'Voer eerst Setup-Upload.ps1 uit.' }
$env:PYTHONPATH=(Join-Path $PSScriptRoot 'src')+[IO.Path]::PathSeparator+$PSScriptRoot
& $python upload_tools.py profile --device $Device
if ($LASTEXITCODE -ne 0) { throw 'Modelprofiel koppelen mislukt.' }
$env:FOOTBALL_MODELS=Join-Path $PSScriptRoot '.cache/models-upload.json'
$env:FOOTBALL_AUTO_MODELS=$env:FOOTBALL_MODELS
$env:FOOTBALL_FIELD_RUNTIME=Join-Path $PSScriptRoot '.tools/field-runtime.json'
$env:FOOTBALL_TEAMS=Join-Path $PSScriptRoot 'configs/teams-broadcast.json'
$env:FOOTBALL_RUNS=Join-Path $PSScriptRoot 'runs/upload'
$env:FOOTBALL_UPLOAD_MODE=if($Manual){'manual'}else{'automatic'}
$env:PYTHONIOENCODING='utf-8'
$env:OMP_NUM_THREADS='4'
$env:MKL_NUM_THREADS='4'
if (-not $Manual -and -not (Test-Path $env:FOOTBALL_FIELD_RUNTIME)) { throw 'Veldruntime ontbreekt: voer Setup-Upload.ps1 uit, of start met -Manual.' }
& $python -m streamlit run upload_app.py --server.address=127.0.0.1 --server.port=$Port
