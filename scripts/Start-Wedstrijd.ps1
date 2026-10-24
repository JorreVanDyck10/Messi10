param(
    [string]$Device = '0',
    [string]$FieldRuntime = ''
)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
if ($FieldRuntime) {
    $env:FOOTBALL_FIELD_RUNTIME = [IO.Path]::GetFullPath($FieldRuntime)
} elseif (-not $env:FOOTBALL_FIELD_RUNTIME) {
    $env:FOOTBALL_FIELD_RUNTIME = Join-Path $projectRoot '.tools\field-runtime.json'
}
if (-not (Test-Path -LiteralPath $env:FOOTBALL_FIELD_RUNTIME)) {
    throw 'De aparte veldomgeving ontbreekt. Voer met Python 3.11 eerst scripts\setup_field_model.py uit. Gebruik voor een CPU-veldmodel --device cpu. Zie docs\Gezamenlijke_Integratie.md.'
}
# Preserve the configured field environment; its GPU/CPU setting is independent.
& (Join-Path $PSScriptRoot 'Start-Spelermodel.ps1') -Recognition players -FieldMode automatic -Device $Device
