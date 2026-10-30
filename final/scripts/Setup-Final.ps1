param([string]$Python = 'python', [switch]$Cuda)
$ErrorActionPreference = 'Stop'
& (Join-Path $PSScriptRoot 'Setup-Persoon1.ps1') -Python $Python -CpuOnly:(-not $Cuda)
& (Join-Path $PSScriptRoot 'setup_tools.ps1')
Write-Host 'Final is klaar. Start met scripts/Start-Final.ps1 (CPU), of voeg -Device 0 toe voor CUDA.'
