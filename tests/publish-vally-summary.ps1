<#
.SYNOPSIS
Create or update a marker-scoped Vally summary comment on a pull request.
#>
#Requires -Version 7.0

[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [string]$Repository,

    [Parameter(Mandatory)]
    [int]$PullRequest,

    [Parameter(Mandatory)]
    [ValidatePattern('^[a-z0-9-]+$')]
    [string]$ReportKey,

    [Parameter(Mandatory)]
    [string]$MarkdownPath
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

if (-not (Test-Path -LiteralPath $MarkdownPath -PathType Leaf)) {
    throw "Summary file not found: $MarkdownPath"
}

$marker = "<!-- skills-for-caf-vally:$ReportKey -->"
$body = "$marker`n$(Get-Content -LiteralPath $MarkdownPath -Raw)"
$commentsJson = & gh api "repos/$Repository/issues/$PullRequest/comments" --paginate
if ($LASTEXITCODE -ne 0) {
    throw 'Unable to list pull request comments.'
}

$comments = @($commentsJson | ConvertFrom-Json)
$existing = $comments |
    Where-Object { $_.body -like "*$marker*" } |
    Sort-Object -Property id -Descending |
    Select-Object -First 1

if ($existing) {
    & gh api --method PATCH "repos/$Repository/issues/comments/$($existing.id)" -f "body=$body" | Out-Null
} else {
    & gh api --method POST "repos/$Repository/issues/$PullRequest/comments" -f "body=$body" | Out-Null
}
if ($LASTEXITCODE -ne 0) {
    throw 'Unable to publish the pull request summary.'
}
