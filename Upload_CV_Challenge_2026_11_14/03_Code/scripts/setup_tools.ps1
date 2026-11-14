param([string]$Destination = (Join-Path $PSScriptRoot '..\.tools'))
$ErrorActionPreference = 'Stop'
$destinationPath = [System.IO.Path]::GetFullPath($Destination)
New-Item -ItemType Directory -Path $destinationPath -Force | Out-Null
$archivePath = Join-Path $destinationPath 'ffmpeg-btbn.zip'
$downloadUrl = 'https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip'
# BtbN is a Windows build provider linked by ffmpeg.org/download.html.
& curl.exe --fail --location --retry 2 --output $archivePath $downloadUrl
if ($LASTEXITCODE -ne 0) { throw 'FFmpeg downloaden mislukt.' }
Expand-Archive -LiteralPath $archivePath -DestinationPath $destinationPath -Force
Get-ChildItem -LiteralPath $destinationPath -Filter 'ffmpeg.exe' -Recurse | ForEach-Object { & $_.FullName -version | Select-Object -First 1 }
Get-ChildItem -LiteralPath $destinationPath -Filter 'ffprobe.exe' -Recurse | ForEach-Object { & $_.FullName -version | Select-Object -First 1 }
