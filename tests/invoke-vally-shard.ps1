<#
.SYNOPSIS
Run one Vally shard and always emit a safe normalized result artifact.
#>
#Requires -Version 7.0

[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [ValidateSet('smoke', 'fulleval')]
    [string]$Suite,

    [Parameter(Mandatory)]
    [string]$EvalDirs,

    [Parameter(Mandatory)]
    [ValidateRange(0, 1000)]
    [int]$Shard,

    [Parameter(Mandatory)]
    [string]$OutputRoot,

    [switch]$Baseline,

    [string]$Model
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$mode = if ($Baseline) { 'baseline' } else { 'skill' }
$rawRoot = Join-Path $OutputRoot "$mode-raw"
$safeRoot = Join-Path $OutputRoot "$mode-redacted"
$normalizedPath = Join-Path $OutputRoot "$mode-shard-$Shard.json"
New-Item -ItemType Directory -Path $OutputRoot -Force | Out-Null

if ([string]::IsNullOrWhiteSpace($env:COPILOT_GITHUB_TOKEN)) {
    @{
        shard = $Shard
        error = 'Authentication failed because COPILOT_GITHUB_TOKEN is unavailable.'
        results = @()
    } | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $normalizedPath -Encoding utf8NoBOM
    Write-Warning 'COPILOT_GITHUB_TOKEN is unavailable; wrote a normalized authentication failure.'
    return
}

New-Item -ItemType Directory -Path $rawRoot -Force | Out-Null

$arguments = @(
    '-NoLogo',
    '-NoProfile',
    '-NonInteractive',
    '-File',
    (Join-Path $PSScriptRoot 'run-vally-eval.ps1'),
    '-Suite', $Suite,
    '-EvalDirs', $EvalDirs,
    '-Runs', '1',
    '-Workers', '1',
    '-MaxRetries', '1',
    '-ResultsDir', $rawRoot
)
if ($Baseline) {
    $arguments += '-Baseline'
}
if ($Model) {
    $arguments += @('-Model', $Model)
}

$previousNativePreference = $PSNativeCommandUseErrorActionPreference
$PSNativeCommandUseErrorActionPreference = $false
& pwsh @arguments
$vallyExitCode = $LASTEXITCODE
$PSNativeCommandUseErrorActionPreference = $previousNativePreference

$normalizationError = $null
try {
    python -m tests.vally_ci normalize `
        --results-root $rawRoot `
        --shard $Shard `
        --json-out $normalizedPath
} catch {
    $normalizationError = $_.Exception.Message
}

if ($normalizationError -or -not (Test-Path -LiteralPath $normalizedPath -PathType Leaf)) {
    @{
        shard = $Shard
        error = if ($vallyExitCode -ne 0) {
            "Vally process failed with exit code $vallyExitCode and produced no usable results."
        } else {
            'Vally produced no usable normalized results.'
        }
        results = @()
    } | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $normalizedPath -Encoding utf8NoBOM
}

python -m tests.vally_ci redact-tree --input $rawRoot --output $safeRoot | Out-Host
Write-Host "Normalized $mode shard result: $normalizedPath"
