<#
.SYNOPSIS
Run independent Skills for Databricks Vally evaluations.
#>
#Requires -Version 7.0

[CmdletBinding()]
param(
    [string]$Skill,
    [string]$Suite = 'smoke',
    [int]$Runs = 1,
    [int]$Workers = 1,
    [int]$MaxRetries = 0,
    [string]$EvalDirs,
    [int]$ShardIndex = -1,
    [int]$ShardCount = 1,
    [switch]$Baseline,
    [switch]$DryRun,
    [string]$Model,
    [string]$ResultsDir
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$VallyVersion = '0.13.0'
$RepoRoot = Split-Path -Parent $PSScriptRoot
$EvalRoot = Join-Path $PSScriptRoot 'evals'
$StageRoot = Join-Path $PSScriptRoot '.vally-staging'
$PluginRoot = Join-Path $RepoRoot 'plugins/databricks-skills'
$EmptySkillRoot = Join-Path $StageRoot '_empty-skills'

$nodeVersionText = (& node --version 2>$null)
if (-not $nodeVersionText) { throw 'Node.js 22+ is required.' }
$nodeMajor = [int](($nodeVersionText -replace '^v', '').Split('.')[0])
if ($nodeMajor -lt 22) { throw "Node.js 22+ is required; found $nodeVersionText." }

$npmVersionText = (& npm --version 2>$null)
if (-not $npmVersionText) { throw 'npm 11.11.1+ is required.' }
$npmVersion = [version]$npmVersionText
if ($npmVersion -lt [version]'11.11.1') { throw "npm 11.11.1+ is required; found $npmVersionText." }

$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) { throw 'Python 3 with PyYAML is required.' }
& $python.Source -c 'import yaml' 2>$null
if ($LASTEXITCODE -ne 0) { throw 'PyYAML is required. Install tests/requirements-dev.txt.' }

& $python.Source (Join-Path $RepoRoot 'build/build_plugins.py') --check
if ($LASTEXITCODE -ne 0) { throw 'Plugin materialization failed.' }

if (Test-Path $StageRoot) { Remove-Item $StageRoot -Recurse -Force }
New-Item -ItemType Directory -Path $StageRoot | Out-Null
New-Item -ItemType Directory -Path $EmptySkillRoot | Out-Null

$selector = @'
import json, pathlib, sys, yaml
root = pathlib.Path(sys.argv[1])
skill = sys.argv[2]
suite = sys.argv[3]
eval_dirs = {x.strip() for x in sys.argv[4].split(',') if x.strip()}
index, count = int(sys.argv[5]), int(sys.argv[6])
suite_filters = yaml.safe_load((root.parents[1] / '.vally.yaml').read_text(encoding='utf-8'))['suites']
filter_map = suite_filters.get(suite, {}).get('filter', {}) if suite else {}
selected = []
for path in sorted(root.glob('*/eval.yaml')):
    if skill and path.parent.name != skill:
        continue
    if eval_dirs and path.parent.name not in eval_dirs:
        continue
    doc = yaml.safe_load(path.read_text(encoding='utf-8')) or {}
    tags = doc.get('tags', {}) or {}
    if filter_map:
        eval_matches = all(tags.get(key) == value for key, value in filter_map.items())
        stimulus_matches = any(
            all((stimulus.get('tags', {}) or {}).get(key) == value for key, value in filter_map.items())
            for stimulus in doc.get('stimuli', [])
        )
        if not eval_matches and not stimulus_matches:
            continue
    selected.append(path)
if count > 1:
    if index < 0 or index >= count:
        raise SystemExit('ShardIndex must be between 0 and ShardCount-1')
    selected = selected[index::count]
print(json.dumps([str(path) for path in selected]))
'@

$selectionJson = $selector | & $python.Source - $EvalRoot $Skill $Suite $EvalDirs $ShardIndex $ShardCount
if ($LASTEXITCODE -ne 0) { throw 'Eval selection failed.' }
$evalFiles = @($selectionJson | ConvertFrom-Json)
if ($evalFiles.Count -eq 0) { throw 'No eval specifications matched the requested scope.' }

$staged = @()
foreach ($sourceText in $evalFiles) {
    $source = [IO.Path]::GetFullPath([string]$sourceText)
    $destinationDir = Join-Path $StageRoot (Split-Path $source -Parent | Split-Path -Leaf)
    New-Item -ItemType Directory -Path $destinationDir -Force | Out-Null
    $destination = Join-Path $destinationDir 'eval.yaml'
    $content = Get-Content $source -Raw
    if ($content -match '\{\{[A-Z0-9_]+\}\}') {
        throw "Unresolved token in $source. Offline evals must not require cloud placeholders."
    }
    Set-Content -Path $destination -Value $content -Encoding utf8NoBOM
    $staged += $destination
}

Write-Host "Staged $($staged.Count) eval specification(s):"
$staged | ForEach-Object { Write-Host "  $_" }
if ($DryRun) { exit 0 }

$outputDir = if ($ResultsDir) { $ResultsDir } else { Join-Path $PSScriptRoot '.vally-results' }
New-Item -ItemType Directory -Path $outputDir -Force | Out-Null
$env:VALLY_TELEMETRY_OPTOUT = if ($env:VALLY_TELEMETRY_OPTOUT) { $env:VALLY_TELEMETRY_OPTOUT } else { '1' }

$vallyCommand = @('--yes', '--ignore-scripts', "@microsoft/vally-cli@$VallyVersion", 'eval', '--output-dir', $outputDir)
foreach ($evalFile in $staged) { $vallyCommand += @('--eval-spec', $evalFile) }
$vallyCommand += @('--runs', "$Runs", '--workers', "$Workers", '--max-retries', "$MaxRetries")
$vallyCommand += @('--skill-dir', $(if ($Baseline) { $EmptySkillRoot } else { $PluginRoot }))
if ($Model) { $vallyCommand += @('--model', $Model) }

Write-Host "Running Vally $VallyVersion with $($staged.Count) spec(s)."
& npx @vallyCommand
exit $LASTEXITCODE
