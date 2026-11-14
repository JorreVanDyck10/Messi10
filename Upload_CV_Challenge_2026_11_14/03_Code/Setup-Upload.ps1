param([string]$Python = '', [switch]$SkipField)
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
if (-not $Python) {
    $Python = & py -3.11 -c "import sys; print(sys.executable)"
    if ($LASTEXITCODE -ne 0) { throw 'Installeer Python 3.11 of geef -Python met het volledige pad.' }
}
$version = & $Python -c "import sys; print(str(sys.version_info.major)+'.'+str(sys.version_info.minor))"
if ($LASTEXITCODE -ne 0 -or $version -ne '3.11') { throw 'Gebruik Python 3.11 voor app en veldruntime.' }
if (-not (Test-Path '.venv/Scripts/python.exe')) { & $Python -m venv .venv }
if ($LASTEXITCODE -ne 0) { throw 'Omgeving maken mislukt.' }
$appPython = Join-Path $PSScriptRoot '.venv/Scripts/python.exe'
& $appPython -m pip install torch==2.10.0 torchvision==0.25.0 --index-url https://download.pytorch.org/whl/cpu
if ($LASTEXITCODE -ne 0) { throw 'PyTorch installeren mislukt.' }
& $appPython -m pip install -r requirements-upload-app.txt
if ($LASTEXITCODE -ne 0) { throw 'Applicatiebibliotheken installeren mislukt.' }
& $appPython -m pip install --no-deps -e .
if ($LASTEXITCODE -ne 0) { throw 'Project registreren mislukt.' }
if (-not (Test-Path '.tools/ffmpeg-master-latest-win64-gpl/bin/ffprobe.exe')) { & ./scripts/setup_tools.ps1 }
if ($LASTEXITCODE -ne 0) { throw 'FFmpeg installeren mislukt.' }
if (-not $SkipField) {
    if (-not (Get-Command git -ErrorAction SilentlyContinue)) { throw 'Git is nodig voor de broncontrole van PnLCalib.' }
    if (-not (Test-Path '.tools/pnlcalib-env/Scripts/python.exe')) { & $Python -m venv .tools/pnlcalib-env }
    if ($LASTEXITCODE -ne 0) { throw 'Veldomgeving maken mislukt.' }
    $fieldPython = Join-Path $PSScriptRoot '.tools/pnlcalib-env/Scripts/python.exe'
    & $fieldPython -m pip install torch==2.3.1 torchvision==0.18.1 --index-url https://download.pytorch.org/whl/cpu
    if ($LASTEXITCODE -ne 0) { throw 'Veld-PyTorch installeren mislukt.' }
    & $fieldPython -m pip install -r requirements-upload-field.txt
    if ($LASTEXITCODE -ne 0) { throw 'Veldbibliotheken installeren mislukt.' }
    & $appPython upload_tools.py field --python $fieldPython
    if ($LASTEXITCODE -ne 0) { throw 'Veldruntime koppelen mislukt.' }
}
Write-Host 'Klaar. Start met ./Start-Upload.ps1 of ./Start-Upload.ps1 -Manual.'
