param([string]$Device='auto', [int]$Port=8501, [string]$Python='', [switch]$CheckOnly)
& (Join-Path $PSScriptRoot 'Start-Voetbal.ps1') -Model yolo26 -Device $Device -Port $Port -Python $Python -CheckOnly:$CheckOnly
