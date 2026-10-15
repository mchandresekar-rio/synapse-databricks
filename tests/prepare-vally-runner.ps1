<#
.SYNOPSIS
Validate the self-hosted runner toolchain and prepare an isolated Python environment.
#>
#Requires -Version 7.0

[CmdletBinding()]
param(
    [string]$Requirements = (Join-Path $PSScriptRoot 'requirements-dev.txt')
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) {
    throw 'Python 3.11 or later must be installed on the self-hosted runner.'
}

$pythonVersion = & $python.Source -c 'import sys; print(".".join(map(str, sys.version_info[:3])))'
if ([version]$pythonVersion -lt [version]'3.11.0') {
    throw "Python 3.11 or later is required; found $pythonVersion."
}

$nodeVersionText = & node --version
$nodeVersion = [version]($nodeVersionText -replace '^v', '')
if ($nodeVersion -lt [version]'22.0.0') {
    throw "Node.js 22 or later is required; found $nodeVersionText."
}

$npmVersionText = & npm --version
$npmVersion = [version]$npmVersionText
if ($npmVersion -lt [version]'11.11.1') {
    throw "npm 11.11.1 or later is required; found $npmVersionText."
}

if (-not (Test-Path -LiteralPath $Requirements -PathType Leaf)) {
    throw "Requirements file not found: $Requirements"
}

$runnerTemp = if ($env:RUNNER_TEMP) {
    $env:RUNNER_TEMP
} else {
    Join-Path ([IO.Path]::GetTempPath()) 'skills-for-caf-runner'
}
$venvRoot = Join-Path $runnerTemp 'caf-eval-venv'

if (Test-Path -LiteralPath $venvRoot) {
    Remove-Item -LiteralPath $venvRoot -Recurse -Force
}

& $python.Source -m venv $venvRoot
$venvPython = Join-Path $venvRoot 'Scripts\python.exe'
& $venvPython -m pip install --disable-pip-version-check -r $Requirements

if ($env:GITHUB_PATH) {
    Add-Content -LiteralPath $env:GITHUB_PATH -Value (Join-Path $venvRoot 'Scripts')
}

Write-Host "Runner ready: Python $pythonVersion, Node.js $nodeVersionText, npm $npmVersionText."
